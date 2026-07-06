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

from fastapi import APIRouter, Depends, HTTPException, Request
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
    return la.build_facts(customer, profile_data, list(facilities), list(guarantors))


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

    system = la.SYSTEM_PROMPT
    prompt = la.build_user_prompt(
        payload.fields or {}, facts, tools,
        instruction=payload.instruction or "", selection=payload.selection or "",
        selections=payload.selections or [],
    )

    result = await inference.complete(
        db, prompt, task="report_drafting", system=system,
        model_id=payload.model_id, max_tokens=8000,
        # No explicit temperature: newer reasoning models (Opus 4.8) reject it with
        # a 400. inference.complete also strips+retries as a backstop for any model
        # that carries a configured temperature.
    )
    if not result.get("ok"):
        # Friendly, non-fatal: the UI shows the reason (e.g. no model configured).
        return {
            "ok": False,
            "error": result.get("error") or "ai_failed",
            "model": result.get("model"),
            "changes": [],
            "facts_used": bool(facts),
        }

    changes = la.parse_and_validate(result.get("text") or "", payload.fields or {})

    # When the extract-to-DB tool is on, stage the model's db_write proposals
    # against the live database (resolve target customer + add/update/skip). These
    # are reviewed like any other change; applying them hits /apply-db.
    if "db_extract" in tools:
        raw_writes = la.parse_db_writes(result.get("text") or "")
        if raw_writes:
            primary_name = ""
            if isinstance(facts.get("customer"), dict):
                primary_name = facts["customer"].get("name") or ""
            staged = await db_extract.stage_db_writes(
                db, (payload.account_no or "").strip(), primary_name, raw_writes,
            )
            changes.extend(staged)

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


class ApplyDbRequest(BaseModel):
    items: List[DbWriteItem] = Field(default_factory=list)
    links: List[LinkItem] = Field(default_factory=list)
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
    return result


class ExtractAttachmentRequest(BaseModel):
    account_no: str = ""
    customer_name: str = ""
    subject: str = ""
    body_excerpt: str = ""
    model_id: Optional[int] = None


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
    mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"

    letter_ctx = {
        "subject": payload.subject or "", "account_no": payload.account_no or a.account_no or "",
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
        db, extraction, primary_account=(payload.account_no or a.account_no or "").strip(),
        primary_name=payload.customer_name or "", source_ref=fname,
    )
    # unique ids per attachment so items from several attachments never collide
    for it in staged:
        it["id"] = f"{attachment_id[-6:]}-{it['id']}"
        it["source_file"] = fname
    await record_audit(
        action="analyze", entity_type="letter_attachment_ai", entity_id=attachment_id,
        account_no=(payload.account_no or a.account_no or None),
        detail=f"استخراج هوشمند از پیوست «{fname}» — {len(staged)} مورد",
        user=user, request=request, db=db,
    )
    return {"ok": True, "changes": staged, "model": extraction.get("model"),
            "chunk_errors": extraction.get("chunk_errors", []), "file": fname}
