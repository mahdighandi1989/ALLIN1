"""Build a portable JSON snapshot of the whole CRM business dataset.

Single source of truth for "what a backup contains", reused by:
  * the admin download endpoint (GET /api/crm/backup/export.json), and
  * the Google Drive sync (drive_sync.sync_database_snapshot).

Users and personal notes are intentionally excluded — a backup is of the shared
business data, not of accounts/credentials or private per-user content.
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Page size for reading each table when building a backup — keeps memory bounded
# on large tables. Kept modest because rows like customer_profiles carry large
# data_json blobs, so a big page would briefly hold many MB at once.
_BACKUP_CHUNK = 500


def _serialize(obj) -> dict:
    """Flatten an ORM row into a JSON-safe dict (Decimal/enum/datetime aware)."""
    row = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.name)
        if isinstance(value, Decimal):
            value = float(value)
        elif hasattr(value, "value"):  # Enum -> its value
            value = value.value
        elif hasattr(value, "isoformat"):  # date/datetime -> ISO string
            value = value.isoformat()
        row[col.name] = value
    return row


def _targets() -> dict:
    """Map each export section name to its ORM model (imported lazily)."""
    from app.models.crm import (
        ChecklistProgress,
        FacilityChecklist,
        CustomTask,
        CustomerProfile,
        CustomerNote,
        JournalEntry,
        Attachment,
    )
    from app.models.customer import Customer
    from app.models.facility import Facility
    from app.models.guarantor import Guarantor
    from app.models.profile_entities import MortgagedProperty, FixedDeposit, Partner
    from app.models.security import Security
    from app.models.general import (
        GeneralProfile,
        GeneralChecklist,
        GeneralChecklistItem,
    )
    # v157 — owner DATA that the snapshot silently omitted. A restore from a
    # backup without these came back with no letters, no offer letters, no credit
    # reviews, no tariff, no FX history and an empty knowledge base. See
    # docs/DATA_SURFACE_CHECKLIST.md; the table below is now enforced by a test.
    from app.models.case_report import CaseReport
    from app.models.charge_tariff import ChargeRule
    from app.models.credit_review import CreditReview
    from app.models.customer_link_rel import CustomerLink
    from app.models.department import Department
    from app.models.exchange_rate import ExchangeRate
    from app.models.inspection import (
        InspectionBinder, InspectionFile, InspectionReport, InspectionShot,
    )
    from app.models.kb import KnowledgeEntry, KnowledgeTopic
    from app.models.kb_chat import KbChatFile, KbChatMessage, KbChatSession
    from app.models.letter import Letter
    from app.models.offer_letter import OfferAttachment, OfferCalculation, OfferLetter
    from app.models.personal import PersonalNote
    from app.models.profile_entities import PropertyEvent
    from app.models.staff import StaffMember
    from app.models.system_setting import SystemSetting

    return {
        "customers": Customer,
        "facilities": Facility,
        "customer_profiles": CustomerProfile,
        "guarantors": Guarantor,
        "securities": Security,
        "mortgaged_properties": MortgagedProperty,
        "fixed_deposits": FixedDeposit,
        "partners": Partner,
        "checklist_progress": ChecklistProgress,
        "facility_checklists": FacilityChecklist,
        "custom_tasks": CustomTask,
        "customer_notes": CustomerNote,
        "journal_entries": JournalEntry,
        "attachments": Attachment,
        "general_profiles": GeneralProfile,
        "general_checklists": GeneralChecklist,
        "general_checklist_items": GeneralChecklistItem,
        "property_events": PropertyEvent,
        "customer_links": CustomerLink,
        # documents the branch produces — losing these loses work nobody can redo
        "letters": Letter,
        "case_reports": CaseReport,
        "credit_reviews": CreditReview,
        "offer_letters": OfferLetter,
        "offer_attachments": OfferAttachment,
        "offer_calculations": OfferCalculation,
        # reference data the system is configured with
        "charge_rules": ChargeRule,
        "exchange_rates": ExchangeRate,
        "departments": Department,
        "staff_members": StaffMember,
        "system_settings": SystemSetting,
        "kb_topics": KnowledgeTopic,
        "kb_entries": KnowledgeEntry,
        "kb_chat_sessions": KbChatSession,
        "kb_chat_messages": KbChatMessage,
        "kb_chat_files": KbChatFile,
        "personal_notes": PersonalNote,
        # the owner's own supervision record
        "inspection_binders": InspectionBinder,
        "inspection_reports": InspectionReport,
        "inspection_files": InspectionFile,
        "inspection_shots": InspectionShot,
    }


# Tables deliberately LEFT OUT of the snapshot, each with the reason. This is not
# a list of things nobody got round to: it is a decision, and the test in
# tests/test_backup_covers_every_table.py makes every NEW table land in one of
# these two places before it can be merged. Changing an entry here is a decision
# about the owner's data, so it belongs in docs/AUDIT_LOG.md too.
BACKUP_EXCLUDED = {
    "users": "credentials (password hashes, roles) — putting them in a Drive file "
             "is the owner's call, not a default",
    "ai_providers": "holds provider API keys; a Drive snapshot of live credentials "
                    "is a separate decision from backing up customer data",
    "ai_models": "model config tied to the provider keys above; re-entered in "
                 "Settings in a minute and not worth snapshotting credentials for",
    "ai_task_routes": "routing config for the two above; meaningless without them",
    "audit_logs": "append-only and unbounded; it would dominate every snapshot "
                  "and needs its own retention decision",
    "notifications": "transient UI state, rebuilt by the expiry scan",
    "notification_reads": "which user dismissed which bell notification; rebuilt as people read them and worthless after a restore",
    "cleanup_runs": "run history of a maintenance tool, not customer data",
    "exposure_snapshots": "derived from facilities + exchange_rates",
    "import_jobs": "operational history of past uploads",
}


async def build_backup_payload(db: AsyncSession) -> dict:
    """Return the full backup as a JSON-serializable dict with a counts summary.

    Each table is read in bounded pages (never ``select(model)).all()`` on the
    whole table) so a large table — e.g. ~44k customer_profiles after the customer
    listing import — can't materialise tens of thousands of ORM rows at once and
    OOM the 512MB instance. Only one page of ORM objects is held at a time; the
    serialized dicts accumulate into the result.
    """
    data: dict = {}
    for name, model in _targets().items():
        try:
            rows: list = []
            pk = model.__mapper__.primary_key[0]
            offset = 0
            while True:
                chunk = (
                    await db.execute(
                        select(model).order_by(pk).offset(offset).limit(_BACKUP_CHUNK)
                    )
                ).scalars().all()
                if not chunk:
                    break
                rows.extend(_serialize(o) for o in chunk)
                offset += len(chunk)
                if len(chunk) < _BACKUP_CHUNK:
                    break  # last (partial) page
            data[name] = rows
        except Exception as exc:  # pragma: no cover - defensive per-table guard
            data[name] = {"error": str(exc)[:120]}

    counts = {k: (len(v) if isinstance(v, list) else 0) for k, v in data.items()}
    return {
        "generated": datetime.utcnow().isoformat() + "Z",
        "counts": counts,
        "data": data,
    }


async def stream_backup_to_file(db: AsyncSession, fh) -> dict:
    """Write the full backup as compact JSON to text file handle ``fh`` ONE PAGE
    at a time, so the whole dataset is never materialised in memory.

    This is the memory-safe path used by the Drive snapshot and the admin export:
    ``build_backup_payload`` holds every serialized row at once (fine for small
    DBs, but a ~44k-row customer_profiles table with large data_json blobs would
    OOM the 512MB instance), whereas this keeps only one page (rows + their JSON)
    resident. Returns the counts dict.
    """
    counts: dict = {}
    fh.write('{"generated":')
    fh.write(json.dumps(datetime.utcnow().isoformat() + "Z"))
    fh.write(',"data":{')
    first_table = True
    for name, model in _targets().items():
        fh.write(("" if first_table else ",") + json.dumps(name) + ":[")
        first_table = False
        n = 0
        try:
            pk = model.__mapper__.primary_key[0]
            offset = 0
            first_row = True
            while True:
                chunk = (
                    await db.execute(
                        select(model).order_by(pk).offset(offset).limit(_BACKUP_CHUNK)
                    )
                ).scalars().all()
                if not chunk:
                    break
                for o in chunk:
                    fh.write(("" if first_row else ",") + json.dumps(_serialize(o), ensure_ascii=False))
                    first_row = False
                    n += 1
                offset += len(chunk)
                if len(chunk) < _BACKUP_CHUNK:
                    break
        except Exception as exc:  # pragma: no cover - defensive per-table guard
            counts[f"{name}__error"] = str(exc)[:120]
        fh.write("]")
        counts[name] = n
    fh.write('},"counts":' + json.dumps(counts, ensure_ascii=False) + "}")
    return counts
