"""Portfolio reporting endpoints (read-only analytics over the whole book)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select, func, and_, cast as sa_cast, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.services.exporters import rows_to_csv, build_pdf, build_xlsx, XLSX_MEDIA_TYPE
from app.utils.security import get_current_user

router = APIRouter(tags=["reports"], dependencies=[Depends(get_current_user)])


def _download(content: bytes, media_type: str, base: str) -> Response:
    ext = {
        "application/pdf": "pdf",
        "text/html": "html",
        "text/csv": "csv",
        XLSX_MEDIA_TYPE: "xlsx",
    }.get(media_type, "bin")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{base}.{ext}"'},
    )


async def _grouped(db: AsyncSession, model, column, *, amount_col=None):
    cols = [column, func.count(model.id)]
    if amount_col is not None:
        cols.append(func.coalesce(func.sum(sa_cast(amount_col, Float)), 0.0))
    rows = (
        await db.execute(
            select(*cols).where(model.is_deleted == False).group_by(column)
        )
    ).all()
    out = []
    for r in rows:
        label = getattr(r[0], "value", r[0])
        out.append({
            "label": str(label) if label is not None else "unknown",
            "count": int(r[1] or 0),
            "amount": float(r[2]) if amount_col is not None and len(r) > 2 else 0.0,
        })
    out.sort(key=lambda x: x["amount"] or x["count"], reverse=True)
    return out


@router.get("/portfolio")
async def portfolio_report(db: AsyncSession = Depends(get_db)):
    """A consolidated portfolio report used by the Reports page."""
    total_customers = (
        await db.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
    ).scalar() or 0
    total_facilities = (
        await db.execute(
            select(func.count(Facility.id)).where(Facility.is_deleted == False)
        )
    ).scalar() or 0
    total_exposure = float(
        (
            await db.execute(
                select(func.coalesce(func.sum(sa_cast(Facility.amount, Float)), 0.0))
                .where(Facility.is_deleted == False)
            )
        ).scalar()
        or 0
    )
    total_outstanding = float(
        (
            await db.execute(
                select(func.coalesce(func.sum(sa_cast(Facility.outstanding, Float)), 0.0))
                .where(Facility.is_deleted == False)
            )
        ).scalar()
        or 0
    )

    by_type = await _grouped(db, Facility, Facility.facility_type, amount_col=Facility.amount)
    by_status = await _grouped(db, Facility, Facility.status, amount_col=Facility.amount)
    by_risk = await _grouped(db, Facility, Facility.risk_rating, amount_col=Facility.amount)
    by_branch = await _grouped(db, Customer, Customer.branch, amount_col=None)
    by_customer_type = await _grouped(db, Customer, Customer.account_type, amount_col=None)

    utilisation = (total_outstanding / total_exposure * 100) if total_exposure else 0.0

    return {
        "summary": {
            "total_customers": total_customers,
            "total_facilities": total_facilities,
            "total_exposure": total_exposure,
            "total_outstanding": total_outstanding,
            "available_headroom": max(0.0, total_exposure - total_outstanding),
            "utilisation_pct": round(utilisation, 1),
            "currency": "AED",
        },
        "facilities_by_type": by_type,
        "facilities_by_status": by_status,
        "facilities_by_risk": by_risk,
        "customers_by_branch": by_branch,
        "customers_by_type": by_customer_type,
    }


@router.get("/top-exposures")
async def top_exposures(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """The largest customer exposures (sum of facility amounts), descending."""
    rows = (
        await db.execute(
            select(
                Customer.id,
                Customer.name,
                Customer.account_no,
                func.coalesce(func.sum(sa_cast(Facility.amount, Float)), 0.0).label("exposure"),
                func.count(Facility.id).label("facilities"),
            )
            .join(Facility, and_(
                Facility.customer_id == Customer.id, Facility.is_deleted == False
            ), isouter=True)
            .where(Customer.is_deleted == False)
            .group_by(Customer.id, Customer.name, Customer.account_no)
            .order_by(func.coalesce(func.sum(sa_cast(Facility.amount, Float)), 0.0).desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "customer_id": r[0],
                "name": r[1],
                "account_no": r[2],
                "exposure": float(r[3] or 0),
                "facilities": int(r[4] or 0),
            }
            for r in rows
        ]
    }


@router.get("/portfolio/export.csv")
async def export_portfolio_csv(db: AsyncSession = Depends(get_db)):
    """Top exposures as CSV (the most useful tabular slice of the portfolio)."""
    data = await top_exposures(db=db, limit=1000)
    headers = ["customer_id", "name", "account_no", "facilities", "exposure"]
    rows = [
        [i["customer_id"], i["name"], i["account_no"], i["facilities"], i["exposure"]]
        for i in data["items"]
    ]
    return _download(rows_to_csv(headers, rows), "text/csv", "portfolio-exposures")


@router.get("/portfolio/export.pdf")
async def export_portfolio_pdf(db: AsyncSession = Depends(get_db)):
    """Full portfolio report as a PDF (summary + breakdowns + top exposures)."""
    report = await portfolio_report(db=db)
    top = await top_exposures(db=db, limit=20)
    s = report["summary"]
    cur = s["currency"]

    def money(n):
        return f"{cur} {float(n or 0):,.0f}"

    meta = {"Currency": cur, "Utilisation": f"{s['utilisation_pct']}%"}
    summary_rows = [
        ["Total Customers", s["total_customers"]],
        ["Total Facilities", s["total_facilities"]],
        ["Total Exposure", money(s["total_exposure"])],
        ["Total Outstanding", money(s["total_outstanding"])],
        ["Available Headroom", money(s["available_headroom"])],
        ["Utilisation", f"{s['utilisation_pct']}%"],
    ]

    def breakdown_rows(items):
        return [[b["label"], b["count"], money(b["amount"])] for b in items]

    sections = [
        ("Summary", ["Metric", "Value"], summary_rows),
        ("Facilities by Type", ["Type", "Count", "Amount"], breakdown_rows(report["facilities_by_type"])),
        ("Facilities by Risk", ["Risk", "Count", "Amount"], breakdown_rows(report["facilities_by_risk"])),
        ("Facilities by Status", ["Status", "Count", "Amount"], breakdown_rows(report["facilities_by_status"])),
        (
            "Top Exposures",
            ["Customer", "Account", "Facilities", "Exposure"],
            [[i["name"], i["account_no"], i["facilities"], money(i["exposure"])] for i in top["items"]],
        ),
    ]
    content, media_type = build_pdf("Portfolio Report", sections, meta)
    return _download(content, media_type, "portfolio-report")


@router.get("/portfolio/export.xlsx")
async def export_portfolio_xlsx(db: AsyncSession = Depends(get_db)):
    """Full portfolio report as a multi-sheet .xlsx workbook."""
    report = await portfolio_report(db=db)
    top = await top_exposures(db=db, limit=1000)
    s = report["summary"]

    summary_rows = [
        ["Total Customers", s["total_customers"]],
        ["Total Facilities", s["total_facilities"]],
        ["Total Exposure", s["total_exposure"]],
        ["Total Outstanding", s["total_outstanding"]],
        ["Available Headroom", s["available_headroom"]],
        ["Utilisation %", s["utilisation_pct"]],
    ]

    def bd(items):
        return [[b["label"], b["count"], b["amount"]] for b in items]

    sections = [
        ("Summary", ["Metric", "Value"], summary_rows),
        ("By Type", ["Type", "Count", "Amount"], bd(report["facilities_by_type"])),
        ("By Risk", ["Risk", "Count", "Amount"], bd(report["facilities_by_risk"])),
        ("By Status", ["Status", "Count", "Amount"], bd(report["facilities_by_status"])),
        ("By Branch", ["Branch", "Count", "Amount"], bd(report["customers_by_branch"])),
        (
            "Top Exposures",
            ["Customer", "Account", "Facilities", "Exposure"],
            [[i["name"], i["account_no"], i["facilities"], i["exposure"]] for i in top["items"]],
        ),
    ]
    return _download(build_xlsx(sections), XLSX_MEDIA_TYPE, "portfolio-report")
