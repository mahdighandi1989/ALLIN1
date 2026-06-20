"""Excel/CSV import endpoints. Wired at /api/imports."""
import logging
from decimal import Decimal, InvalidOperation
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.services.excel_import import (
    parse_workbook,
    cell_str,
    ExcelParseError,
    validate_required_columns,
)
from app.services.exporters import rows_to_csv
from app.services.audit import record_audit
from app.routers.auth import get_current_active_user
from fastapi import Response

logger = logging.getLogger("app.imports")

router = APIRouter(tags=["imports"], dependencies=[Depends(get_current_active_user)])

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_EXTENSIONS = (".xlsx", ".xlsm", ".xls")


class ImportRowError(BaseModel):
    """A single row that could not be imported, with a human-readable reason."""

    row: int
    error: str


class ImportResult(BaseModel):
    """Typed, documented response for both import endpoints."""

    dry_run: bool
    total_rows: int
    created: int
    would_create: int
    skipped_existing: int = 0
    errors: List[ImportRowError] = []


def _to_decimal(v) -> Decimal:
    s = cell_str(v).replace(",", "")
    if s == "":
        raise ValueError("empty number")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError(f"'{s}' is not a number")


async def _read_upload(file: UploadFile) -> bytes:
    name = (file.filename or "").lower()
    if not name.endswith(_ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400, detail="Please upload an .xlsx, .xlsm or .xls file"
        )
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    return content


def _parse_or_400(content: bytes, filename: str | None) -> tuple:
    """Parse the workbook, turning ExcelParseError into a precise 400.

    Logs every failure (with its ``kind``) so a malformed upload is observable
    in production rather than vanishing behind a generic error.
    """
    try:
        return parse_workbook(content)
    except ExcelParseError as exc:
        logger.warning(
            "import parse failed kind=%s file=%s: %s", exc.kind, filename, exc
        )
        raise HTTPException(status_code=400, detail=f"Invalid spreadsheet: {exc}")


def _require_columns(headers, required) -> None:
    """Fail fast with a clear 400 if the sheet is missing required columns."""
    missing = validate_required_columns(headers, required)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required column(s): {', '.join(missing)}",
        )


@router.get("/customers/template")
async def customers_template():
    """Download a CSV template for customer import."""
    headers = ["account_no", "name", "account_type", "email", "phone", "branch", "status"]
    sample = [["AE-900001", "Sample Trading LLC", "corporate", "info@sample.ae", "+97140000000", "Dubai Main", "active"]]
    return Response(
        content=rows_to_csv(headers, sample),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="customers-template.csv"'},
    )


@router.get("/facilities/template")
async def facilities_template():
    headers = ["account_no", "name", "facility_type", "amount", "currency", "interest_rate", "status"]
    sample = [["AE-900001", "Term Loan", "loan", "1000000", "AED", "6.5", "active"]]
    return Response(
        content=rows_to_csv(headers, sample),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="facilities-template.csv"'},
    )


@router.post("/customers", response_model=ImportResult)
async def import_customers(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Validate only; do not write"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Import customers from an Excel file.

    Expected columns (case-insensitive): account_no, name, account_type, email,
    phone, branch, status. account_no + name are required. Existing account
    numbers are skipped. Returns a per-row result summary.
    """
    content = await _read_upload(file)
    headers, rows = _parse_or_400(content, file.filename)
    _require_columns(headers, ["account_no", "name"])

    valid_types = {t.value for t in AccountType}
    valid_status = {s.value for s in CustomerStatus}

    created = 0
    skipped = 0
    errors = []
    to_add = []
    seen_accounts = set()

    for idx, row in enumerate(rows, start=2):  # row 1 is the header
        account_no = cell_str(row.get("account_no"))
        name = cell_str(row.get("name"))
        if not account_no or not name:
            errors.append({"row": idx, "error": "account_no and name are required"})
            continue
        if account_no in seen_accounts:
            errors.append({"row": idx, "error": f"duplicate account_no '{account_no}' in file"})
            continue
        seen_accounts.add(account_no)

        # Skip if the account already exists.
        existing = (
            await db.execute(select(Customer.id).where(Customer.account_no == account_no))
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        acc_type = cell_str(row.get("account_type")).lower() or "retail"
        if acc_type not in valid_types:
            errors.append({"row": idx, "error": f"invalid account_type '{acc_type}'"})
            continue
        st = cell_str(row.get("status")).lower() or "active"
        if st not in valid_status:
            errors.append({"row": idx, "error": f"invalid status '{st}'"})
            continue

        email = cell_str(row.get("email")) or None
        to_add.append(
            Customer(
                account_no=account_no, name=name, account_type=acc_type, status=st,
                email=email, phone=cell_str(row.get("phone")) or None,
                branch=cell_str(row.get("branch")) or None,
            )
        )
        created += 1

    if not dry_run and to_add:
        db.add_all(to_add)
        await db.commit()
        await record_audit(
            action="create", entity_type="customer", entity_id=f"import:{created}",
            detail=f"Imported {created} customers from '{file.filename}'",
            user=current_user, request=request, db=db,
        )

    return {
        "dry_run": dry_run,
        "total_rows": len(rows),
        "created": 0 if dry_run else created,
        "would_create": created if dry_run else created,
        "skipped_existing": skipped,
        "errors": errors,
    }


@router.post("/facilities", response_model=ImportResult)
async def import_facilities(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Import facilities from an Excel file.

    Columns: account_no (of an existing customer), name, facility_type, amount,
    currency, interest_rate, status. account_no + amount are required.
    """
    content = await _read_upload(file)
    headers, rows = _parse_or_400(content, file.filename)
    _require_columns(headers, ["account_no", "amount"])

    valid_types = {t.value for t in FacilityType}
    valid_status = {s.value for s in FacilityStatus}

    created = 0
    errors = []
    to_add = []

    # Cache account_no -> customer id lookups.
    cust_cache: dict = {}

    for idx, row in enumerate(rows, start=2):
        account_no = cell_str(row.get("account_no"))
        if not account_no:
            errors.append({"row": idx, "error": "account_no is required"})
            continue

        if account_no not in cust_cache:
            cust_cache[account_no] = (
                await db.execute(
                    select(Customer.id).where(
                        Customer.account_no == account_no, Customer.is_deleted == False
                    )
                )
            ).scalar_one_or_none()
        customer_id = cust_cache[account_no]
        if not customer_id:
            errors.append({"row": idx, "error": f"no customer with account_no '{account_no}'"})
            continue

        try:
            amount = _to_decimal(row.get("amount"))
        except ValueError as exc:
            errors.append({"row": idx, "error": f"amount: {exc}"})
            continue
        if amount <= 0:
            errors.append({"row": idx, "error": "amount must be > 0"})
            continue

        ftype = cell_str(row.get("facility_type")).lower() or "loan"
        if ftype not in valid_types:
            errors.append({"row": idx, "error": f"invalid facility_type '{ftype}'"})
            continue
        st = cell_str(row.get("status")).lower() or "active"
        if st not in valid_status:
            errors.append({"row": idx, "error": f"invalid status '{st}'"})
            continue

        rate = None
        if cell_str(row.get("interest_rate")):
            try:
                rate = _to_decimal(row.get("interest_rate"))
            except ValueError as exc:
                errors.append({"row": idx, "error": f"interest_rate: {exc}"})
                continue

        to_add.append(
            Facility(
                customer_id=customer_id, name=cell_str(row.get("name")) or None,
                facility_type=ftype, amount=amount,
                currency=(cell_str(row.get("currency")) or "AED")[:3].upper(),
                interest_rate=rate, status=st, risk_rating="low",
            )
        )
        created += 1

    if not dry_run and to_add:
        db.add_all(to_add)
        await db.commit()
        await record_audit(
            action="create", entity_type="facility", entity_id=f"import:{created}",
            detail=f"Imported {created} facilities from '{file.filename}'",
            user=current_user, request=request, db=db,
        )

    return {
        "dry_run": dry_run,
        "total_rows": len(rows),
        "created": 0 if dry_run else created,
        "would_create": created,
        "errors": errors,
    }


# ===========================================================================
# AI document import — upload a PDF / image / Word file, let a chosen (or auto)
# model extract it, persist each customer's data (deduped), store the file in
# Google Drive and link it under every customer it belongs to, recording a
# page→document map. Models are wired from Settings (enable/route there).
# ===========================================================================
import json as _json
import mimetypes as _mimetypes
import uuid as _uuid
from datetime import datetime as _dt, date as _date
from typing import Optional

from fastapi import Form

_AI_MAX_BYTES = 25 * 1024 * 1024
_IMAGE_MIMES = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif", "image/tiff", "image/bmp")
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _guess_mime(filename: str, given: str) -> str:
    if given and given != "application/octet-stream":
        return given
    guess, _ = _mimetypes.guess_type(filename or "")
    return guess or "application/octet-stream"


def _doc_title(docs: list, filename: str) -> str:
    types = [d.get("type") for d in (docs or []) if isinstance(d, dict) and d.get("type")]
    if types:
        return ", ".join(list(dict.fromkeys(types))[:4])
    return filename or "Imported document"


@router.get("/ai-models")
async def ai_import_models(db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    """Document/vision-capable models, wired live from Settings (enable/route is
    controlled there; here they are only selectable)."""
    from app.ai import ai_manager
    from app.services import drive_sync

    doc_caps = await ai_manager.capable_models(db, "documents")
    vis_caps = await ai_manager.capable_models(db, "vision")
    doc_ids = {m["id"] for m in doc_caps}
    models = []
    for m in doc_caps:
        models.append({**m, "supports_pdf": True})
    for m in vis_caps:
        if m["id"] not in doc_ids:
            models.append({**m, "supports_pdf": False})
    return {"models": models, "drive_enabled": drive_sync.is_enabled()}


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    model_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Extract a document with AI and persist it across the right customers."""
    from app.ai import inference
    from app.services import doc_ingest, drive_sync
    from app.models.crm import Attachment, CustomerProfile

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > _AI_MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {_AI_MAX_BYTES // (1024*1024)} MB)")
    fname = file.filename or "document"
    mime = _guess_mime(fname, file.content_type or "")
    username = getattr(user, "username", "") or ""

    documents: list = []
    if mime == _DOCX_MIME or fname.lower().endswith(".docx"):
        # Word drafts: use the deterministic parser (no AI needed).
        from app.services.draft_extract import extract_from_docx
        try:
            dx = extract_from_docx(data)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not read the Word file: {exc}")
        o, pf = dx.get("offer", {}), dx.get("profile", {})
        customers = [{
            "account_no": dx.get("account_no"), "account_display": dx.get("account_display"),
            "name": o.get("CompanyName"), "account_type": o.get("AccountType"), "branch": o.get("Branch"),
            "fields": {**pf, "business_type": o.get("BusinessType") or pf.get("business_type")},
            "guarantors": dx.get("guarantors", []),
            "review": {"date_of_review": pf.get("review_date"), "purpose": o.get("Purpose"),
                       "proposed_rating": o.get("Rating"), "credit_application_no": pf.get("credit_application_no"),
                       "proposed_amount": pf.get("proposed_amount"), "proposed_tenor": pf.get("proposed_tenor"),
                       "proposed_rate": pf.get("proposed_rate"), "proposed_facility": pf.get("proposed_facility")},
        }]
        model_name = "Word draft parser"
    elif mime == "application/pdf" or mime in _IMAGE_MIMES:
        res = await inference.complete_multimodal(
            db, doc_ingest.EXTRACTION_PROMPT,
            [{"filename": fname, "mimetype": mime, "data": data}], model_id=model_id)
        if not res.get("ok"):
            err = res.get("error")
            if err == "model_incapable":
                raise HTTPException(status_code=422, detail={
                    "error": "model_incapable", "model": res.get("model"),
                    "message": f"«{res.get('model')}» نمی‌تواند این فایل را بخواند. یکی از مدل‌های پیشنهادی را انتخاب کن:",
                    "suggestions": res.get("suggestions", [])})
            if err == "no_model":
                raise HTTPException(status_code=400, detail="هیچ مدلِ سند/تصویرخوان در تنظیمات فعال نیست.")
            raise HTTPException(status_code=502, detail=f"استخراج با مدل ناموفق بود: {err}")
        parsed = doc_ingest.parse_model_json(res.get("text", ""))
        customers = parsed.get("customers") or []
        documents = parsed.get("documents") or []
        model_name = res.get("model")
        if not customers:
            raise HTTPException(status_code=422, detail="مدل نتوانست داده‌ای استخراج کند. مدلِ قوی‌تری انتخاب کن.")
    else:
        raise HTTPException(status_code=415, detail="فقط PDF، تصویر یا Word (.docx) پشتیبانی می‌شود.")

    # Persist each customer (deduped).
    results = []
    for c in customers:
        try:
            results.append(await doc_ingest.persist_customer(db, c, username))
        except Exception as exc:  # never let one bad record break the batch
            results.append({"ok": False, "reason": str(exc)})
    saved = [r for r in results if r.get("ok")]

    # Store the file once in Drive, then link it under every customer.
    primary = saved[0]["account_no"] if saved else "unknown"
    drive = await drive_sync.sync_attachment(account_no=primary, facility_id="",
                                             original_name=fname, data=data, mimetype=mime)
    drive_id = drive_link = drive_name = ""
    if drive.get("ok"):
        r = drive.get("result", {})
        drive_id, drive_link, drive_name = r.get("id", ""), r.get("link", ""), r.get("name", "")

    for r in saved:
        acc = r["account_no"]
        my_docs = [d for d in documents if isinstance(d, dict) and (
            not d.get("customer_account") or str(d.get("customer_account")).endswith(acc) or acc in str(d.get("customer_account")))]
        if drive_id:
            exists = (await db.execute(select(Attachment).where(
                Attachment.account_no == acc, Attachment.drive_file_id == drive_id))).scalar_one_or_none()
            if exists is None:
                db.add(Attachment(
                    id=f"ATT-{acc}-{_dt.now().strftime('%Y%m%d%H%M%S')}-{_uuid.uuid4().hex[:3]}",
                    account_no=acc, facility_id="", file_name=drive_name, original_name=fname,
                    drive_file_id=drive_id, file_size=str(len(data)), upload_date=_date.today().isoformat(),
                    uploaded_by=username, is_shared=("true" if len(saved) > 1 else "false"),
                    notes=_json.dumps({"title": _doc_title(my_docs, fname), "link": drive_link,
                                       "source": "ai_import", "pages": my_docs}, ensure_ascii=False)))
        cp = (await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))).scalar_one_or_none()
        if cp is not None:
            try:
                pdata = _json.loads(cp.data_json) if cp.data_json else {}
            except Exception:
                pdata = {}
            doc_ingest.record_documents_on_profile(pdata, my_docs, drive_link, drive_id, fname)
            cp.data_json = _json.dumps(pdata, ensure_ascii=False)

    await db.commit()
    return {
        "ok": True, "model": model_name, "filename": fname,
        "customers": results, "multi_customer": len(saved) > 1, "documents": documents,
        "drive": {"stored": bool(drive_id), "link": drive_link, "id": drive_id,
                  "skipped": drive.get("skipped", False), "reason": drive.get("reason") or drive.get("error")},
    }
