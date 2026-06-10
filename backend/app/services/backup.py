"""Build a portable JSON snapshot of the whole CRM business dataset.

Single source of truth for "what a backup contains", reused by:
  * the admin download endpoint (GET /api/crm/backup/export.json), and
  * the Google Drive sync (drive_sync.sync_database_snapshot).

Users and personal notes are intentionally excluded — a backup is of the shared
business data, not of accounts/credentials or private per-user content.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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
    }


async def build_backup_payload(db: AsyncSession) -> dict:
    """Return the full backup as a JSON-serializable dict with a counts summary."""
    data: dict = {}
    for name, model in _targets().items():
        try:
            objs = (await db.execute(select(model))).scalars().all()
            data[name] = [_serialize(o) for o in objs]
        except Exception as exc:  # pragma: no cover - defensive per-table guard
            data[name] = {"error": str(exc)[:120]}

    counts = {k: (len(v) if isinstance(v, list) else 0) for k, v in data.items()}
    return {
        "generated": datetime.utcnow().isoformat() + "Z",
        "counts": counts,
        "data": data,
    }
