"""Seed the bundled Persian-Gulf staff directory on first run.

Idempotent: only inserts when the ``staff_members`` table is empty, so it never
overwrites edits people make later. The data ships as a JSON file next to the app
so the deployed instance gets the directory automatically (no manual import).
"""
import json
import logging
import os

from sqlalchemy import select, func

from app.models.staff import StaffMember

logger = logging.getLogger(__name__)
_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "staff_directory.json")


async def seed_staff(session) -> int:
    """Insert the bundled directory if the table is empty. Best-effort."""
    try:
        count = (await session.execute(select(func.count()).select_from(StaffMember))).scalar() or 0
        if count:
            return 0
        if not os.path.exists(_JSON):
            return 0
        with open(_JSON, encoding="utf-8") as fh:
            rows = json.load(fh)
        for r in rows:
            session.add(StaffMember(
                name=(r.get("name") or "").strip()[:200],
                department=(r.get("department") or "").strip()[:200],
                telephone=(r.get("telephone") or "").strip()[:60],
                ext=(r.get("ext") or "").strip()[:20],
                fax=(r.get("fax") or "").strip()[:60],
                email=(r.get("email") or "").strip()[:150],
                region="Persian Gulf",
            ))
        await session.commit()
        logger.info("seed_staff: inserted %d staff members", len(rows))
        return len(rows)
    except Exception as exc:  # pragma: no cover - never block startup
        logger.warning("seed_staff failed: %s", exc)
        try:
            await session.rollback()
        except Exception:
            pass
        return 0
