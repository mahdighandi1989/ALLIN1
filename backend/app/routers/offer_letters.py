from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.offer_letter import OfferLetter, OfferCalculation, OfferStatus
from app.schemas.offer_letter import (
    OfferLetterCreate,
    OfferLetterUpdate,
    OfferLetterResponse,
    OfferLetterDetailResponse,
    OfferLetterListResponse,
    OfferCalculationResponse,
)
from app.services.amortization import generate_schedule, schedule_totals
from app.services.exporters import rows_to_csv, build_pdf
from app.utils.security import get_current_user
from app.routers.auth import get_current_active_user, require_editor


def _ext_for(media_type: str) -> str:
    return {"application/pdf": "pdf", "text/html": "html", "text/csv": "csv"}.get(
        media_type, "bin"
    )


def _download_headers(filename: str) -> dict:
    return {"Content-Disposition": f'attachment; filename="{filename}"'}

router = APIRouter(tags=["offer_letters"], dependencies=[Depends(get_current_user)])

_NOT_FOUND = "Offer letter not found"
_CUSTOMER_NOT_FOUND = "Customer not found"


async def _get_offer(offer_id: str, db: AsyncSession) -> OfferLetter:
    result = await db.execute(
        select(OfferLetter).where(
            OfferLetter.id == offer_id, OfferLetter.is_deleted == False
        )
    )
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return offer


async def _ensure_customer(customer_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id, Customer.is_deleted == False
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_CUSTOMER_NOT_FOUND
        )


def _apply_totals(offer: OfferLetter) -> None:
    """Recompute and store the headline repayment figures on the offer."""
    schedule = generate_schedule(
        Decimal(offer.principal_amount),
        Decimal(offer.interest_rate),
        int(offer.tenor_months),
        repayment_type=getattr(offer.repayment_type, "value", offer.repayment_type) or "monthly",
        grace_period_months=int(offer.grace_period_months or 0),
        start=offer.offer_date,
    )
    totals = schedule_totals(schedule)
    offer.monthly_installment = totals["monthly_installment"]
    offer.total_repayment_amount = totals["total_repayment_amount"]


@router.get("/", response_model=OfferLetterListResponse)
async def list_offers(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    customer_id: Optional[str] = Query(None),
    status_filter: Optional[OfferStatus] = Query(None, alias="status"),
):
    base = select(OfferLetter).where(OfferLetter.is_deleted == False)
    if customer_id:
        base = base.where(OfferLetter.customer_id == customer_id)
    if status_filter:
        base = base.where(OfferLetter.status == status_filter)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0
    rows = (
        await db.execute(
            base.order_by(OfferLetter.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return OfferLetterListResponse(
        items=rows, total=total, page=page, page_size=page_size
    )


@router.get("/{offer_id}", response_model=OfferLetterDetailResponse)
async def get_offer(offer_id: str, db: AsyncSession = Depends(get_db)):
    offer = await _get_offer(offer_id, db)

    # Customer name (best-effort).
    cust = (
        await db.execute(select(Customer.name).where(Customer.id == offer.customer_id))
    ).scalar_one_or_none()

    # Prefer a stored schedule; otherwise compute it on the fly.
    stored = (
        await db.execute(
            select(OfferCalculation)
            .where(OfferCalculation.offer_letter_id == offer.id)
            .order_by(OfferCalculation.installment_number.asc())
        )
    ).scalars().all()

    if stored:
        schedule = [
            OfferCalculationResponse(
                installment_number=c.installment_number,
                payment_date=c.payment_date,
                opening_balance=float(c.opening_balance or 0),
                principal_payment=float(c.principal_payment or 0),
                interest_payment=float(c.interest_payment or 0),
                total_payment=float(c.total_payment or 0),
                closing_balance=float(c.closing_balance or 0),
            )
            for c in stored
        ]
    else:
        schedule = [
            OfferCalculationResponse(
                installment_number=i.installment_number,
                payment_date=i.payment_date,
                opening_balance=float(i.opening_balance),
                principal_payment=float(i.principal_payment),
                interest_payment=float(i.interest_payment),
                total_payment=float(i.total_payment),
                closing_balance=float(i.closing_balance),
            )
            for i in generate_schedule(
                Decimal(offer.principal_amount),
                Decimal(offer.interest_rate),
                int(offer.tenor_months),
                repayment_type=getattr(offer.repayment_type, "value", offer.repayment_type)
                or "monthly",
                grace_period_months=int(offer.grace_period_months or 0),
                start=offer.offer_date,
            )
        ]

    detail = OfferLetterDetailResponse.model_validate(offer)
    detail.customer_name = cust
    detail.schedule = schedule
    return detail


@router.post("/", response_model=OfferLetterResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: OfferLetterCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    await _ensure_customer(payload.customer_id, db)

    offer = OfferLetter(**payload.model_dump(exclude_none=True))
    _apply_totals(offer)
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    from app.services.audit import record_audit
    from app.services.notify_inapp import create_notification
    acc = (
        await db.execute(select(Customer.account_no).where(Customer.id == offer.customer_id))
    ).scalar_one_or_none()
    await record_audit(
        action="create", entity_type="offer_letter", entity_id=offer.id, account_no=acc,
        detail=f"Created offer letter {offer.id}", user=current_user, request=request, db=db,
    )
    await create_notification(
        title="New offer letter created",
        message=f"Offer {offer.id} for {offer.currency} {float(offer.principal_amount):,.0f}",
        level="success", link="/offer-letters", category="offer_letter", db=db,
    )
    try:
        from app.services.telegram import telegram_service

        await telegram_service.notify_event(
            "offer_letter_created",
            f"📝 نامهٔ پیشنهاد جدید *{offer.id}* — "
            f"{offer.currency} {float(offer.principal_amount):,.0f}",
            priority="medium",
        )
    except Exception:  # best-effort; never block the request on a notify failure
        pass
    return offer


@router.put("/{offer_id}", response_model=OfferLetterResponse)
async def update_offer(
    offer_id: str,
    payload: OfferLetterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    offer = await _get_offer(offer_id, db)
    data = payload.model_dump(exclude_unset=True)
    if data.get("customer_id"):
        await _ensure_customer(data["customer_id"], db)
    for field, value in data.items():
        setattr(offer, field, value)
    _apply_totals(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.post("/{offer_id}/generate-schedule", response_model=OfferLetterDetailResponse)
async def generate_offer_schedule(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """(Re)generate and persist the amortisation schedule for an offer."""
    offer = await _get_offer(offer_id, db)

    installments = generate_schedule(
        Decimal(offer.principal_amount),
        Decimal(offer.interest_rate),
        int(offer.tenor_months),
        repayment_type=getattr(offer.repayment_type, "value", offer.repayment_type) or "monthly",
        grace_period_months=int(offer.grace_period_months or 0),
        start=offer.offer_date,
    )

    # Replace any previously-stored schedule.
    await db.execute(
        delete(OfferCalculation).where(OfferCalculation.offer_letter_id == offer.id)
    )
    cum_principal = Decimal("0")
    cum_interest = Decimal("0")
    for inst in installments:
        cum_principal += inst.principal_payment
        cum_interest += inst.interest_payment
        db.add(
            OfferCalculation(
                offer_letter_id=offer.id,
                installment_number=inst.installment_number,
                payment_date=inst.payment_date,
                opening_balance=inst.opening_balance,
                principal_payment=inst.principal_payment,
                interest_payment=inst.interest_payment,
                total_payment=inst.total_payment,
                closing_balance=inst.closing_balance,
                cumulative_principal=cum_principal,
                cumulative_interest=cum_interest,
            )
        )
    _apply_totals(offer)
    await db.commit()
    return await get_offer(offer_id, db)


@router.post("/{offer_id}/status", response_model=OfferLetterResponse)
async def set_offer_status(
    offer_id: str,
    request: Request,
    new_status: OfferStatus = Query(..., description="New offer status"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    offer = await _get_offer(offer_id, db)
    old_status = getattr(offer.status, "value", offer.status)
    offer.status = new_status
    await db.commit()
    await db.refresh(offer)
    from app.services.audit import record_audit

    await record_audit(
        action="update", entity_type="offer_letter", entity_id=offer.id,
        detail=f"Status changed {old_status} -> {new_status.value}",
        user=current_user, request=request, db=db,
    )
    return offer


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    offer = await _get_offer(offer_id, db)
    offer.is_deleted = True
    await db.commit()
    from app.services.audit import record_audit

    await record_audit(
        action="delete", entity_type="offer_letter", entity_id=offer.id,
        detail=f"Deleted offer letter {offer.id}",
        user=current_user, request=request, db=db,
    )
    return None


@router.post("/{offer_id}/restore", response_model=OfferLetterResponse)
async def restore_offer(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Restore a soft-deleted offer letter."""
    result = await db.execute(
        select(OfferLetter).where(
            OfferLetter.id == offer_id, OfferLetter.is_deleted == True
        )
    )
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    offer.is_deleted = False
    await db.commit()
    await db.refresh(offer)
    return offer


def _offer_schedule_rows(offer: OfferLetter):
    """Compute the amortisation schedule for an offer as plain rows."""
    return generate_schedule(
        Decimal(offer.principal_amount),
        Decimal(offer.interest_rate),
        int(offer.tenor_months),
        repayment_type=getattr(offer.repayment_type, "value", offer.repayment_type) or "monthly",
        grace_period_months=int(offer.grace_period_months or 0),
        start=offer.offer_date,
    )


async def _offer_export_payload(offer: OfferLetter, db: AsyncSession):
    """Build (title, meta, sections) describing an offer letter for export."""
    customer_name = (
        await db.execute(select(Customer.name).where(Customer.id == offer.customer_id))
    ).scalar_one_or_none()
    cur = offer.currency or "AED"
    meta = {
        "Offer ID": offer.id,
        "Customer": customer_name or offer.customer_id,
        "Status": getattr(offer.status, "value", offer.status),
        "Offer Date": offer.offer_date,
        "Expiry": offer.expiry_date,
    }
    terms_rows = [
        ["Principal", f"{cur} {float(offer.principal_amount):,.2f}"],
        ["Interest Rate", f"{float(offer.interest_rate)}%"],
        ["Tenor (months)", offer.tenor_months],
        ["Grace (months)", offer.grace_period_months or 0],
        ["Repayment", getattr(offer.repayment_type, "value", offer.repayment_type)],
        ["Monthly Installment", f"{cur} {float(offer.monthly_installment or 0):,.2f}"],
        ["Total Repayment", f"{cur} {float(offer.total_repayment_amount or 0):,.2f}"],
        ["Purpose", offer.purpose_of_facility or "-"],
    ]
    schedule = _offer_schedule_rows(offer)
    sched_rows = [
        [
            i.installment_number,
            i.payment_date,
            f"{float(i.opening_balance):,.2f}",
            f"{float(i.principal_payment):,.2f}",
            f"{float(i.interest_payment):,.2f}",
            f"{float(i.total_payment):,.2f}",
            f"{float(i.closing_balance):,.2f}",
        ]
        for i in schedule
    ]
    sections = [
        ("Offer Terms", ["Field", "Value"], terms_rows),
        (
            "Repayment Schedule",
            ["#", "Date", "Opening", "Principal", "Interest", "Payment", "Closing"],
            sched_rows,
        ),
    ]
    return "Offer Letter", meta, sections


@router.get("/{offer_id}/export.csv")
async def export_offer_csv(offer_id: str, db: AsyncSession = Depends(get_db)):
    """Download the offer's repayment schedule as CSV."""
    offer = await _get_offer(offer_id, db)
    schedule = _offer_schedule_rows(offer)
    headers = ["installment", "payment_date", "opening_balance", "principal",
               "interest", "total_payment", "closing_balance"]
    rows = [
        [i.installment_number, i.payment_date, float(i.opening_balance),
         float(i.principal_payment), float(i.interest_payment),
         float(i.total_payment), float(i.closing_balance)]
        for i in schedule
    ]
    content = rows_to_csv(headers, rows)
    return Response(
        content=content,
        media_type="text/csv",
        headers=_download_headers(f"offer-{offer.id}.csv"),
    )


@router.get("/{offer_id}/export.pdf")
async def export_offer_pdf(offer_id: str, db: AsyncSession = Depends(get_db)):
    """Download the offer letter (terms + schedule) as a PDF document."""
    offer = await _get_offer(offer_id, db)
    title, meta, sections = await _offer_export_payload(offer, db)
    content, media_type = build_pdf(title, sections, meta)
    return Response(
        content=content,
        media_type=media_type,
        headers=_download_headers(f"offer-{offer.id}.{_ext_for(media_type)}"),
    )
