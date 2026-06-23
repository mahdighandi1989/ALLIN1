"""Excel/CSV import endpoints. Wired at /api/imports."""
import logging
from decimal import Decimal, InvalidOperation
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, status
from pydantic import BaseModel
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.import_job import ImportJob  # noqa: F401  (register import_jobs table)
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
from contextlib import asynccontextmanager as _asynccontextmanager
from datetime import datetime as _dt, date as _date
from typing import Optional

from fastapi import Form

# PDFs/images are sent to the model inline → bounded by the provider's request
# limit (Anthropic PDF max is 32 MB). Locally-parsed files (Word/Excel/CSV) never
# go base64 to the model, so they can be much larger.
_AI_MAX_BYTES = 32 * 1024 * 1024
_PDF_MAX_BYTES = 64 * 1024 * 1024   # PDFs over the inline limit are split server-side
_DOC_MAX_BYTES = 60 * 1024 * 1024
# Memory budget: the API runs on a small (512 MB) instance, so a big PDF is split
# into SMALL page-chunks and the chunks are extracted ONE AT A TIME (each base64
# payload freed before the next). Sending several big chunks at once is what
# blew the 512 MB limit and got the instance OOM-killed mid-import.
_PDF_SPLIT_BYTES = 5 * 1024 * 1024   # split any PDF bigger than this
_PDF_CHUNK_BYTES = 5 * 1024 * 1024   # peak-memory lever: each chunk's bytes are bounded here
_PDF_CHUNK_PAGES = 12                 # page cap per chunk (bytes cap usually bites first)
_IMAGE_MIMES = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif", "image/tiff", "image/bmp")
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_EXCEL_EXT = (".xlsx", ".xlsm", ".xls", ".csv")


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


async def _match_facility(db: AsyncSession, customer_id, hint: str) -> str:
    """Best-effort: map a proposed-facility hint to one of the customer's existing
    facilities, so the imported file is filed under the right facility."""
    if not customer_id or not (hint or "").strip():
        return ""
    from app.models.facility import Facility
    facs = (await db.execute(
        select(Facility).where(Facility.customer_id == customer_id, Facility.is_deleted == False))  # noqa: E712
    ).scalars().all()
    if not facs:
        return ""
    h = str(hint).lower()
    want = None
    if "overdraft" in h:
        want = "overdraft"
    elif "loan" in h:
        want = "loan"
    elif "guarantee" in h or "\blg\b" in h or "log" in h:
        want = "lg"
    elif "lc" in h or ("letter" in h and "credit" in h):
        want = "lc"
    for f in facs:
        ft = str(getattr(f.facility_type, "value", f.facility_type) or "").lower()
        if want and want in ft:
            return f.id
        if f.name and h in str(f.name).lower():
            return f.id
    return ""


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


async def _process_document(db: AsyncSession, data: bytes, fname: str, mime: str,
                            model_id, username: str) -> dict:
    """Extract one uploaded document and persist it across the right customers.
    Runs inside a background job so the browser never waits on a multi-minute call."""
    from app.ai import inference
    from app.services import doc_ingest, drive_sync
    from app.models.crm import Attachment, CustomerProfile

    lower = fname.lower()
    is_pdf = mime == "application/pdf" or lower.endswith(".pdf")

    documents: list = []
    chunk_errors: list = []
    if lower.endswith(_EXCEL_EXT) or mime in ("text/csv",):
        # Office/Excel/CSV tables: parse locally to text and let the model extract
        # every row/account (chunked for big tables), routing each to its customer.
        from app.services import doc_ingest as _di
        try:
            table_text = _di.workbook_to_text(data, fname)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"جدول قابلِ خواندن نبود: {exc}")
        if not (table_text or "").strip():
            raise HTTPException(status_code=422, detail="جدول خالی است.")
        chunks = _di.chunk_text(table_text, 100000)
        merged: dict = {}
        model_name = None
        for ci, ch in enumerate(chunks):
            prompt = (_di.EXTRACTION_PROMPT +
                      f"\n\nThe content below is a SPREADSHEET/TABLE (part {ci+1} of {len(chunks)}). "
                      "Each row is usually ONE account/customer; extract EVERY row and attribute it "
                      "to the correct account. There are no page images — ignore the 'documents' array.\n\n"
                      "TABLE CONTENT:\n" + ch)
            res = await inference.complete(db, prompt, task="document_extraction", model_id=model_id, max_tokens=8000)
            if not res.get("ok"):
                if res.get("error") == "no_model":
                    raise HTTPException(status_code=400, detail="هیچ مدلی در تنظیمات فعال نیست.")
                raise HTTPException(status_code=502, detail=f"استخراج با مدل ناموفق بود: {res.get('error')}")
            model_name = res.get("model")
            for c in (doc_ingest.parse_model_json(res.get("text", "")).get("customers") or []):
                acc = doc_ingest._acc_of(c)
                if not acc:
                    continue
                if acc in merged:
                    doc_ingest.merge_customer(merged[acc], c)
                else:
                    merged[acc] = c
        customers = list(merged.values())
        if not customers:
            raise HTTPException(status_code=422, detail="هیچ حساب/مشتری از جدول استخراج نشد.")
    elif mime == _DOCX_MIME or lower.endswith(".docx"):
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
    elif is_pdf or mime in _IMAGE_MIMES:
        # Big PDFs are split into SMALL page-chunks and extracted ONE AT A TIME so
        # peak memory stays well under the instance limit (sending several big
        # base64 payloads at once — or even holding the whole list of chunks —
        # previously OOM-killed the worker mid-import). Chunks are STREAMED from a
        # generator so the full set is never in memory at once.
        if is_pdf and len(data) > _PDF_SPLIT_BYTES:
            try:
                chunk_iter = doc_ingest.pdf_chunks(data, max_bytes=_PDF_CHUNK_BYTES, max_pages=_PDF_CHUNK_PAGES)
            except Exception as exc:
                raise HTTPException(status_code=413, detail=f"فایلِ بزرگ قابلِ تقسیم نبود: {exc}")
        else:
            chunk_iter = iter([(0, data)])
        # Resolve the model ONCE (DB), then send the chunks (no DB).
        rr = await inference.resolve_multimodal(db, [{"mimetype": mime}], model_id=model_id)
        if not rr.get("ok"):
            err = rr.get("error")
            if err == "model_incapable":
                raise HTTPException(status_code=422, detail={
                    "error": "model_incapable", "model": rr.get("model"),
                    "message": f"«{rr.get('model')}» نمی‌تواند این فایل را بخواند. یکی از مدل‌های پیشنهادی را انتخاب کن:",
                    "suggestions": rr.get("suggestions", [])})
            if err == "no_model":
                raise HTTPException(status_code=400, detail="هیچ مدلِ سند/تصویرخوان در تنظیمات فعال نیست.")
            raise HTTPException(status_code=502, detail=f"استخراج با مدل ناموفق بود: {err}")
        resolved = rr["resolved"]
        model_name = resolved.display_name
        import asyncio

        merged: dict = {}
        errs: list = []
        for start, pbytes in chunk_iter:
            res = await inference.send_multimodal(
                resolved, doc_ingest.EXTRACTION_PROMPT,
                [{"filename": fname, "mimetype": mime, "data": pbytes}], max_tokens=8000)
            if not res.get("ok") and "429" in str(res.get("error", "")):
                await asyncio.sleep(3)  # single backoff retry on rate-limit
                res = await inference.send_multimodal(
                    resolved, doc_ingest.EXTRACTION_PROMPT,
                    [{"filename": fname, "mimetype": mime, "data": pbytes}], max_tokens=8000)
            pbytes = None  # free this chunk's bytes before the next one
            if not res.get("ok"):
                errs.append(res.get("error"))
                continue
            parsed = doc_ingest.parse_model_json(res.get("text", ""))
            off = (start - 1) if start else 0
            for c in (parsed.get("customers") or []):
                a = doc_ingest._acc_of(c)
                if not a:
                    continue
                if a in merged:
                    doc_ingest.merge_customer(merged[a], c)
                else:
                    merged[a] = c
            for d in (parsed.get("documents") or []):
                if isinstance(d, dict):
                    if off:
                        d["pages"] = doc_ingest.offset_pages(d.get("pages", ""), off)
                    documents.append(d)
        customers = list(merged.values())
        if not customers:
            raise HTTPException(status_code=502, detail=f"استخراج ناموفق بود: {errs[0] if errs else 'داده‌ای یافت نشد'}")
        chunk_errors = errs  # surfaced in the response so partial failures are visible
    else:
        raise HTTPException(status_code=415, detail="فقط PDF، تصویر یا Word (.docx) پشتیبانی می‌شود.")

    # Persist each customer (deduped). Each runs in its OWN savepoint so a single
    # bad record (e.g. a value that overflows a column) rolls back just that
    # customer instead of poisoning the whole transaction and failing the import.
    results = []
    for c in customers:
        try:
            async with db.begin_nested():
                r = await doc_ingest.persist_customer(db, c, username)
            results.append(r)
        except Exception as exc:  # never let one bad record break the batch
            results.append({"ok": False, "reason": str(exc)})
    saved = [r for r in results if r.get("ok")]

    # Content hash → re-uploading the SAME file reuses the existing Drive copy
    # instead of creating a duplicate.
    import hashlib
    sha = hashlib.sha256(data).hexdigest()
    prior = (await db.execute(
        select(Attachment).where(Attachment.content_sha256 == sha,
                                 Attachment.drive_file_id != None,  # noqa: E711
                                 Attachment.drive_file_id != ""))
    ).scalars().first()

    drive_id = drive_link = drive_name = ""
    reused = False
    if prior is not None:
        # Same bytes already in Drive — reuse it (no second upload).
        drive_id = prior.drive_file_id or ""
        drive_name = prior.file_name or fname
        try:
            drive_link = (_json.loads(prior.notes or "{}") or {}).get("link", "") if prior.notes else ""
        except Exception:
            drive_link = ""
        if not drive_link and drive_id:
            drive_link = f"https://drive.google.com/file/d/{drive_id}/view"
        reused = True
    else:
        primary = saved[0]["account_no"] if saved else "unknown"
        drive = await drive_sync.sync_attachment(account_no=primary, facility_id="",
                                                 original_name=fname, data=data, mimetype=mime)
        if drive.get("ok"):
            r = drive.get("result", {})
            drive_id, drive_link, drive_name = r.get("id", ""), r.get("link", ""), r.get("name", "")

    for r in saved:
        acc = r["account_no"]
        my_docs = [d for d in documents if isinstance(d, dict) and (
            not d.get("customer_account") or str(d.get("customer_account")).endswith(acc) or acc in str(d.get("customer_account")))]
        if drive_id:
            notes = _json.dumps({"title": _doc_title(my_docs, fname), "link": drive_link,
                                 "source": "ai_import", "pages": my_docs}, ensure_ascii=False)
            # Dedup the per-customer link by content hash → same file never doubles up.
            exists = (await db.execute(select(Attachment).where(
                Attachment.account_no == acc, Attachment.content_sha256 == sha))).scalar_one_or_none()
            if exists is None:
                fac_id = await _match_facility(db, r.get("customer_id"), r.get("facility_hint"))
                db.add(Attachment(
                    id=f"ATT-{acc}-{_dt.now().strftime('%Y%m%d%H%M%S')}-{_uuid.uuid4().hex[:3]}",
                    account_no=acc, facility_id=fac_id, file_name=drive_name or fname, original_name=fname,
                    drive_file_id=drive_id, content_sha256=sha, file_size=str(len(data)),
                    upload_date=_date.today().isoformat(), uploaded_by=username,
                    is_shared=("true" if len(saved) > 1 else "false"), notes=notes))
            else:
                exists.notes = notes  # refresh page-map/title in place (no new row)
            cp = (await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))).scalar_one_or_none()
            if cp is not None:
                try:
                    pdata = _json.loads(cp.data_json) if cp.data_json else {}
                except Exception:
                    pdata = {}
                doc_ingest.record_documents_on_profile(pdata, my_docs, drive_link, drive_id, fname, sha)
                cp.data_json = _json.dumps(pdata, ensure_ascii=False)

    await db.commit()

    # Log the import under each affected customer's profile (and the global log).
    from types import SimpleNamespace
    actor = SimpleNamespace(username=username, id="")
    for r in saved:
        nfields = r.get("fields_saved")
        await record_audit(
            action="import", entity_type="document", entity_id=r.get("customer_id"),
            account_no=r.get("account_no"),
            detail=f"استخراج از فایل «{fname}»" + (f" — {nfields} فیلد" if nfields else ""),
            user=actor, request=None, db=db,
        )

    return {
        "ok": True, "model": model_name, "filename": fname,
        "customers": results, "multi_customer": len(saved) > 1, "documents": documents,
        "chunk_errors": [e for e in chunk_errors if e],
        "drive": {"stored": bool(drive_id), "link": drive_link, "id": drive_id, "reused": reused},
    }


# ---------------------------------------------------------------------------
# Background jobs — extraction can take minutes (big PDFs split into chunks),
# longer than the HTTP gateway timeout. So /analyze records a job and returns its
# id immediately; the UI polls /jobs/{id} until it's done. State lives in the DB
# (table import_jobs) so a poll is answered correctly even with several API
# workers (the upload and a later poll may hit different workers). The heavy
# extraction itself runs as an in-process task on the worker that took the upload.
# ---------------------------------------------------------------------------
_BG_TASKS: set = set()  # keep strong refs so fire-and-forget tasks aren't GC'd


@_asynccontextmanager
async def _job_session():
    """Yield a DB session for a background import job.

    A job outlives the request that started it (that request's session is closed
    once it returns), so it gets its own fresh session. Overridden in tests to
    reuse the in-memory test session instead of opening a second connection."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


async def _prune_jobs(db: AsyncSession, keep: int = 300) -> None:
    """Best-effort housekeeping: keep the most recent ``keep`` finished jobs."""
    try:
        old = (await db.execute(
            select(ImportJob.id).where(ImportJob.status != "running")
            .order_by(ImportJob.started_at.desc()).offset(keep))).scalars().all()
        if old:
            await db.execute(delete(ImportJob).where(ImportJob.id.in_(old)))
    except Exception:  # pragma: no cover - non-fatal
        pass


async def _create_job(db: AsyncSession, job_id: str, fname: str, username: str) -> None:
    db.add(ImportJob(id=job_id, status="running", filename=fname, username=username))
    await _prune_jobs(db)
    await db.commit()


async def _record_job_error(db: AsyncSession, job_id: str, http_status: int, detail) -> None:
    row = await db.get(ImportJob, job_id)
    if row is not None:
        row.status = "error"
        row.http_status = http_status
        row.detail_json = _json.dumps(detail, ensure_ascii=False)
        row.finished_at = func.now()
    await db.commit()


async def _run_import_job(job_id: str, data: bytes, fname: str, mime: str, model_id, username: str) -> None:
    async with _job_session() as db:
        try:
            result = await _process_document(db, data, fname, mime, model_id, username)
            row = await db.get(ImportJob, job_id)
            if row is not None:
                row.status = "done"
                row.result_json = _json.dumps(result, ensure_ascii=False)
                row.finished_at = func.now()
            await db.commit()
        except HTTPException as he:
            await db.rollback()
            await _record_job_error(db, job_id, he.status_code, he.detail)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("import job %s failed", job_id)
            await db.rollback()
            await _record_job_error(db, job_id, 500, str(exc))


async def _spawn_job(job_id: str, data: bytes, fname: str, mime: str, model_id, username: str) -> None:
    """Fire-and-forget the import job. Overridden in tests to run it inline so the
    poll endpoint is deterministic."""
    import asyncio
    task = asyncio.create_task(_run_import_job(job_id, data, fname, mime, model_id, username))
    _BG_TASKS.add(task)
    task.add_done_callback(_BG_TASKS.discard)


async def fail_orphaned_jobs() -> int:
    """At startup, any import job still 'running' is orphaned: the process that was
    extracting it died on a restart/redeploy, so its task is gone and the row would
    otherwise stay 'running' forever (the browser polling it endlessly). Mark such
    jobs as errored so the poll returns a clear 'please re-upload' instead. Returns
    how many were reconciled."""
    try:
        async with _job_session() as db:
            rows = (await db.execute(select(ImportJob).where(ImportJob.status == "running"))).scalars().all()
            for r in rows:
                r.status = "error"
                r.http_status = 503
                r.detail_json = _json.dumps(
                    "پردازش به‌خاطر ری‌استارتِ سرور نیمه‌کاره ماند؛ لطفاً دوباره فایل را بارگذاری کنید.",
                    ensure_ascii=False)
                r.finished_at = func.now()
            await db.commit()
            return len(rows)
    except Exception:  # pragma: no cover - best-effort startup housekeeping
        return 0


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    model_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Start an extraction job and return its id immediately (poll /jobs/{id})."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    fname = file.filename or "document"
    mime = _guess_mime(fname, file.content_type or "")
    lower = fname.lower()
    is_pdf = mime == "application/pdf" or lower.endswith(".pdf")
    if lower.endswith(".docx") or lower.endswith(_EXCEL_EXT):
        limit = _DOC_MAX_BYTES
    elif is_pdf:
        limit = _PDF_MAX_BYTES
    else:
        limit = _AI_MAX_BYTES
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"حجم فایل زیاد است (حداکثر {limit // (1024*1024)} MB برای این نوع)")

    username = getattr(user, "username", "") or ""
    job_id = _uuid.uuid4().hex[:12]
    await _create_job(db, job_id, fname, username)
    await _spawn_job(job_id, data, fname, mime, model_id, username)
    return {"job_id": job_id, "status": "running", "filename": fname}


@router.get("/jobs/{job_id}")
async def import_job_status(job_id: str, db: AsyncSession = Depends(get_db),
                            user=Depends(get_current_active_user)):
    """Poll an import job: {status: running|done|error, result?|detail?}."""
    row = await db.get(ImportJob, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found (it may have expired). Please re-upload.")
    out: dict = {"job_id": row.id, "status": row.status, "filename": row.filename}
    if row.status == "done" and row.result_json:
        try:
            out["result"] = _json.loads(row.result_json)
        except Exception:
            out["result"] = None
    elif row.status == "error":
        out["http_status"] = row.http_status
        if row.detail_json:
            try:
                out["detail"] = _json.loads(row.detail_json)
            except Exception:
                out["detail"] = row.detail_json
    return out
