from sqlalchemy import select, func, and_, cast as sa_cast, Float
from sqlalchemy.orm import load_only
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.schemas.stats import (
    DashboardStatsResponse,
    TotalExposureResponse,
    OtherStatsResponse,
    RecentCustomerResponse,
    RecentActivityResponse,
    BreakdownItem,
    MonthlyTrendItem,
    ExpiringFacilityItem,
)
from app.utils.security import get_current_user

# Authentication is required for every stats endpoint.
router = APIRouter(dependencies=[Depends(get_current_user)])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Return aggregated dashboard statistics.

    Every aggregate query — counts *and* the currency-normalised
    exposure/revenue totals — is individually guarded, so a single broken or
    missing column degrades that value to ``0`` rather than blanking (or
    ``500``-ing) the whole dashboard. The frontend therefore always receives a
    usable payload and the page never gets stuck on an infinite spinner. Only a
    failure outside the guarded blocks surfaces as a clean, internals-free
    ``500`` that the frontend renders as an actionable error with a retry.
    """
    today = datetime.utcnow().date()
    thirty_days_later = today + timedelta(days=30)
    try:
        # Total customers
        try:
            total_customers_result = await db.execute(
                select(func.count(Customer.id)).where(Customer.is_deleted == False)
            )
            total_customers = total_customers_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching total customers: %s", e)
            total_customers = 0

        # Active customers
        try:
            active_customers_result = await db.execute(
                select(func.count(Customer.id)).where(
                    and_(Customer.is_deleted == False, Customer.status == 'active')
                )
            )
            active_customers = active_customers_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching active customers: %s", e)
            active_customers = 0

        # Total facilities
        try:
            total_facilities_result = await db.execute(
                select(func.count(Facility.id)).where(Facility.is_deleted == False)
            )
            total_facilities = total_facilities_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching total facilities: %s", e)
            total_facilities = 0

        # Active facilities
        try:
            active_facilities_result = await db.execute(
                select(func.count(Facility.id)).where(
                    and_(Facility.is_deleted == False, Facility.status == 'active')
                )
            )
            active_facilities = active_facilities_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching active facilities: %s", e)
            active_facilities = 0

        # Facilities expiring soon (within 30 days). Both end_date and the newer
        # expiry_date columns are considered so the count is robust to whichever
        # column a record populated.
        try:
            expiring_soon_result = await db.execute(
                select(func.count(Facility.id)).where(
                    and_(
                        Facility.is_deleted == False,
                        func.coalesce(Facility.expiry_date, Facility.end_date) >= today,
                        func.coalesce(Facility.expiry_date, Facility.end_date)
                        <= thirty_days_later,
                    )
                )
            )
            expiring_soon = expiring_soon_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching expiring soon facilities: %s", e)
            expiring_soon = 0

        # Total exposure / outstanding / monthly-revenue — multi-currency aware.
        # Each facility's amount is converted to the base currency via the
        # exchange-rate table before being summed, so a USD facility and an AED
        # facility aggregate correctly. Computed in Python (portable + avoids the
        # NUMERIC overflow that bit the SQL revenue calc).
        from app.services.fx import load_rates, to_base
        from app.models.exchange_rate import BASE_CURRENCY

        total_exposure_amount = 0.0
        total_outstanding = 0.0
        monthly_revenue = 0.0
        try:
            rates = await load_rates(db)
            fac_rows = (
                await db.execute(
                    select(
                        Facility.amount, Facility.outstanding, Facility.currency,
                        Facility.interest_rate, Facility.status,
                    ).where(Facility.is_deleted == False)
                )
            ).all()
            for amount, outstanding, currency, rate, fstatus in fac_rows:
                amt_base = to_base(amount, currency, rates)
                total_exposure_amount += amt_base
                total_outstanding += to_base(outstanding, currency, rates)
                if getattr(fstatus, "value", fstatus) == "active":
                    monthly_revenue += amt_base * float(rate or 0) / 1200.0
        except Exception as e:
            logger.error("Error computing currency-normalised totals: %s", e)

        # Recent customers (last 5)
        try:
            recent_customers_result = await db.execute(
                select(Customer)
                .options(
                    load_only(
                        Customer.id,
                        Customer.account_no,
                        Customer.name,
                        Customer.status,
                        Customer.created_at,
                    )
                )
                .where(
                    and_(
                        Customer.is_deleted == False,
                        Customer.name.isnot(None),
                        Customer.name != "",
                    )
                )
                .order_by(Customer.created_at.desc())
                .limit(5)
            )
            recent_customers = recent_customers_result.scalars().all()
        except Exception as e:
            logger.error("Error fetching recent customers: %s", e)
            recent_customers = []

        recent_customers_response: List[RecentCustomerResponse] = []
        recent_activities_response: List[RecentActivityResponse] = []
        for index, customer in enumerate(recent_customers):
            try:
                recent_customers_response.append(
                    RecentCustomerResponse(
                        id=str(customer.id),
                        account_no=customer.account_no or "",
                        name=customer.name or "",
                        status=customer.status or "inactive",
                        created_at=customer.created_at,
                    )
                )
                recent_activities_response.append(
                    RecentActivityResponse(
                        id=index + 1,
                        action=f"New customer added: {customer.name or customer.account_no or customer.id}",
                        timestamp=customer.created_at,
                        user="system",
                    )
                )
            except Exception as e:
                logger.error(
                    "Error processing customer %s: %s",
                    getattr(customer, 'id', 'unknown'),
                    e,
                )
                continue

        # --- analytics breakdowns (each guarded; empty list on error) ---------
        facility_type_breakdown = await _breakdown_by(
            db, Facility, Facility.facility_type, with_amount=True
        )
        facility_status_breakdown = await _breakdown_by(
            db, Facility, Facility.status, with_amount=True
        )
        risk_rating_breakdown = await _breakdown_by(
            db, Facility, Facility.risk_rating, with_amount=True
        )
        customer_type_breakdown = await _breakdown_by(
            db, Customer, Customer.account_type, with_amount=False
        )
        monthly_trend = await _monthly_trend(db)
        expiring_list = await _expiring_facilities(db, today, thirty_days_later)

        return DashboardStatsResponse(
            total_customers=total_customers,
            active_customers=active_customers,
            total_facilities=total_facilities,
            active_facilities=active_facilities,
            expiring_soon=expiring_soon,
            expiring_facilities=expiring_soon,
            expiring_soon_facilities=expiring_soon,
            monthly_revenue=monthly_revenue,
            total_outstanding=total_outstanding,
            total_exposure=TotalExposureResponse(
                amount=total_exposure_amount, currency=BASE_CURRENCY
            ),
            # Flat headline amount (mirrors total_exposure.amount).
            total_amount=total_exposure_amount,
            # The remaining scalars grouped for the documented contract.
            other_stats=OtherStatsResponse(
                total_customers=total_customers,
                active_customers=active_customers,
                total_facilities=total_facilities,
                active_facilities=active_facilities,
                expiring_soon=expiring_soon,
                monthly_revenue=monthly_revenue,
                total_outstanding=total_outstanding,
                currency=BASE_CURRENCY,
            ),
            recent_customers=recent_customers_response,
            recent_activities=recent_activities_response,
            facility_type_breakdown=facility_type_breakdown,
            facility_status_breakdown=facility_status_breakdown,
            risk_rating_breakdown=risk_rating_breakdown,
            customer_type_breakdown=customer_type_breakdown,
            monthly_trend=monthly_trend,
            expiring_facilities_list=expiring_list,
        )
    except HTTPException:
        # Preserve explicit HTTP errors (e.g. the monthly-revenue 500) verbatim.
        raise
    except Exception as e:
        # Generic message only — never leak internals to the client (see the
        # log for the full error).
        logger.error("Critical error in dashboard stats endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching dashboard stats")


# ---------------------------------------------------------------------------
# Analytics helpers for the dashboard charts/tables. Each is fully guarded and
# returns an empty list on any error so it can never break the dashboard.
# ---------------------------------------------------------------------------
async def _breakdown_by(db: AsyncSession, model, column, *, with_amount: bool):
    """GROUP BY a column, returning labelled counts (and summed amount)."""
    try:
        cols = [column, func.count(model.id)]
        if with_amount:
            cols.append(func.coalesce(func.sum(sa_cast(model.amount, Float)), 0.0))
        query = (
            select(*cols)
            .where(model.is_deleted == False)
            .group_by(column)
            .order_by(func.count(model.id).desc())
        )
        rows = (await db.execute(query)).all()
        items = []
        for row in rows:
            raw_label = row[0]
            label = getattr(raw_label, "value", raw_label)
            items.append(
                BreakdownItem(
                    label=str(label) if label is not None else "unknown",
                    count=int(row[1] or 0),
                    amount=float(row[2]) if with_amount and len(row) > 2 else 0.0,
                )
            )
        return items
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Error building breakdown for %s: %s", getattr(column, "key", column), e)
        return []


async def _monthly_trend(db: AsyncSession, months: int = 6):
    """Exposure + facility count per month for the last N months.

    Prefers the real ``exposure_snapshots`` time series (actual recorded history);
    if there are no snapshots it falls back to a cumulative view computed from
    each facility's start_date.
    """
    # 1) Real snapshots first.
    try:
        from app.models.exposure_snapshot import ExposureSnapshot

        snaps = (
            await db.execute(
                select(ExposureSnapshot).order_by(
                    ExposureSnapshot.year.desc(), ExposureSnapshot.month.desc()
                ).limit(months)
            )
        ).scalars().all()
        if snaps:
            snaps = list(reversed(snaps))
            return [
                MonthlyTrendItem(
                    month=f"{s.year:04d}-{s.month:02d}",
                    exposure=float(s.total_exposure or 0),
                    facilities=int(s.facility_count or 0),
                )
                for s in snaps
            ]
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Snapshot trend read failed, falling back: %s", e)

    # 2) Fallback: cumulative view from facility start dates.
    try:
        rows = (
            await db.execute(
                select(
                    Facility.start_date,
                    Facility.created_at,
                    sa_cast(Facility.amount, Float),
                ).where(Facility.is_deleted == False)
            )
        ).all()

        # Build the list of the last `months` year-month buckets.
        today = datetime.utcnow().date()
        buckets = []
        y, m = today.year, today.month
        for _ in range(months):
            buckets.append((y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        buckets.reverse()

        result = []
        for (by, bm) in buckets:
            # Everything created on/before the end of this month counts toward
            # the cumulative exposure (a portfolio view).
            exposure = 0.0
            count = 0
            for start_date, created_at, amount in rows:
                ref = start_date or (created_at.date() if created_at else None)
                if ref is None:
                    continue
                if (ref.year, ref.month) <= (by, bm):
                    exposure += float(amount or 0)
                    count += 1
            result.append(
                MonthlyTrendItem(
                    month=f"{by:04d}-{bm:02d}", exposure=exposure, facilities=count
                )
            )
        return result
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Error building monthly trend: %s", e)
        return []


async def _expiring_facilities(db: AsyncSession, today, horizon, limit: int = 10):
    """Facilities expiring between today and `horizon`, soonest first."""
    try:
        expiry = func.coalesce(Facility.expiry_date, Facility.end_date)
        rows = (
            await db.execute(
                select(Facility, Customer.name)
                .join(Customer, Customer.id == Facility.customer_id, isouter=True)
                .where(
                    and_(
                        Facility.is_deleted == False,
                        expiry >= today,
                        expiry <= horizon,
                    )
                )
                .order_by(expiry.asc())
                .limit(limit)
            )
        ).all()
        items = []
        for facility, customer_name in rows:
            exp = facility.expiry_date or facility.end_date
            days = (exp - today).days if exp else None
            items.append(
                ExpiringFacilityItem(
                    id=str(facility.id),
                    name=facility.name,
                    customer_id=str(facility.customer_id) if facility.customer_id else None,
                    customer_name=customer_name,
                    facility_type=getattr(facility.facility_type, "value", facility.facility_type),
                    amount=float(facility.amount or 0),
                    currency=facility.currency or "AED",
                    expiry_date=exp,
                    days_to_expiry=days,
                    status=getattr(facility.status, "value", facility.status),
                )
            )
        return items
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Error building expiring facilities list: %s", e)
        return []


@router.post("/snapshot")
async def capture_snapshot_now(db: AsyncSession = Depends(get_db)):
    """Capture (upsert) this month's exposure snapshot from current data.

    Useful to call from a scheduler (e.g. monthly cron) to build the trend over
    time. Idempotent per calendar month.
    """
    from app.services.snapshots import capture_current_snapshot
    await capture_current_snapshot()
    return {"ok": True}
