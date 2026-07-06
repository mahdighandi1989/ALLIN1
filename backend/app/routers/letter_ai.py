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

from fastapi import APIRouter, Depends, Request
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


class ApplyDbRequest(BaseModel):
    items: List[DbWriteItem] = Field(default_factory=list)


@router.post("/apply-db")
async def apply_db(
    payload: ApplyDbRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Persist the user-approved extracted facts into the right customer
    profile(s) — dedup + staleness guarded, creating profiles as needed, auditing
    every write to the account (global log + that profile's «Logs» tab)."""
    items = [i.model_dump() for i in (payload.items or [])
             if (i.account_no or "").strip() and (i.key or "").strip()]
    if not items:
        return {"ok": True, "outcomes": [],
                "counts": {"added": 0, "updated": 0, "skipped": 0, "profiles_created": 0}}
    return await db_extract.apply_db_writes(db, user, request, items)
