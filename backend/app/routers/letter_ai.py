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

import logging
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

logger = logging.getLogger("app.letter_ai")

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
    # v123 — anything the budget had to cut comes back here and is surfaced to
    # the user as review rows; a silently trimmed input is what made partial
    # answers look complete.
    prompt_warnings: List[str] = []
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
        warnings_out=prompt_warnings,
    )

    # v93 — the analyze prompt can be very large (attachment PDFs' text, all
    # tools, tables, archive tone samples): the 60s default inference deadline
    # expired for the owner exactly like the generator path (v89). Long deadline
    # + one transient retry; the UI already waits 300s.
    async def _an_complete(p_):
        import asyncio as _aio
        res = await inference.complete(
            db, p_, task="report_drafting", system=system,
            model_id=payload.model_id, max_tokens=16000, timeout=240.0,
            # No explicit temperature: newer reasoning models (Opus 4.8) reject it
            # with a 400. inference.complete also strips+retries as a backstop for
            # any model that carries a configured temperature.
        )
        err0 = str(res.get("error") or "")
        if not res.get("ok") and ("timed out" in err0 or "connection failed" in err0 or "429" in err0):
            await _aio.sleep(3)
            res = await inference.complete(
                db, p_, task="report_drafting", system=system,
                model_id=payload.model_id, max_tokens=16000, timeout=240.0,
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

    # v123 — a trimmed input must never masquerade as a complete answer: every
    # budget cut becomes a HIGH-severity advisory row at the TOP of the review
    # list, so «چرا ناقص بود؟» is answered before the user asks.
    if prompt_warnings:
        notes = [{
            "id": f"trunc-{i}", "op": "note", "category": "consistency", "field": "",
            "severity": "high", "applicable": False,
            "title": "هشدار: همهٔ محتوای پیوست‌ها به مدل نرسید — نتیجه ممکن است ناقص باشد",
            "detail": w,
        } for i, w in enumerate(prompt_warnings, 1)]
        changes = notes + changes

    await record_audit(
        action="analyze", entity_type="letter_ai", entity_id=None,
        account_no=(payload.account_no or None),
        detail=f"دستیار هوشمندِ نامه — {len(changes)} پیشنهاد ({', '.join(tools)})"
               + (f" — {len(prompt_warnings)} هشدارِ بریده‌شدنِ ورودی" if prompt_warnings else ""),
        user=user, request=request, db=db,
    )
    return {
        "ok": True,
        "model": result.get("model"),
        "changes": changes,
        "count": len(changes),
        "facts_used": bool(facts),
        "tools": tools,
        "input_warnings": prompt_warnings,
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


# v121 — ONE approved nested-collection entry (facility / mortgaged property /
# guarantor / partner / security row). `payload` is the extractor's own dict,
# handed unchanged to doc_ingest.persist_customer — the Import page's writer.
class EntityWriteItem(BaseModel):
    id: str = ""
    account_no: str = ""
    customer_name: str = ""
    entity_key: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)


class ApplyDbRequest(BaseModel):
    items: List[DbWriteItem] = Field(default_factory=list)
    links: List[LinkItem] = Field(default_factory=list)
    kb_items: List[KbWriteItem] = Field(default_factory=list)
    entities: List[EntityWriteItem] = Field(default_factory=list)
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

    # v121 — approved nested collections (facilities / mortgaged properties /
    # guarantors / partners / security). Grouped per account and handed to the
    # IMPORT page's own writer, so this path gains every guard it already has
    # instead of growing a second, drifting one. A per-account failure is
    # isolated and reported; it never aborts the rest of the apply.
    ent_counts: Dict[str, int] = {}
    ent_errors: List[str] = []
    if payload.entities:
        from app.services import doc_ingest
        allowed = {k for k, _kind, _lbl in lax_specs()}
        grouped: Dict[str, Dict[str, Any]] = {}
        for en in payload.entities:
            acc = (en.account_no or "").strip()
            key = (en.entity_key or "").strip()
            if not acc or key not in allowed or not isinstance(en.payload, dict) or not en.payload:
                continue
            cust = grouped.setdefault(acc, {"account_no": acc, "fields": {},
                                            "name": (en.customer_name or "").strip()})
            cust.setdefault(key, []).append(en.payload)
        username = getattr(user, "username", "") or ""
        for acc, cust in grouped.items():
            try:
                res = await doc_ingest.persist_customer(
                    db, cust, username, source="letter_attachment_ai")
            except Exception as exc:  # noqa: BLE001 — one account must not sink the batch
                logger.warning("entity apply failed for %s: %s", acc, exc)
                ent_errors.append(f"{acc}: {exc}")
                continue
            if not res.get("ok"):
                ent_errors.append(f"{acc}: {res.get('reason') or 'failed'}")
                continue
            for k in ("facilities_added", "facilities_updated", "properties_added",
                      "properties_updated", "property_events_added", "guarantors_added",
                      "guarantors_updated", "partners_added", "partners_updated",
                      "security_added", "facilities_skipped_deposits"):
                if res.get(k):
                    ent_counts[k] = ent_counts.get(k, 0) + int(res[k])
        await db.commit()
        for acc in grouped:
            await record_audit(
                action="update", entity_type="letter_attachment_entities", entity_id=acc,
                account_no=acc,
                detail=("ثبتِ تسهیلات/املاک/ضامن/شریک/وثیقهٔ تأییدشده از پیوستِ نامه"
                        + (f" ({payload.source_ref})" if payload.source_ref else "")),
                user=user, request=request, db=db,
            )
    result["entity_counts"] = ent_counts
    result["entity_errors"] = ent_errors
    return result


def lax_specs():
    """The nested-collection keys the attachment path may write (single source
    of truth shared with the staging side)."""
    from app.services.letter_attachment_extract import _ENTITY_SPECS
    return _ENTITY_SPECS


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
    """Deep-extract ONE letter attachment, in the foreground (kept as-is: it is
    still the single-file path and the batch job's building block)."""
    return await _extract_one_attachment(attachment_id, payload, request, db, user)


async def _extract_one_attachment(
    attachment_id: str,
    payload: "ExtractAttachmentRequest",
    request: Optional[Request],
    db: AsyncSession,
    user,
):
    """Deep-extract ONE letter attachment. Returns staged, reviewable changes —
    writes nothing. Pipeline + guards mirror the Import page (chunking/backoff/
    caps). Shared by the single-file route and the v121 background batch job."""
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


# ---------------------------------------------------------------------------
# v121 (part ب) — BATCH extraction as a background job.
#
# The UI used to loop the single-file route itself: N foreground requests that
# only survive while the tab is open, each capped by the browser's timeout. With
# 20+ attachments that is a 20-60 minute marathon the user must babysit. The
# Import page solved exactly this with jobs, so the batch reuses the SAME
# ImportJob table and helpers (`_job_session`, `_BG_TASKS`) instead of inventing
# a second mechanism: the loop stays strictly sequential (one attachment in
# memory at a time — the OOM lesson), each file is still isolated by its own
# try/except, and progress + accumulated changes are written to the job row
# after EVERY file so a poll always sees partial results.
# The single-file route is untouched and remains the fallback (rule 2).
# ---------------------------------------------------------------------------
class ExtractAttachmentsBatchRequest(ExtractAttachmentRequest):
    attachment_ids: List[str] = Field(default_factory=list)


def _job_progress(job_row, *, done: int, total: int, current: str,
                  changes: List[dict], errors: List[str]) -> None:
    import json as _json
    job_row.result_json = _json.dumps(
        {"done": done, "total": total, "current": current,
         "changes": changes, "errors": errors}, ensure_ascii=False)


async def _run_attachment_batch(job_id: str, attachment_ids: List[str],
                                payload_data: dict, username: str) -> None:
    """Sequentially extract every attachment, recording progress on the job row."""
    import json as _json
    from sqlalchemy import func as _func
    from app.models.import_job import ImportJob
    from app.routers.imports import _job_session

    changes: List[dict] = []
    errors: List[str] = []
    total = len(attachment_ids)
    try:
        for i, att_id in enumerate(attachment_ids):
            # Each attachment gets its OWN session+transaction so one bad file
            # can never poison the next one's unit of work.
            async with _job_session() as db:
                name = att_id
                try:
                    from app.models.crm import Attachment
                    a = (await db.execute(select(Attachment).where(
                        Attachment.id == att_id))).scalar_one_or_none()
                    name = (a.original_name or a.file_name or att_id) if a else att_id
                    res = await _extract_one_attachment(
                        att_id, ExtractAttachmentRequest(**payload_data), None, db,
                        _JobUser(username),
                    )
                    if res.get("ok"):
                        for it in (res.get("changes") or []):
                            it["source_file"] = name
                        changes.extend(res.get("changes") or [])
                        for ce in (res.get("chunk_errors") or []):
                            errors.append(f"{name}: {ce}")
                    else:
                        errors.append(f"{name}: {res.get('error') or 'failed'}")
                except HTTPException as exc:
                    errors.append(f"{name}: {exc.detail}")
                except Exception as exc:  # noqa: BLE001 — never sink the batch
                    logger.warning("attachment batch %s failed on %s: %s", job_id, att_id, exc)
                    errors.append(f"{name}: {exc}")
            # progress after EVERY file, in its own short transaction
            async with _job_session() as db:
                row = await db.get(ImportJob, job_id)
                if row is None or row.status != "running":
                    return  # cancelled/pruned — stop quietly
                _job_progress(row, done=i + 1, total=total, current=name,
                              changes=changes, errors=errors)
                await db.commit()
        async with _job_session() as db:
            row = await db.get(ImportJob, job_id)
            if row is not None:
                row.status = "done"
                _job_progress(row, done=total, total=total, current="",
                              changes=changes, errors=errors)
                row.finished_at = _func.now()
                await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("attachment batch %s crashed", job_id)
        try:
            async with _job_session() as db:
                row = await db.get(ImportJob, job_id)
                if row is not None:
                    row.status = "error"
                    row.http_status = 500
                    row.detail_json = _json.dumps(str(exc), ensure_ascii=False)
                    row.finished_at = _func.now()
                    await db.commit()
        except Exception:  # noqa: BLE001
            pass


async def _spawn_attachment_batch(job_id: str, ids: List[str], data: dict,
                                  username: str) -> None:
    """Fire-and-forget the batch. Overridden in tests to run it inline (the same
    pattern the Import page's ``_spawn_job`` uses) so polling is deterministic."""
    import asyncio as _aio
    from app.routers.imports import _BG_TASKS
    task = _aio.create_task(_run_attachment_batch(job_id, ids, data, username))
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)


class _JobUser:
    """Minimal user stand-in for audit records written from the background job."""
    def __init__(self, username: str):
        self.username = username
        self.id = None


@router.post("/extract-attachments-job")
async def extract_attachments_job(
    payload: ExtractAttachmentsBatchRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Queue a batch extraction of several attachments; poll /attachment-job/{id}."""
    import uuid as _uuid
    from app.models.import_job import ImportJob

    ids = [i for i in (payload.attachment_ids or []) if (i or "").strip()]
    if not ids:
        raise HTTPException(status_code=422, detail="هیچ پیوستی انتخاب نشده است")
    job_id = f"LAX-{_uuid.uuid4().hex[:12]}"
    username = getattr(user, "username", "") or ""
    db.add(ImportJob(id=job_id, status="running",
                     filename=f"{len(ids)} پیوستِ نامه", username=username, attempts=1))
    await db.commit()
    data = payload.model_dump(exclude={"attachment_ids"})
    await _spawn_attachment_batch(job_id, ids, data, username)
    return {"ok": True, "job_id": job_id, "total": len(ids)}


@router.get("/attachment-job/{job_id}")
async def attachment_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Poll a batch extraction: status + live progress + what it has staged so far."""
    import json as _json
    from app.models.import_job import ImportJob

    row = await db.get(ImportJob, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="کارِ استخراج پیدا نشد")
    prog: Dict[str, Any] = {}
    if row.result_json:
        try:
            prog = _json.loads(row.result_json)
        except Exception:  # noqa: BLE001
            prog = {}
    detail = None
    if row.detail_json:
        try:
            detail = _json.loads(row.detail_json)
        except Exception:  # noqa: BLE001
            detail = row.detail_json
    return {"ok": row.status != "error", "status": row.status,
            "done": prog.get("done", 0), "total": prog.get("total", 0),
            "current": prog.get("current", ""), "changes": prog.get("changes", []),
            "errors": prog.get("errors", []), "detail": detail}


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
    for Excel/CSV/Word/plain text; PDFs are transcribed page-chunk by page-chunk
    (v114 — every page reaches the model, gaps reported in failed_parts).
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
    return {"ok": True, "file": fname, "text": r.get("text") or "", "model": r.get("model"),
            "truncated": bool(r.get("truncated")), "failed_parts": r.get("failed_parts") or []}


@router.post("/template-text")
async def template_text_endpoint(
    file: UploadFile = File(...),
    model_id: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Readable TEXT of a TEMPLATE/SAMPLE file the user picked from their machine
    (a blank table another department sent, in any format) — for the attachment
    GENERATOR. Nothing is stored; deterministic for Excel/CSV/Word/plain text;
    PDFs are transcribed page-chunk by page-chunk (v114 — full coverage, gaps
    reported in failed_parts)."""
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
    return {"ok": True, "file": fname, "text": r.get("text") or "", "model": r.get("model"),
            "truncated": bool(r.get("truncated")), "failed_parts": r.get("failed_parts") or []}


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
    # v114: cap follows letter_attachment_extract._TEXT_CAP (120k) + headroom.
    template_text: str = Field(default="", max_length=130000)
    template_name: str = Field(default="", max_length=200)
    # v65: SOURCE/DATA files' TEXT ([{name, text}], extracted via /template-text)
    # — an allowed data source alongside the DB facts; any format, any count
    # (v114: server budgets 8 files × 120k chars, 360k total, in the prompt —
    # any cut is warned, never silent).
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
    # v89 — the source-files prompt is long (v114: budgeted 360k chars): the
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

    # v114: 16000-token output budget in round 1 too — a big source-file table
    # needs the room even when no need_data round happens.
    result = await _gen_complete(prompt, 16000)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or "ai_failed", "model": result.get("model")}

    # v114: any prompt-side truncation of source files / template surfaces as a
    # warning in the reply — an incomplete attachment must never look complete.
    fetch_warnings: list = gen.prompt_size_warnings(payload.source_files or [], tpl_text)
    need = gen.parse_need_data(result.get("text") or "")
    if need:
        fetched, _fw = await gen.fetch_datasets(db, need["datasets"], need.get("branch") or "",
                                                logs_filter=need.get("logs_filter"))
        fetch_warnings.extend(w for w in _fw if w not in fetch_warnings)
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
