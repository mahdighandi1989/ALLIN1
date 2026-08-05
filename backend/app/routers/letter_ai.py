"""AI letter-assistant API — wired at /api/letter-ai.

Powers the «دستیار هوشمند» tool on the Letter page. Two endpoints:

* ``GET  /models``  — the enabled+configured AI models, best (priority) first, so
  the user can pick which one runs (or let it auto-pick the top one).
* ``POST /analyze`` — gather the letter's account facts from the DB, ask the
  chosen model for a list of *proposed* edits, then return only the changes that
  survive deterministic validation (see :mod:`app.services.letter_assistant`).

This router is **read-only** on the database: it never writes the letter or any
record. Applying the ticked changes happens client-side, and the letter is saved
through the normal ``/api/letters`` flow (``require_editor``). Running the model
is gated to editors (it is an editing tool and costs tokens) and audited.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import ai_manager, inference
from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.guarantor import Guarantor
from app.routers.auth import require_editor, get_current_active_user
from app.services import letter_assistant as la
from app.services import letter_db_extract as db_extract
from app.services.audit import record_audit

router = APIRouter(tags=["letter-ai"])


@router.get("/models")
async def list_models(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    """Usable models (enabled + provider configured), best-first, for the picker.
    Also exposes the catalog of tools so the UI and backend never drift."""
    models = await ai_manager.list_usable(db)
    tools = [{"id": k, "label": v["label"]} for k, v in la.TOOLS.items()]
    return {"ok": True, "models": models, "tools": tools, "available": bool(models)}


class AnalyzeRequest(BaseModel):
    account_no: Optional[str] = Field(default=None, max_length=50)
    fields: Dict[str, Any] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    instruction: str = ""
    selection: str = ""                                    # back-compat (single)
    selections: List[str] = Field(default_factory=list)    # the gathered snippets
    tables: List[str] = Field(default_factory=list)        # user-selected tables' HTML
    # v61 (full_check): attachment CONTENT the letter must agree with —
    # in-flow attachment tables' HTML + per-file transcribed/extracted text.
    attachment_tables: List[str] = Field(default_factory=list)
    attachments_text: List[Dict[str, str]] = Field(default_factory=list)  # [{name, text}]
    model_id: Optional[int] = None


async def _gather_facts(db: AsyncSession, account_no: str) -> Dict[str, Any]:
    """Authoritative DB snapshot for the account (customer + facilities +
    guarantors + a profile slice). Empty dict when the account is unknown."""
    acc = (account_no or "").strip()
    if not acc:
        return {}
    customer = (
        await db.execute(
            select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False)  # noqa: E712
        )
    ).scalar_one_or_none()
    if customer is None:
        return {}
    facilities = (
        await db.execute(
            select(Facility).where(Facility.customer_id == customer.id, Facility.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    guarantors = (
        await db.execute(
            select(Guarantor).where(Guarantor.account_no == acc, Guarantor.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    # Mortgaged properties (+ their dated event history), fixed deposits and
    # partners — so letters, the full_check pass and the attachment generator
    # can answer property/valuation/mortgage questions from the DB.
    from app.models.profile_entities import MortgagedProperty, PropertyEvent, FixedDeposit, Partner
    properties = (
        await db.execute(
            select(MortgagedProperty).where(MortgagedProperty.account_no == acc,
                                            MortgagedProperty.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    property_events = []
    if properties:
        property_events = (
            await db.execute(
                select(PropertyEvent).where(PropertyEvent.account_no == acc,
                                            PropertyEvent.is_deleted == False)  # noqa: E712
                .order_by(PropertyEvent.event_date)
            )
        ).scalars().all()
    fixed_deposits = (
        await db.execute(
            select(FixedDeposit).where(FixedDeposit.account_no == acc,
                                       FixedDeposit.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    partners = (
        await db.execute(
            select(Partner).where(Partner.account_no == acc, Partner.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    # The account's activity logs (audit trail + journal/daily-log lines) —
    # newest first, capped — so «از لاگ‌ها استخراج کن» requests work everywhere
    # the AI reads the DB. Best-effort: a missing table must not kill analyze.
    audit_rows: list = []
    journal_rows: list = []
    try:
        from app.models.audit_log import AuditLog
        audit_rows = (
            await db.execute(
                select(AuditLog).where(AuditLog.account_no == acc)
                .order_by(AuditLog.created_at.desc()).limit(40)
            )
        ).scalars().all()
    except Exception:
        audit_rows = []
    try:
        from app.models.crm import JournalEntry
        journal_rows = (
            await db.execute(
                select(JournalEntry).where(JournalEntry.account_no == acc)
                .order_by(JournalEntry.created_at.desc()).limit(40)
            )
        ).scalars().all()
    except Exception:
        journal_rows = []
    # Profile blob (extracted facts / offer-letter snapshot live here).
    profile_data: Dict[str, Any] = {}
    try:
        from app.models.crm import CustomerProfile
        import json as _json

        prof = (
            await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
        ).scalar_one_or_none()
        if prof is not None and getattr(prof, "data_json", None):
            loaded = _json.loads(prof.data_json)
            if isinstance(loaded, dict):
                profile_data = loaded
    except Exception:
        profile_data = {}
    return la.build_facts(customer, profile_data, list(facilities), list(guarantors),
                          properties=list(properties), property_events=list(property_events),
                          fixed_deposits=list(fixed_deposits), partners=list(partners),
                          audit_logs=list(audit_rows), journal_entries=list(journal_rows))


async def _style_samples(db: AsyncSession, current_body_html: str, limit: int = 3) -> list:
    """v88 — few-shot tone exemplars from the office's OWN saved letters, so
    rewrite suggestions read like this office's real correspondence instead of
    generic (childish) prose. Recent letters with a substantial body win; the
    letter currently being edited is skipped by body-prefix signature. Only
    subject+body text are sent, capped, and rule 16 forbids lifting facts."""
    import json as _json
    import re as _re

    from app.models.letter import Letter

    def _strip(h: str) -> str:
        return _re.sub(r"\s+", " ", _re.sub(r"<[^>]+>", " ", h or "")).strip()

    cur_sig = _strip(current_body_html)[:200]
    rows = (await db.execute(
        select(Letter).where(Letter.is_deleted == False)  # noqa: E712
        .order_by(Letter.created_at.desc()).limit(24)
    )).scalars().all()
    out: list = []
    for l in rows:
        try:
            vals = _json.loads(l.values_json or "{}")
        except Exception:
            continue
        body = _strip(str(vals.get("body") or ""))
        if len(body) < 220:                      # too short to model tone
            continue
        if cur_sig and body[:200] == cur_sig:    # the letter being edited
            continue
        out.append({"subject": _strip(str(vals.get("subject") or ""))[:120],
                    "body": body[:1500]})
        if len(out) >= limit:
            break
    return out


@router.post("/analyze")
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Run the chosen (or auto) model over the letter and return validated,
    reviewable change proposals. Never mutates anything."""
    tools = [t for t in (payload.tools or []) if t in la.TOOLS] or list(la.TOOLS.keys())
    facts = await _gather_facts(db, payload.account_no or "")
    # v88 — the office's own archive as the tone model for rewrites (rule 16)
    style = await _style_samples(db, str((payload.fields or {}).get("body") or ""))

    system = la.SYSTEM_PROMPT
    prompt = la.build_user_prompt(
        payload.fields or {}, facts, tools, style_samples=style,
        instruction=payload.instruction or "", selection=payload.selection or "",
        selections=payload.selections or [],
        tables=(payload.tables or []) if "tables" in tools else [],
        # attachment content feeds the full consistency/conformity pass AND the
        # KB harvest (db_extract may lift general/educational material out of
        # the attachments too); harmless to other tools (its section explains
        # it is not replaceable).
        attachments_text=(payload.attachments_text or []) if ({"full_check", "db_extract"} & set(tools)) else [],
        attachment_tables=(payload.attachment_tables or []) if ({"full_check", "db_extract"} & set(tools)) else [],
    )

    # v93 — the analyze prompt can be very large (attachment PDFs' text, all
    # tools, tables, archive tone samples): the 60s default inference deadline
    # expired for the owner exactly like the generator path (v89). Long deadline
    # + one transient retry; the UI already waits 300s.
    async def _an_complete(p_):
        import asyncio as _aio
        res = await inference.complete(
            db, p_, task="report_drafting", system=system,
            model_id=payload.model_id, max_tokens=8000, timeout=240.0,
            # No explicit temperature: newer reasoning models (Opus 4.8) reject it
            # with a 400. inference.complete also strips+retries as a backstop for
            # any model that carries a configured temperature.
        )
        err0 = str(res.get("error") or "")
        if not res.get("ok") and ("timed out" in err0 or "connection failed" in err0 or "429" in err0):
            await _aio.sleep(3)
            res = await inference.complete(
                db, p_, task="report_drafting", system=system,
                model_id=payload.model_id, max_tokens=8000, timeout=240.0,
            )
        return res

    result = await _an_complete(prompt)
    if not result.get("ok"):
        # Friendly, non-fatal: the UI shows the reason (e.g. no model configured).
        return {
            "ok": False,
            "error": result.get("error") or "ai_failed",
            "model": result.get("model"),
            "changes": [],
            "facts_used": bool(facts),
        }

    # need_logs (rule 15): the recent slice in facts is only ambient context —
    # when the instruction needs MORE logs (older, other accounts, system-wide,
    # a user/date filter), the model asks once and the server searches the
    # WHOLE log tables (no newest-N pre-limit), then re-runs with the results.
    need_logs = la.parse_need_logs(result.get("text") or "")
    if need_logs is not None:
        from app.services import log_search
        import json as _json

        found = await log_search.search_logs(db, need_logs)
        prompt2 = (
            prompt
            + "\n\n### نتایجِ جستجوی لاگ‌ها (پاسخِ need_logs تو — جستجو روی کلِ لاگ‌ها اجرا شد؛ "
              "دیگر need_logs مجاز نیست، همین حالا خروجیِ نهایی را بده):\n"
            + _json.dumps(found, ensure_ascii=False, separators=(",", ":"))
        )
        result = await _an_complete(prompt2)
        if not result.get("ok"):
            return {
                "ok": False,
                "error": result.get("error") or "ai_failed",
                "model": result.get("model"),
                "changes": [],
                "facts_used": bool(facts),
            }

    changes = la.parse_and_validate(
        result.get("text") or "", payload.fields or {},
        tables_count=(len(payload.tables or []) if "tables" in tools else 0),
    )

    # When the extract-to-DB tool is on — or inline in-text prompts may ask to
    # RECORD data («... این موارد ثبت بشه») — stage the model's db_write
    # proposals against the live database (resolve target customer +
    # add/update/skip). Reviewed like any other change; applying hits /apply-db.
    if "db_extract" in tools or "inline_prompts" in tools:
        raw_writes = la.parse_db_writes(result.get("text") or "")
        if raw_writes:
            primary_name = ""
            if isinstance(facts.get("customer"), dict):
                primary_name = facts["customer"].get("name") or ""
            staged = await db_extract.stage_db_writes(
                db, (payload.account_no or "").strip(), primary_name, raw_writes,
            )
            changes.extend(staged)

    # Knowledge-Base proposals (general/educational content) — staged like any
    # other change; the user ticks them and /apply-db persists via kb_store.
    if "db_extract" in tools:
        for i, kb in enumerate(la.parse_kb_writes(result.get("text") or ""), 1):
            changes.append({
                "id": f"kb-{i}", "op": "kb_write", "category": "db_extract",
                "field": "", "severity": "low", "applicable": True,
                "title": kb["title"], "detail": kb["detail"] or kb["source_note"],
                "topic": kb["topic"], "kb_category": kb["category"],
                "content": kb["content"], "source_note": kb["source_note"],
            })

    await record_audit(
        action="analyze", entity_type="letter_ai", entity_id=None,
        account_no=(payload.account_no or None),
        detail=f"دستیار هوشمندِ نامه — {len(changes)} پیشنهاد ({', '.join(tools)})",
        user=user, request=request, db=db,
    )
    return {
        "ok": True,
        "model": result.get("model"),
        "changes": changes,
        "count": len(changes),
        "facts_used": bool(facts),
        "tools": tools,
    }


class DbWriteItem(BaseModel):
    account_no: str
    customer_name: str = ""
    key: str
    value: str


class LinkItem(BaseModel):
    account_no: str
    related_account: str
    kind: str = "other"
    reason: str


class KbWriteItem(BaseModel):
    topic: str
    content: str
    category: str = ""
    source_note: str = ""
    account_no: str = ""


class ApplyDbRequest(BaseModel):
    items: List[DbWriteItem] = Field(default_factory=list)
    links: List[LinkItem] = Field(default_factory=list)
    kb_items: List[KbWriteItem] = Field(default_factory=list)
    source_ref: str = ""


@router.post("/apply-db")
async def apply_db(
    payload: ApplyDbRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Persist the user-approved extracted facts into the right customer
    profile(s) — dedup + staleness guarded, creating profiles as needed, auditing
    every write to the account (global log + that profile's «Logs» tab). Also
    creates approved profile↔profile links (kind + exact reason, both profiles)."""
    items = [i.model_dump() for i in (payload.items or [])
             if (i.account_no or "").strip() and (i.key or "").strip()]
    result: Dict[str, Any] = {"ok": True, "outcomes": [],
                              "counts": {"added": 0, "updated": 0, "skipped": 0, "profiles_created": 0}}
    if items:
        result = await db_extract.apply_db_writes(db, user, request, items)

    links_created = 0
    if payload.links:
        from app.services.relationships import ensure_link
        from app.services.customer_link import ensure_customer

        username = getattr(user, "username", "") or ""
        made = []
        for l in payload.links:
            if not (l.account_no or "").strip() or not (l.related_account or "").strip():
                continue
            # both sides must exist as profiles (stub-created if brand new)
            await ensure_customer(db, l.account_no.strip(), None)
            await ensure_customer(db, l.related_account.strip(), None)
            link = await ensure_link(
                db, l.account_no, l.related_account, kind=l.kind, reason=l.reason,
                source="letter_attachment_ai", source_ref=payload.source_ref or "",
                created_by=username,
            )
            if link is not None:
                made.append((l.account_no.strip(), l.related_account.strip(), l.kind, l.reason))
        await db.commit()
        links_created = len(made)
        for a, b, kind, reason in made:
            for acc in (a, b):  # audit on BOTH profiles' logs
                await record_audit(
                    action="update", entity_type="customer_link", entity_id=kind,
                    account_no=acc, detail=f"لینکِ پروفایلی «{kind}» با {b if acc == a else a} — علت: {reason}",
                    user=user, request=request, db=db,
                )
    result["links_created"] = links_created

    # Knowledge-Base items — grouped under topics with provenance (kb_store owns
    # grouping/dedup; the index/categories derive live, nothing else to update).
    kb_added = kb_skipped = 0
    if payload.kb_items:
        from app.services import kb_store
        username = getattr(user, "username", "") or ""
        for k in payload.kb_items:
            src = (k.source_note or "").strip()
            if payload.source_ref:
                src = f"{src} — {payload.source_ref}".strip(" —")
            r = await kb_store.upsert_entry(
                db, topic_title=k.topic, content=k.content, category=k.category,
                source_kind="letter_ai", source_ref=src,
                account_no=k.account_no or "", username=username,
            )
            if r.get("ok") and r.get("created_entry"):
                kb_added += 1
            else:
                kb_skipped += 1
        await db.commit()
        if kb_added:
            await record_audit(
                action="create", entity_type="knowledge", entity_id=None,
                account_no=None,
                detail=f"پایگاه دانش: {kb_added} مطلبِ تأییدشده از دستیارِ نامه ثبت شد"
                       + (f" ({payload.source_ref})" if payload.source_ref else ""),
                user=user, request=request, db=db,
            )
    result["kb_added"] = kb_added
    result["kb_skipped"] = kb_skipped
    return result


class ExtractAttachmentRequest(BaseModel):
    account_no: str = ""
    customer_name: str = ""
    subject: str = ""
    body_excerpt: str = ""
    model_id: Optional[int] = None
    # AI-generated attachments (their data came OUT of the database) are refused
    # by default to prevent circular re-ingestion; the UI sets this only when the
    # user explicitly ticked such an attachment.
    allow_ai_generated: bool = False


@router.post("/extract-attachment/{attachment_id}")
async def extract_attachment_endpoint(
    attachment_id: str,
    payload: ExtractAttachmentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Deep-extract ONE letter attachment (the UI runs attachments sequentially so
    each request stays bounded). Returns staged, reviewable changes — writes
    nothing. Pipeline + guards mirror the Import page (chunking/backoff/caps)."""
    from app.models.crm import Attachment
    from app.services import attachments as attachments_store
    from app.services import letter_attachment_extract as lax

    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Server-side circular-write guard (the frontend default-unticks these, but
    # the server is ground truth): an AI-generated attachment's content already
    # came out of the database — re-extracting it would re-ingest our own output.
    from app.services.letter_attachment_generate import AI_GENERATED_MARK
    if (a.notes or "").startswith(AI_GENERATED_MARK) and not payload.allow_ai_generated:
        return {"ok": False, "error": "ai_generated_attachment", "changes": []}

    # load the bytes from where they live (Drive or disk) — same as the download route
    data: bytes = b""
    if a.drive_file_id:
        from app.services import drive_sync
        try:
            data = await drive_sync.download_attachment(a.drive_file_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"دانلود از Drive ناموفق: {exc}")
    else:
        path = attachments_store.resolve(a.file_path or "")
        if path is None:
            raise HTTPException(status_code=404, detail="فایل روی دیسک یافت نشد")
        data = path.read_bytes()

    import mimetypes
    fname = a.original_name or a.file_name or "file"
    mime = mimetypes.guess_type(fname)[0] or ""
    if not mime:
        # No/unknown extension → sniff the magic bytes (the Import-page lesson:
        # never trust the name alone to decide how to read a file).
        head = data[:12]
        if head.startswith(b"%PDF-"):
            mime = "application/pdf"
        elif head.startswith(b"\x89PNG"):
            mime = "image/png"
        elif head.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif head.startswith(b"II*\x00") or head.startswith(b"MM\x00*"):
            mime = "image/tiff"
        elif head.startswith(b"PK\x03\x04") and fname.lower().endswith((".docx", ".xlsx", ".xlsm")):
            mime = "application/zip"
        else:
            mime = "application/octet-stream"

    # General letters store their attachments under the 'general' key — that is a
    # bucket, NOT a customer; never let it become the primary account (facts
    # would be attributed to a bogus «general» profile). With no primary, only
    # facts whose account is explicitly cited (or name-matched) get staged.
    att_acc = (a.account_no or "").strip()
    primary_acc = (payload.account_no or "").strip() or ("" if att_acc.lower() == "general" else att_acc)
    letter_ctx = {
        "subject": payload.subject or "", "account_no": primary_acc,
        "customer_name": payload.customer_name or "", "body_excerpt": payload.body_excerpt or "",
    }
    extraction = await lax.extract_attachment(
        db, data=data, filename=fname, mimetype=mime,
        letter_ctx=letter_ctx, model_id=payload.model_id,
    )
    if not extraction.get("ok"):
        return {"ok": False, "error": extraction.get("error"),
                "suggestions": extraction.get("suggestions", []), "changes": []}

    staged = await lax.stage_extraction(
        db, extraction, primary_account=primary_acc,
        primary_name=payload.customer_name or "", source_ref=fname,
    )
    # unique ids per attachment so items from several attachments never collide
    for it in staged:
        it["id"] = f"{attachment_id[-6:]}-{it['id']}"
        it["source_file"] = fname
    await record_audit(
        action="analyze", entity_type="letter_attachment_ai", entity_id=attachment_id,
        account_no=(primary_acc or None),
        detail=f"استخراج هوشمند از پیوست «{fname}» — {len(staged)} مورد",
        user=user, request=request, db=db,
    )
    return {"ok": True, "changes": staged, "model": extraction.get("model"),
            "chunk_errors": extraction.get("chunk_errors", []), "file": fname}


class AttachmentTextRequest(BaseModel):
    model_id: Optional[int] = None


@router.post("/attachment-text/{attachment_id}")
async def attachment_text_endpoint(
    attachment_id: str,
    payload: AttachmentTextRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Readable TEXT of one attachment for the full_check pass — deterministic
    for Excel/CSV/Word/plain text, one bounded transcription call for PDF/image.
    Writes NOTHING (unlike extract-attachment, which stages DB facts)."""
    from app.models.crm import Attachment
    from app.services import attachments as attachments_store
    from app.services import letter_attachment_extract as lax

    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    data: bytes = b""
    if a.drive_file_id:
        from app.services import drive_sync
        try:
            data = await drive_sync.download_attachment(a.drive_file_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"دانلود از Drive ناموفق: {exc}")
    else:
        path = attachments_store.resolve(a.file_path or "")
        if path is None:
            raise HTTPException(status_code=404, detail="فایل روی دیسک یافت نشد")
        data = path.read_bytes()

    import mimetypes
    fname = a.original_name or a.file_name or "file"
    mime = mimetypes.guess_type(fname)[0] or ""
    if not mime:
        head = data[:12]
        if head.startswith(b"%PDF-"):
            mime = "application/pdf"
        elif head.startswith(b"\x89PNG"):
            mime = "image/png"
        elif head.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        else:
            mime = "application/octet-stream"

    r = await lax.attachment_text(db, data=data, filename=fname, mimetype=mime,
                                  model_id=payload.model_id)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "file": fname}
    return {"ok": True, "file": fname, "text": r.get("text") or "", "model": r.get("model")}


@router.post("/template-text")
async def template_text_endpoint(
    file: UploadFile = File(...),
    model_id: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Readable TEXT of a TEMPLATE/SAMPLE file the user picked from their machine
    (a blank table another department sent, in any format) — for the attachment
    GENERATOR. Nothing is stored; deterministic for Excel/CSV/Word/plain text,
    one bounded transcription call for PDF/image."""
    from app.services import letter_attachment_extract as lax

    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="فایلِ قالب خالی است")
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="فایلِ قالب بزرگ‌تر از ۱۵MB است")

    import mimetypes
    fname = file.filename or "template"
    mime = mimetypes.guess_type(fname)[0] or (file.content_type or "")
    if not mime or mime == "application/octet-stream":
        head = data[:12]
        if head.startswith(b"%PDF-"):
            mime = "application/pdf"
        elif head.startswith(b"\x89PNG"):
            mime = "image/png"
        elif head.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"

    mid = None
    try:
        mid = int(model_id) if model_id not in (None, "", "null") else None
    except ValueError:
        mid = None
    r = await lax.attachment_text(db, data=data, filename=fname, mimetype=mime, model_id=mid)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "file": fname}
    return {"ok": True, "file": fname, "text": r.get("text") or "", "model": r.get("model")}


class GenerateAttachmentRequest(BaseModel):
    letter_id: str
    account_no: Optional[str] = None
    # instruction may be empty when a TEMPLATE is supplied (the format itself
    # says what to build); the endpoint enforces instruction-OR-template.
    instruction: str = Field(default="", max_length=3000)
    kind: Optional[str] = None                 # "excel" | "word" | None = model decides
    subject: Optional[str] = None
    recipient: Optional[str] = None
    body_excerpt: Optional[str] = None
    model_id: Optional[int] = None
    # v63: a sample/template file's TEXT (extracted via /template-text) — the
    # output must reproduce this exact format, filled from DB facts.
    template_text: str = Field(default="", max_length=20000)
    template_name: str = Field(default="", max_length=200)
    # v65: SOURCE/DATA files' TEXT ([{name, text}], extracted via /template-text)
    # — an allowed data source alongside the DB facts; any format, any count
    # (server caps at 8 files x 20k chars in the prompt).
    source_files: List[Dict[str, str]] = Field(default_factory=list)


@router.post("/generate-attachment")
async def generate_attachment(
    payload: GenerateAttachmentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Build a REAL file attachment (Excel/Word) for the letter from the owner's
    instruction. The model only proposes a strict JSON spec; the file is rendered
    server-side and stored through the SAME Drive+disk+DB path as manual uploads,
    marked AI_GENERATED (default-excluded from the extraction tool — its data
    came out of the database in the first place)."""
    from app.services import letter_attachment_generate as gen

    acct = (payload.account_no or "").strip()
    facts = await _gather_facts(db, acct)

    instruction = payload.instruction.strip()
    tpl_text = (payload.template_text or "").strip()
    if not instruction and not tpl_text:
        raise HTTPException(status_code=422,
                            detail="شرحِ درخواست یا فایلِ قالب/نمونه لازم است (حداقل یکی).")
    if payload.kind in ("excel", "word") and instruction:
        instruction += f"\n(فرمتِ خواسته‌شده توسط کاربر: {payload.kind})"
    letter_ctx = {
        "subject": payload.subject or "",
        "recipient": payload.recipient or "",
        "body_excerpt": payload.body_excerpt or "",
    }
    # The catalog lets the model REQUEST cross-customer data (branch-wide /
    # bank-wide lists) via need_data instead of returning an empty skeleton —
    # single-account facts alone cannot answer e.g. «همهٔ املاک شعبهٔ X».
    branches = await gen.list_branches(db)
    prompt = gen.build_prompt(facts, letter_ctx, instruction, catalog=gen.catalog_text(branches),
                              template_text=tpl_text, template_name=payload.template_name or "",
                              source_files=payload.source_files or [])
    # v89 — the source-files prompt can reach ~160k chars (8×20k caps): the
    # 60s default inference deadline regularly expired with several files
    # attached (owner: «دوبار امتحان کردم نشد … قبلا میشد»). Long deadline +
    # ONE retry on a transient failure, the same treatment the import path got
    # in v46. The UI already waits 420s for this call.
    async def _gen_complete(p_, max_tokens_):
        import asyncio as _aio
        res = await inference.complete(
            db, p_, task="report_drafting", system=gen.SYSTEM_PROMPT,
            model_id=payload.model_id, max_tokens=max_tokens_, timeout=240.0,
        )
        err0 = str(res.get("error") or "")
        if not res.get("ok") and ("timed out" in err0 or "connection failed" in err0 or "429" in err0):
            await _aio.sleep(3)
            res = await inference.complete(
                db, p_, task="report_drafting", system=gen.SYSTEM_PROMPT,
                model_id=payload.model_id, max_tokens=max_tokens_, timeout=240.0,
            )
        return res

    result = await _gen_complete(prompt, 8000)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or "ai_failed", "model": result.get("model")}

    fetch_warnings: list = []
    need = gen.parse_need_data(result.get("text") or "")
    if need:
        fetched, fetch_warnings = await gen.fetch_datasets(db, need["datasets"], need.get("branch") or "",
                                                           logs_filter=need.get("logs_filter"))
        prompt2 = gen.build_prompt(facts, letter_ctx, instruction, fetched=fetched,
                                   template_text=tpl_text, template_name=payload.template_name or "",
                                   source_files=payload.source_files or [])
        # bigger output budget: the spec now carries the fetched rows verbatim
        result = await _gen_complete(prompt2, 16000)
        if not result.get("ok"):
            return {"ok": False, "error": result.get("error") or "ai_failed", "model": result.get("model")}
        if gen.parse_need_data(result.get("text") or ""):
            return {"ok": False, "error": "bad_spec:need_data_twice", "model": result.get("model")}

    try:
        spec, warnings = gen.parse_spec(result.get("text") or "")
        warnings = warnings + [w for w in fetch_warnings if w not in warnings]
        if payload.kind in ("excel", "word"):
            spec["kind"] = payload.kind
            if payload.kind == "excel" and "sheets" not in spec:
                raise ValueError("no_sheets")
            if payload.kind == "word" and "paragraphs" not in spec:
                raise ValueError("no_paragraphs")
        data, filename, mimetype = gen.render(spec)
        # v84 — owner rule: the file's name = content description + account number
        filename = gen.finalize_filename(filename, acct)
    except ValueError as exc:
        return {"ok": False, "error": f"bad_spec:{exc}", "model": result.get("model")}

    # ---- store EXACTLY like a manual upload (Drive first, disk fallback) ----
    import uuid as _uuid
    from datetime import date as _date, datetime as _dt

    from app.models.crm import Attachment
    from app.services import attachments as attachments_store
    from app.services import drive_sync

    store_acct = acct or "general"
    facility_id = f"LTR-{payload.letter_id}"
    drive_file_id = ""
    stored = ""
    rel = ""
    size = len(data)
    if drive_sync.is_enabled():
        try:
            res = await drive_sync.sync_attachment(
                account_no=store_acct, facility_id=facility_id,
                original_name=filename, data=data, mimetype=mimetype,
            )
            if res.get("ok"):
                drive_file_id = res["result"]["id"]
                stored = res["result"]["name"]
        except Exception:  # noqa: BLE001 - Drive errors fall back to disk
            drive_file_id = ""
    if not drive_file_id:
        rel, size, stored = await attachments_store.save_bytes(store_acct, facility_id, filename, data)

    aid = f"A-{store_acct}-{_dt.now().strftime('%Y%m%d%H%M%S')}-{_uuid.uuid4().hex[:3]}"
    att = Attachment(
        id=aid, account_no=store_acct, facility_id=facility_id[:60],
        row_index="", file_name=stored[:255], original_name=filename[:255],
        file_path=rel, drive_file_id=drive_file_id or None,
        file_size=str(size), upload_date=_date.today().isoformat(),
        uploaded_by=getattr(user, "username", "") or "",
        is_shared="0",
        notes=f"{gen.AI_GENERATED_MARK}: {(instruction or ('طبق قالبِ ' + (payload.template_name or 'داده‌شده')))[:400]}",
    )
    db.add(att)
    await db.commit()
    await record_audit(
        action="create", entity_type="letter_attachment_ai", entity_id=aid,
        account_no=(acct or None),
        detail=f"ساختِ پیوستِ هوشمند «{filename}» ({spec['kind']}) برای نامهٔ {payload.letter_id}",
        user=user, request=request, db=db,
    )
    return {
        "ok": True, "model": result.get("model"), "kind": spec["kind"],
        "warnings": warnings,
        "attachment": {
            "id": att.id, "account_no": att.account_no, "original_name": att.original_name,
            "file_size": att.file_size, "upload_date": att.upload_date,
            "uploaded_by": att.uploaded_by,
            "storage": "drive" if drive_file_id else "disk",
            "ai_generated": True,
        },
    }
