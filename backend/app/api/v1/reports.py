"""
Reports & Backup API
API گزارشات و پشتیبان‌گیری
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json
import io

from app.core.security import get_current_user, TokenData, require_role
from app.core.database import get_db
from app.models.customer import Customer, CustomerStatus
from app.models.facility import Facility, FacilityStatus, FacilityType
from app.services.google_drive import drive_service

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard summary data"""
    # Customers
    total_customers = (await db.execute(
        select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
    )).scalar() or 0

    active_customers = (await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.is_deleted == False,
            Customer.status == CustomerStatus.ACTIVE
        )
    )).scalar() or 0

    # Facilities
    total_facilities = (await db.execute(
        select(func.count()).select_from(Facility).where(Facility.is_deleted == False)
    )).scalar() or 0

    total_exposure = (await db.execute(
        select(func.sum(Facility.approved_amount)).where(Facility.is_deleted == False)
    )).scalar() or 0

    # Expiring facilities (next 30 days)
    expiring = (await db.execute(
        select(func.count()).select_from(Facility).where(
            Facility.is_deleted == False,
            Facility.expiry_date <= datetime.now().date() + timedelta(days=30),
            Facility.expiry_date >= datetime.now().date()
        )
    )).scalar() or 0

    # Recent customers
    recent = await db.execute(
        select(Customer)
        .where(Customer.is_deleted == False)
        .order_by(Customer.created_at.desc())
        .limit(5)
    )
    recent_customers = [
        {"id": c.id, "name": c.customer_name, "account_no": c.account_no}
        for c in recent.scalars()
    ]

    return {
        "customers": {
            "total": total_customers,
            "active": active_customers
        },
        "facilities": {
            "total": total_facilities,
            "total_exposure": float(total_exposure),
            "expiring_soon": expiring
        },
        "recent_customers": recent_customers
    }


@router.get("/customers")
async def generate_customers_report(
    format: str = Query("json", enum=["json", "csv"]),
    status: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate customers report"""
    query = select(Customer).where(Customer.is_deleted == False)
    if status:
        try:
            query = query.where(Customer.status == CustomerStatus(status))
        except ValueError:
            pass

    result = await db.execute(query)
    customers = result.scalars().all()

    data = [
        {
            "account_no": c.account_no,
            "customer_name": c.customer_name,
            "branch": c.branch,
            "account_type": c.account_type.value if hasattr(c.account_type, 'value') else str(c.account_type),
            "status": c.status.value if hasattr(c.status, 'value') else str(c.status),
            "email": c.email,
            "phone": c.phone
        }
        for c in customers
    ]

    if format == "csv":
        import pandas as pd
        df = pd.DataFrame(data)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=customers.csv"}
        )

    return {"data": data, "total": len(data)}


@router.get("/facilities")
async def generate_facilities_report(
    format: str = Query("json", enum=["json", "csv"]),
    facility_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate facilities report"""
    query = select(Facility).where(Facility.is_deleted == False)
    if facility_type:
        try:
            query = query.where(Facility.facility_type == FacilityType(facility_type))
        except ValueError:
            pass

    result = await db.execute(query)
    facilities = result.scalars().all()

    # Get customer names
    customer_ids = list(set(f.customer_id for f in facilities))
    customer_names = {}
    if customer_ids:
        customers = await db.execute(
            select(Customer).where(Customer.id.in_(customer_ids))
        )
        for c in customers.scalars():
            customer_names[c.id] = c.customer_name

    data = [
        {
            "customer_name": customer_names.get(f.customer_id, ""),
            "facility_type": f.facility_type.value if hasattr(f.facility_type, 'value') else str(f.facility_type),
            "approved_amount": float(f.approved_amount) if f.approved_amount else 0,
            "outstanding": float(f.outstanding_amount) if f.outstanding_amount else 0,
            "currency": f.currency,
            "expiry_date": f.expiry_date.isoformat() if f.expiry_date else None,
            "status": f.status.value if hasattr(f.status, 'value') else str(f.status)
        }
        for f in facilities
    ]

    if format == "csv":
        import pandas as pd
        df = pd.DataFrame(data)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=facilities.csv"}
        )

    return {"data": data, "total": len(data)}


@router.get("/expiring")
async def get_expiring_report(
    days: int = Query(30, ge=1, le=365),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expiring facilities report"""
    cutoff = datetime.now().date() + timedelta(days=days)

    result = await db.execute(
        select(Facility).where(
            Facility.is_deleted == False,
            Facility.expiry_date <= cutoff,
            Facility.expiry_date >= datetime.now().date(),
            Facility.status == FacilityStatus.ACTIVE
        ).order_by(Facility.expiry_date)
    )
    facilities = result.scalars().all()

    # Get customer names
    customer_ids = list(set(f.customer_id for f in facilities))
    customer_names = {}
    if customer_ids:
        customers = await db.execute(
            select(Customer).where(Customer.id.in_(customer_ids))
        )
        for c in customers.scalars():
            customer_names[c.id] = c.customer_name

    return {
        "items": [
            {
                "id": f.id,
                "customer_id": f.customer_id,
                "customer_name": customer_names.get(f.customer_id, ""),
                "facility_type": f.facility_type.value if hasattr(f.facility_type, 'value') else str(f.facility_type),
                "amount": float(f.approved_amount) if f.approved_amount else 0,
                "expiry_date": f.expiry_date.isoformat() if f.expiry_date else None,
                "days_until_expiry": (f.expiry_date - datetime.now().date()).days if f.expiry_date else None
            }
            for f in facilities
        ],
        "total": len(facilities)
    }


@router.post("/backup")
async def create_backup(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """Create database backup"""
    # Check Google Drive status
    status = drive_service.get_status()
    if not status.get("connected"):
        raise HTTPException(
            status_code=503,
            detail="Google Drive not connected. Configure credentials first."
        )

    if not drive_service.folder_id:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_DRIVE_FOLDER_ID not configured."
        )

    try:
        backup_data = {
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.user_id,
            "type": "full_backup"
        }

        result = await drive_service.backup_database(backup_data)
        return {"success": True, "backup": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/backup/status")
async def get_backup_status(current_user: TokenData = Depends(require_role(["admin"]))):
    """Get backup service status"""
    status = drive_service.get_status()
    return {
        "google_drive_connected": status.get("connected", False),
        "folder_configured": bool(drive_service.folder_id),
        "last_backup": None  # TODO: Track last backup
    }
