"""Document upload storage for per-row / per-checklist attachments (A10 / A15).

Files are stored on disk under ``UPLOAD_DIR``, organised per customer + facility,
so each document is archived to a stable reference in the customer's folder
(mirroring the Excel central-folder archive). Only the metadata lives in the
``attachments`` table; the bytes live on disk and are streamed back by the
download endpoint — so a scanned document actually opens again (the Excel A15
bug where "the file shows as scanned but nothing opens").

``UPLOAD_DIR`` defaults to ``backend/uploads`` and can be pointed at a persistent
volume in production via the ``UPLOAD_DIR`` env var.
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "uploads")))

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe(name: str, fallback: str) -> str:
    cleaned = _SAFE.sub("_", (name or "").strip()).strip("._") or fallback
    return cleaned[:120]


def storage_dir(account_no: str, facility_id: str = "") -> Path:
    acc = _safe(account_no, "account")
    fac = _safe(facility_id, "general") if (facility_id or "").strip() else "general"
    return UPLOAD_DIR / acc / fac


def save_bytes_sync(account_no: str, facility_id: str, filename: str, data: bytes) -> tuple[str, int, str]:
    """Persist already-read bytes under the customer/facility folder.

    Returns ``(relative_path, size_bytes, stored_filename)``. Used when the caller
    needs the bytes for more than just disk (e.g. to also mirror to Drive) and has
    therefore already read the UploadFile.
    """
    folder = storage_dir(account_no, facility_id)
    folder.mkdir(parents=True, exist_ok=True)
    original = _safe(filename or "file", "file")
    stored = f"{uuid.uuid4().hex[:12]}_{original}"
    dest = folder / stored
    dest.write_bytes(data)
    return str(dest.relative_to(UPLOAD_DIR)), len(data), stored


async def save_bytes(account_no: str, facility_id: str, filename: str, data: bytes) -> tuple[str, int, str]:
    """Async-friendly wrapper around :func:`save_bytes_sync`."""
    return save_bytes_sync(account_no, facility_id, filename, data)


async def save_upload(account_no: str, facility_id: str, upload) -> tuple[str, int, str]:
    """Persist an UploadFile under the customer/facility folder.

    Returns ``(relative_path, size_bytes, stored_filename)``.
    """
    data = await upload.read()
    return save_bytes_sync(account_no, facility_id, getattr(upload, "filename", "") or "file", data)


def resolve(file_path: str) -> Path | None:
    """Resolve a stored relative path to an absolute path *inside* UPLOAD_DIR.

    Returns ``None`` if the path escapes UPLOAD_DIR (defence-in-depth against
    traversal) or the file no longer exists on disk.
    """
    if not file_path:
        return None
    base = UPLOAD_DIR.resolve()
    target = (UPLOAD_DIR / file_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target if target.exists() else None
