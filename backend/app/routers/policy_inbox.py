"""Drive «policy inbox» endpoints (v117). Wired at /api/policy-inbox.

Flow: the owner drops issued-policy scans + one mapping Excel into the
dedicated Drive folder (``ensure`` creates it and returns the link) →
``scan`` lists what's there and parses the Excel → ``apply`` reads each
policy's printed identifiers with one small multimodal call, matches the
UNIQUE Excel row and renames the file to ``{branch}-{account}-{original}``
(conservative: ambiguity is reported, never guessed) → ``import-file`` runs
one renamed file through the SAME background import-job pipeline as a browser
upload (v106 restart-survivable, v114 retry/coverage), downloading it
straight from Drive so nothing is re-uploaded by hand.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.routers.auth import get_current_active_user, require_editor
from app.services import drive_sync, google_drive
from app.services import policy_inbox as box
from app.services.audit import record_audit

logger = logging.getLogger("app.policy_inbox")

router = APIRouter(tags=["policy-inbox"], dependencies=[Depends(get_current_active_user)])

_EXCEL_EXT = (".xlsx", ".xlsm", ".xls")
_IDS_PROMPT = (
    "این تصویر/سند یک بیمه‌نامهٔ فارسیِ صادرشده است. فقط و فقط این JSON را برگردان — بدونِ متنِ اضافه:\n"
    '{"computer_code": "", "policy_no": "", "unique_code": "", "national_id": ""}\n'
    "computer_code = کد رایانهٔ بیمه‌نامه؛ policy_no = شمارهٔ بیمه‌نامه؛ "
    "unique_code = کد یکتای بیمه مرکزی؛ national_id = کد ملیِ مالک/راهن (نه شناسهٔ ملیِ بیمه‌گذارِ بانکی). "
    "اعداد را دقیقاً همان‌طور که چاپ شده بنویس؛ هر موردی که روی سند نیست خالی بگذار؛ هرگز حدس نزن."
)


def _mode_warning() -> str:
    if settings.drive_auth_mode() == "oauth":
        return ("اتصالِ درایو در حالتِ OAuth است (دسترسیِ drive.file) — فایل‌هایی که خودت مستقیم در "
                "پوشه می‌گذاری برای برنامه قابل‌مشاهده نیستند. برای این گردش‌کار باید حالتِ "
                "Service Account فعال باشد.")
    return ""


async def _ready_folder() -> str:
    if not drive_sync.is_enabled():
        raise HTTPException(status_code=503, detail="سرویسِ Google Drive پیکربندی/فعال نیست (تنظیمات → درایو).")
    await drive_sync.prepare()
    try:
        return await asyncio.to_thread(google_drive.ensure_folder_path, [box.FOLDER_NAME])
    except google_drive.DriveError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/ensure")
async def ensure_inbox(user=Depends(require_editor)):
    """Create (idempotently) the Drive drop-folder and return its link."""
    folder_id = await _ready_folder()
    try:
        link = await asyncio.to_thread(google_drive.file_link, folder_id)
    except google_drive.DriveError:
        link = ""
    return {"ok": True, "folder_id": folder_id, "link": link,
            "name": box.FOLDER_NAME, "warning": _mode_warning()}


async def _list_and_excel() -> Dict:
    """List the inbox + parse the FIRST Excel found (the mapping table)."""
    folder_id = await _ready_folder()
    try:
        files = await asyncio.to_thread(google_drive.list_folder, folder_id)
    except google_drive.DriveError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    pdfs = [f for f in files if (f.get("mimeType") == "application/pdf"
                                 or str(f.get("name", "")).lower().endswith(".pdf"))]
    excels = [f for f in files if str(f.get("name", "")).lower().endswith(_EXCEL_EXT)]
    mapping = None
    if excels:
        try:
            data = await asyncio.to_thread(google_drive.download_file, excels[0]["id"])
            mapping = box.parse_mapping_workbook(data)
            mapping["file"] = excels[0]["name"]
        except google_drive.DriveError as exc:
            mapping = {"ok": False, "error": f"دانلودِ اکسل ناموفق بود: {exc}", "rows": [], "warnings": []}
    return {"folder_id": folder_id, "pdfs": pdfs, "excels": excels, "mapping": mapping}


@router.post("/scan")
async def scan_inbox(user=Depends(require_editor)):
    """What's in the folder right now + is the mapping Excel usable?"""
    st = await _list_and_excel()
    named = [f for f in st["pdfs"] if box.already_named(f["name"])]
    return {
        "ok": True,
        "folder_id": st["folder_id"],
        "pdf_count": len(st["pdfs"]),
        "named_count": len(named),
        "files": [{"id": f["id"], "name": f["name"], "named": box.already_named(f["name"])}
                  for f in st["pdfs"]],
        "excel": ({"file": st["mapping"].get("file"), "ok": st["mapping"].get("ok"),
                   "rows": len(st["mapping"].get("rows") or []),
                   "columns": st["mapping"].get("columns"),
                   "error": st["mapping"].get("error"),
                   "warnings": st["mapping"].get("warnings")} if st["mapping"] else None),
        "warning": _mode_warning(),
    }


class ApplyRequest(BaseModel):
    model_id: Optional[int] = None
    limit: int = Field(default=4, ge=1, le=8)
    # files already tried and left unmatched this session — the UI passes them
    # back so a stuck file can't loop forever
    exclude_ids: List[str] = Field(default_factory=list)


@router.post("/apply")
async def apply_renames(
    payload: ApplyRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Rename up to ``limit`` policies per call: read identifiers → unique Excel
    row → ``{branch}-{account}-{original}``. Bounded per call so each HTTP
    request stays inside the gateway deadline; the UI loops until done."""
    from app.ai import inference
    from app.services import doc_ingest

    st = await _list_and_excel()
    if not st["mapping"]:
        raise HTTPException(status_code=422, detail="در پوشه هیچ فایلِ اکسلِ نگاشت پیدا نشد — اول جدول را آپلود کن.")
    if not st["mapping"].get("ok"):
        raise HTTPException(status_code=422, detail=st["mapping"].get("error") or "اکسلِ نگاشت قابل‌استفاده نیست.")
    rows = st["mapping"]["rows"]

    skip = set(payload.exclude_ids or [])
    todo = [f for f in st["pdfs"] if not box.already_named(f["name"]) and f["id"] not in skip]
    batch, rest = todo[: payload.limit], todo[payload.limit:]
    if not batch:
        return {"ok": True, "processed": [], "remaining": 0, "pdf_count": len(st["pdfs"])}

    rr = await inference.resolve_multimodal(db, [{"mimetype": "application/pdf"}],
                                            model_id=payload.model_id)
    if not rr.get("ok"):
        err = rr.get("error")
        if err == "no_model":
            raise HTTPException(status_code=400, detail="هیچ مدلِ سندخوان در تنظیمات فعال نیست.")
        raise HTTPException(status_code=422, detail={"error": err, "model": rr.get("model"),
                                                     "suggestions": rr.get("suggestions", [])})
    resolved = rr["resolved"]

    sem = asyncio.Semaphore(3)

    async def _one(f: Dict) -> Dict:
        out = {"id": f["id"], "name": f["name"], "renamed": False}
        try:
            data = await asyncio.to_thread(google_drive.download_file, f["id"])
        except google_drive.DriveError as exc:
            out["reason"] = f"دانلود ناموفق: {exc}"
            return out
        async with sem:
            res = await inference.send_multimodal(
                resolved, _IDS_PROMPT,
                [{"filename": f["name"], "mimetype": "application/pdf", "data": data}],
                max_tokens=300)
            e0 = str(res.get("error") or "")
            if not res.get("ok") and ("timed out" in e0 or "connection failed" in e0 or "429" in e0):
                await asyncio.sleep(3)
                res = await inference.send_multimodal(
                    resolved, _IDS_PROMPT,
                    [{"filename": f["name"], "mimetype": "application/pdf", "data": data}],
                    max_tokens=300)
        data = None
        if not res.get("ok"):
            out["reason"] = f"خواندنِ شناسه‌ها ناموفق: {res.get('error')}"
            return out
        ids = doc_ingest.parse_model_json(res.get("text", ""))
        row, how = box.match_row(ids if isinstance(ids, dict) else {}, rows)
        if row is None:
            out["reason"] = how
            out["ids"] = {k: str((ids or {}).get(k) or "") for k in box.MATCH_KEYS} if isinstance(ids, dict) else {}
            return out
        new_name = box.build_new_name(row.get("branch", ""), row.get("account", ""), f["name"])
        try:
            await asyncio.to_thread(google_drive.rename_file, f["id"], new_name)
        except google_drive.DriveError as exc:
            out["reason"] = f"تغییرنام ناموفق: {exc}"
            return out
        out.update({"renamed": True, "new_name": new_name, "matched_by": how,
                    "account": box.norm_digits(row.get("account")),
                    "customer": row.get("name", "")})
        return out

    processed = list(await asyncio.gather(*(_one(f) for f in batch)))
    n_ok = sum(1 for p in processed if p.get("renamed"))
    if n_ok:
        await record_audit(
            action="update", entity_type="drive_file", entity_id=st["folder_id"],
            account_no=None,
            detail=(f"نام‌گذاری خودکارِ {n_ok} بیمه‌نامه در پوشهٔ درایو «{box.FOLDER_NAME}» "
                    "بر اساسِ اکسلِ نگاشت (شعبه-حساب-نامِ قبلی)"),
            user=user, request=None, db=db,
        )
    return {"ok": True, "processed": processed,
            "remaining": len(rest), "pdf_count": len(st["pdfs"])}


class ImportFileRequest(BaseModel):
    file_id: str
    model_id: Optional[int] = None
    instructions: str = Field(default="", max_length=6000)


@router.post("/import-file")
async def import_from_drive(
    payload: ImportFileRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Run ONE inbox file through the normal import-job pipeline, downloading it
    from Drive server-side (no manual re-upload). Poll /api/imports/jobs/{id}."""
    from app.routers import imports as imp

    folder_id = await _ready_folder()
    try:
        files = await asyncio.to_thread(google_drive.list_folder, folder_id)
    except google_drive.DriveError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    meta = next((f for f in files if f.get("id") == payload.file_id), None)
    if meta is None:
        raise HTTPException(status_code=404, detail="فایل در پوشهٔ بیمه‌نامه‌ها پیدا نشد.")
    try:
        data = await asyncio.to_thread(google_drive.download_file, payload.file_id)
    except google_drive.DriveError as exc:
        raise HTTPException(status_code=502, detail=f"دانلود از درایو ناموفق: {exc}")
    if not data:
        raise HTTPException(status_code=422, detail="فایل خالی است.")
    if len(data) > imp._PDF_MAX_BYTES:
        raise HTTPException(status_code=413, detail="فایل بزرگ‌تر از سقفِ ایمپورت است.")

    fname = meta.get("name") or "policy.pdf"
    mime = meta.get("mimeType") or "application/pdf"
    import uuid as _uuid
    job_id = f"IMP-{_uuid.uuid4().hex[:12]}"
    username = getattr(user, "username", "") or ""
    instr = (payload.instructions or "").strip()
    await imp._create_job(db, job_id, fname, username, data=data, mime=mime,
                          model_id=payload.model_id, instructions=instr)
    await imp._spawn_job(job_id, data, fname, mime, payload.model_id, username,
                         instructions=instr)
    return {"ok": True, "job_id": job_id, "status": "running", "filename": fname}
