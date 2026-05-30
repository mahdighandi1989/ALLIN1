"""Excel/CSV import endpoints. Wired at /api/imports."""
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.services.excel_import import parse_workbook, cell_str, ExcelParseError
from app.services.exporters import rows_to_csv
from app.services.audit import record_audit
from app.routers.auth import get_current_active_user
from fastapi import Response

router = APIRouter(tags=["imports"], dependencies=[Depends(get_current_active_user)])

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


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
    if not name.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Please upload an .xlsx or .xlsm file")
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    return content


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


@router.post("/customers")
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
    try:
        headers, rows = parse_workbook(content)
    except ExcelParseError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid spreadsheet: {exc}")

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


@router.post("/facilities")
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
    try:
        headers, rows = parse_workbook(content)
    except ExcelParseError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid spreadsheet: {exc}")

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
