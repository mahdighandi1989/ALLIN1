"""
Data Import API Endpoint
اندپوینت API برای وارد کردن داده‌ها از فایل‌های اکسل
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pathlib import Path
from decimal import Decimal
import re
import os

import pandas as pd
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.journal import JournalEntry
from app.models.task import CustomTask, TaskStatus, TaskPriority
from app.models.security import Security, SecurityCategory, SecurityStatus
from app.models.base import generate_uuid, generate_short_id

router = APIRouter()


# Response Models
class ImportStats(BaseModel):
    customers: int = 0
    facilities: int = 0
    properties: int = 0
    guarantors: int = 0
    tasks: int = 0
    securities: int = 0
    journal: int = 0
    total: int = 0
    errors: List[str] = []


class ImportResponse(BaseModel):
    success: bool
    message: str
    stats: ImportStats
    files_processed: List[str] = []


class FileInfo(BaseModel):
    name: str
    size: int
    modified: str


class AvailableFilesResponse(BaseModel):
    files: List[FileInfo]
    directory: str


# Helper functions
def get_data_import_path() -> Path:
    """Get the data-import directory path"""
    # Calculate path relative to this file
    # __file__ = backend/app/api/v1/data_import.py
    # We need to go up to project root and then into data-import
    this_file = Path(__file__).resolve()
    backend_dir = this_file.parent.parent.parent.parent  # backend/
    project_root = backend_dir.parent  # ALLIN1/ or /opt/render/project/src/

    possible_paths = [
        project_root / "data-import",  # Main path
        Path("/opt/render/project/src/data-import"),  # Render explicit path
        Path("/app/data-import"),  # Docker/alternative
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Create default path if none exist
    default_path = possible_paths[0]
    default_path.mkdir(parents=True, exist_ok=True)
    return default_path


def parse_amount(value) -> float:
    """Convert amount to float"""
    if pd.isna(value) or value is None:
        return 0
    value = str(value)
    value = re.sub(r'[^\d.]', '', value.replace(',', '').replace('/-', ''))
    try:
        return float(value) if value else 0
    except:
        return 0


def parse_date(value) -> Optional[date]:
    """Parse date value"""
    if pd.isna(value) or value is None:
        return None
    try:
        if isinstance(value, (datetime, date)):
            return value if isinstance(value, date) else value.date()
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(str(value).split()[0], fmt).date()
            except:
                continue
    except:
        pass
    return None


@router.get("/files", response_model=AvailableFilesResponse)
async def list_available_files(
    current_user: TokenData = Depends(get_current_user)
):
    """List available files for import"""
    data_dir = get_data_import_path()

    files = []
    for f in data_dir.glob("*.xls*"):
        stat = f.stat()
        files.append(FileInfo(
            name=f.name,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
        ))

    return AvailableFilesResponse(
        files=files,
        directory=str(data_dir)
    )


@router.post("/run", response_model=ImportResponse)
async def run_import(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Run the data import process
    وارد کردن داده‌ها از تمام فایل‌های اکسل موجود
    """
    data_dir = get_data_import_path()

    files = list(data_dir.glob("*.xls*"))
    if not files:
        return ImportResponse(
            success=False,
            message="No Excel files found in data-import directory",
            stats=ImportStats()
        )

    stats = ImportStats()
    customer_cache: Dict[str, str] = {}  # account_no -> customer_id
    processed_files: List[str] = []

    try:
        # Process Backend_Database.xlsm first
        backend_file = data_dir / "Backend_Database.xlsm"
        if backend_file.exists():
            processed_files.append(backend_file.name)

            # Import Customers
            try:
                df = pd.read_excel(backend_file, sheet_name="Customers")
                df = df.dropna(how='all')
                df = df[df['Account No'].notna()]

                for _, row in df.iterrows():
                    account_no = str(int(row.get('Account No', 0)))
                    if not account_no or account_no == '0':
                        continue

                    result = await db.execute(
                        select(Customer).where(Customer.account_no == account_no)
                    )
                    existing = result.scalar_one_or_none()
                    if existing:
                        customer_cache[account_no] = existing.id
                        continue

                    category = str(row.get('Category', '')).lower()
                    account_type = AccountType.CORPORATE if 'corporate' in category else AccountType.RETAIL

                    customer = Customer(
                        id=generate_uuid(),
                        account_no=account_no,
                        customer_name=str(row.get('Account Name', '')).strip() or 'Unknown',
                        branch=str(int(row.get('Branch', 0))) if pd.notna(row.get('Branch')) else None,
                        account_type=account_type,
                        status=CustomerStatus.ACTIVE,
                        country="UAE",
                    )
                    db.add(customer)
                    customer_cache[account_no] = customer.id
                    stats.customers += 1
            except Exception as e:
                stats.errors.append(f"Customers: {str(e)}")

            # Import Facilities
            try:
                df = pd.read_excel(backend_file, sheet_name="Facilities")
                df = df.dropna(how='all')

                for _, row in df.iterrows():
                    account_no = str(int(row.get('AccountNo', 0)))
                    customer_id = customer_cache.get(account_no)
                    if not customer_id:
                        continue

                    ftype = str(row.get('FacilityType', '')).lower()
                    if 'overdraft' in ftype or 'od' in ftype:
                        facility_type = FacilityType.OD
                    elif 'personal' in ftype or 'loan' in ftype:
                        facility_type = FacilityType.LOAN
                    elif 'lg' in ftype:
                        facility_type = FacilityType.LG
                    else:
                        facility_type = FacilityType.OTHER

                    amount = parse_amount(str(row.get('Amount', '0')))

                    facility = Facility(
                        id=str(row.get('FacilityID')) or generate_short_id("FAC-"),
                        customer_id=customer_id,
                        facility_type=facility_type,
                        facility_name=str(row.get('FacilityNo', '')) or None,
                        reference_no=str(row.get('FacilityNo', '')) or None,
                        status=FacilityStatus.ACTIVE if row.get('IsActive', 1) == 1 else FacilityStatus.CLOSED,
                        approved_amount=Decimal(str(amount)) if amount else Decimal('0'),
                        currency=str(row.get('Currency', 'AED')),
                        sanction_date=parse_date(row.get('ApprovalDate')),
                        notes=str(row.get('Notes', '')) or None,
                    )
                    db.add(facility)
                    stats.facilities += 1
            except Exception as e:
                stats.errors.append(f"Facilities: {str(e)}")

            # Import Guarantors
            try:
                df = pd.read_excel(backend_file, sheet_name="Guarantors")
                df = df.dropna(how='all')

                for _, row in df.iterrows():
                    account_no = str(int(row.get('AccountNo', 0)))
                    customer_id = customer_cache.get(account_no)
                    if not customer_id:
                        continue

                    guarantor = Guarantor(
                        id=str(row.get('GuarantorID')) or generate_short_id("GNT-"),
                        customer_id=customer_id,
                        guarantor_name=str(row.get('GuarantorName', '')).strip() or 'Unknown',
                        phone=str(row.get('GuarantorAccount', '')) if pd.notna(row.get('GuarantorAccount')) else None,
                    )
                    db.add(guarantor)

                    cheque_no = row.get('ChequeNo')
                    if pd.notna(cheque_no) and str(cheque_no).strip():
                        cheque = GuarantorCheque(
                            id=generate_short_id("CHQ-"),
                            guarantor_id=guarantor.id,
                            cheque_no=str(cheque_no),
                            bank_name=str(row.get('IssuingBank', '')) or None,
                            amount=Decimal(str(parse_amount(str(row.get('ChequeAmount', '0'))))) if row.get('ChequeAmount') else None,
                            currency="AED",
                        )
                        db.add(cheque)

                    stats.guarantors += 1
            except Exception as e:
                stats.errors.append(f"Guarantors: {str(e)}")

            # Import CustomTasks
            try:
                df = pd.read_excel(backend_file, sheet_name="CustomTasks")
                df = df.dropna(how='all')

                for _, row in df.iterrows():
                    account_no = str(int(row.get('AccountNo', 0))) if pd.notna(row.get('AccountNo')) else None
                    customer_id = customer_cache.get(account_no) if account_no else None

                    status_str = str(row.get('Status', '')).lower()
                    if 'complete' in status_str:
                        status = TaskStatus.COMPLETED
                    elif 'progress' in status_str:
                        status = TaskStatus.IN_PROGRESS
                    elif 'cancel' in status_str:
                        status = TaskStatus.CANCELLED
                    else:
                        status = TaskStatus.PENDING

                    priority_str = str(row.get('Priority', '')).lower()
                    if 'high' in priority_str or 'urgent' in priority_str:
                        priority = TaskPriority.HIGH
                    elif 'low' in priority_str:
                        priority = TaskPriority.LOW
                    else:
                        priority = TaskPriority.MEDIUM

                    task = CustomTask(
                        id=generate_short_id("TSK-"),
                        task_id=str(row.get('TaskID', '')) or None,
                        customer_id=customer_id,
                        account_no=account_no,
                        task_name=str(row.get('TaskName', 'Unnamed Task')),
                        status=status,
                        priority=priority,
                        follow_up_date=parse_date(row.get('FollowUpDate')),
                        notes=str(row.get('Notes', '')) if pd.notna(row.get('Notes')) else None,
                        is_active=row.get('IsActive', 1) == 1,
                    )
                    db.add(task)
                    stats.tasks += 1
            except Exception as e:
                stats.errors.append(f"CustomTasks: {str(e)}")

            # Import Journal
            try:
                df = pd.read_excel(backend_file, sheet_name="Journal")
                df = df.dropna(how='all')
                df = df[df['Record ID'] != '--- Data Below ---']

                for _, row in df.iterrows():
                    account_no = str(int(row.get('Account No', 0))) if pd.notna(row.get('Account No')) else None
                    customer_id = customer_cache.get(account_no) if account_no else None

                    entry_date = parse_date(row.get('Date'))
                    timestamp = datetime.now()
                    if entry_date:
                        timestamp = datetime.combine(entry_date, datetime.min.time())

                    entry = JournalEntry(
                        id=generate_short_id("JRN-"),
                        timestamp=timestamp,
                        action_type=str(row.get('Action', 'import')) if pd.notna(row.get('Action')) else 'import',
                        entity_type='customer' if customer_id else 'general',
                        entity_id=customer_id,
                        description=str(row.get('Notes', '')) if pd.notna(row.get('Notes')) else str(row.get('Item', '')),
                        details={
                            "account_no": account_no,
                            "branch": str(row.get('Branch', '')) if pd.notna(row.get('Branch')) else None,
                            "category": str(row.get('Category', '')) if pd.notna(row.get('Category')) else None,
                            "item": str(row.get('Item', '')) if pd.notna(row.get('Item')) else None,
                        }
                    )
                    db.add(entry)
                    stats.journal += 1
            except Exception as e:
                stats.errors.append(f"Journal: {str(e)}")

        # Import Iran Properties
        iran_file = data_dir / "PROPERTIES - IRAN.xlsx"
        if iran_file.exists():
            processed_files.append(iran_file.name)
            try:
                df = pd.read_excel(iran_file, sheet_name="IRAN")
                df = df.dropna(how='all')

                for _, row in df.iterrows():
                    account_no = str(int(row.get('شماره حساب', 0))) if pd.notna(row.get('شماره حساب')) else None
                    customer_id = customer_cache.get(account_no) if account_no else None

                    if not customer_id and account_no:
                        customer = Customer(
                            id=generate_uuid(),
                            account_no=account_no,
                            customer_name=str(row.get('نام مشتری', '')).strip() or 'Unknown',
                            account_type=AccountType.CORPORATE,
                            status=CustomerStatus.ACTIVE,
                            country="IRAN",
                        )
                        db.add(customer)
                        customer_id = customer.id
                        customer_cache[account_no] = customer_id
                        stats.customers += 1

                    if not customer_id:
                        continue

                    prop_type = str(row.get('نوع', '')).lower()
                    if 'آپارتمان' in prop_type:
                        property_type = PropertyType.APARTMENT
                    elif 'ویلا' in prop_type:
                        property_type = PropertyType.VILLA
                    elif 'زمین' in prop_type:
                        property_type = PropertyType.LAND
                    else:
                        property_type = PropertyType.OTHER

                    prop = Property(
                        id=generate_short_id("PRP-"),
                        customer_id=customer_id,
                        location=PropertyLocation.IRAN,
                        property_type=property_type,
                        status=PropertyStatus.MORTGAGED,
                        plate_no=str(row.get('شماره پلاک ثبتی', '')) if pd.notna(row.get('شماره پلاک ثبتی')) else None,
                        city=str(row.get('شهر', '')) if pd.notna(row.get('شهر')) else None,
                        address=str(row.get('نشانی ملک', '')) if pd.notna(row.get('نشانی ملک')) else None,
                        currency="IRR",
                        owner_name=str(row.get('نام مشتری', '')) if pd.notna(row.get('نام مشتری')) else None,
                    )
                    db.add(prop)
                    stats.properties += 1
            except Exception as e:
                stats.errors.append(f"Iran Properties: {str(e)}")

        # Import UAE Properties
        uae_file = data_dir / "PROPERTIES - UAE.xlsx"
        if uae_file.exists():
            processed_files.append(uae_file.name)
            try:
                df = pd.read_excel(uae_file, sheet_name="U.A.E")
                df = df.dropna(how='all')

                for _, row in df.iterrows():
                    account_no = str(int(row.get('AC  No', 0))) if pd.notna(row.get('AC  No')) else None
                    customer_id = customer_cache.get(account_no) if account_no else None

                    if not customer_id and account_no:
                        customer = Customer(
                            id=generate_uuid(),
                            account_no=account_no,
                            customer_name=str(row.get('Name', '')).strip() or 'Unknown',
                            branch=str(int(row.get('Branch', 0))) if pd.notna(row.get('Branch')) else None,
                            account_type=AccountType.CORPORATE,
                            status=CustomerStatus.ACTIVE,
                            country="UAE",
                        )
                        db.add(customer)
                        customer_id = customer.id
                        customer_cache[account_no] = customer_id
                        stats.customers += 1

                    if not customer_id:
                        continue

                    prop_type = str(row.get('TYPE', '')).lower()
                    if 'building' in prop_type:
                        property_type = PropertyType.BUILDING
                    elif 'apartment' in prop_type:
                        property_type = PropertyType.APARTMENT
                    elif 'villa' in prop_type:
                        property_type = PropertyType.VILLA
                    elif 'land' in prop_type:
                        property_type = PropertyType.LAND
                    else:
                        property_type = PropertyType.OTHER

                    value_2025 = parse_amount(str(row.get('AED Value 2025', 0)))

                    prop = Property(
                        id=generate_short_id("PRP-"),
                        customer_id=customer_id,
                        location=PropertyLocation.UAE,
                        property_type=property_type,
                        status=PropertyStatus.MORTGAGED,
                        deed_no=str(row.get('Deed No.', '')) if pd.notna(row.get('Deed No.')) else None,
                        city=str(row.get('City', '')) if pd.notna(row.get('City')) else None,
                        area=str(row.get('Zone', '')) if pd.notna(row.get('Zone')) else None,
                        current_value=Decimal(str(value_2025)) if value_2025 else None,
                        currency="AED",
                        owner_name=str(row.get('Name.1', '')) if pd.notna(row.get('Name.1')) else None,
                    )
                    db.add(prop)
                    stats.properties += 1
            except Exception as e:
                stats.errors.append(f"UAE Properties: {str(e)}")

        # Import Securities
        security_files = sorted(data_dir.glob("Securities List*.xlsx"))
        for sec_file in security_files:
            processed_files.append(sec_file.name)
            year_match = re.search(r'20\d{2}', sec_file.name)
            year = int(year_match.group()) if year_match else None

            try:
                xl = pd.ExcelFile(sec_file)

                for sheet in xl.sheet_names:
                    category = SecurityCategory.RETAIL if 'retail' in sheet.lower() else SecurityCategory.CORPORATE

                    df = pd.read_excel(xl, sheet_name=sheet, header=None)
                    df = df.dropna(how='all')

                    header_row = None
                    for i, row in df.iterrows():
                        row_str = ' '.join(str(x).lower() for x in row.values if pd.notna(x))
                        if 'account' in row_str and ('no' in row_str or '#' in row_str):
                            header_row = i
                            break

                    if header_row is None:
                        continue

                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:]
                    df = df.dropna(how='all')

                    for _, row in df.iterrows():
                        account_no = None
                        for col in df.columns:
                            if 'account' in str(col).lower():
                                account_no = row.get(col)
                                break

                        if pd.isna(account_no):
                            continue

                        account_no = str(int(account_no)) if isinstance(account_no, float) else str(account_no)
                        customer_id = customer_cache.get(account_no)

                        customer_name = None
                        for col in df.columns:
                            if 'customer' in str(col).lower() or 'name' in str(col).lower():
                                customer_name = row.get(col)
                                break

                        branch = None
                        for col in df.columns:
                            if 'branch' in str(col).lower():
                                branch = row.get(col)
                                break

                        security = Security(
                            id=generate_short_id("SEC-"),
                            customer_id=customer_id,
                            account_no=account_no,
                            branch=str(int(branch)) if pd.notna(branch) and isinstance(branch, (int, float)) else str(branch) if pd.notna(branch) else None,
                            customer_name=str(customer_name).strip() if pd.notna(customer_name) else None,
                            category=category,
                            year=year,
                            status=SecurityStatus.ACTIVE,
                            source_file=sec_file.name,
                        )
                        db.add(security)
                        stats.securities += 1
            except Exception as e:
                stats.errors.append(f"Securities {sec_file.name}: {str(e)}")

        await db.commit()

        stats.total = (
            stats.customers + stats.facilities + stats.properties +
            stats.guarantors + stats.tasks + stats.securities + stats.journal
        )

        return ImportResponse(
            success=True,
            message=f"Successfully imported {stats.total} records",
            stats=stats,
            files_processed=processed_files
        )

    except Exception as e:
        await db.rollback()
        stats.errors.append(f"General error: {str(e)}")
        return ImportResponse(
            success=False,
            message=f"Import failed: {str(e)}",
            stats=stats,
            files_processed=processed_files
        )


@router.get("/stats")
async def get_database_stats(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get current database statistics"""
    from sqlalchemy import func

    stats = {}

    # Count each table
    for model, name in [
        (Customer, "customers"),
        (Facility, "facilities"),
        (Property, "properties"),
        (Guarantor, "guarantors"),
        (CustomTask, "tasks"),
        (Security, "securities"),
        (JournalEntry, "journal"),
    ]:
        result = await db.execute(select(func.count(model.id)))
        stats[name] = result.scalar() or 0

    stats["total"] = sum(stats.values())

    return stats


@router.post("/enhance")
async def enhance_existing_data(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Enhance existing data with more information from Excel files
    This adds MORE data without deleting existing records
    تکمیل داده‌های موجود با اطلاعات بیشتر از فایل‌های اکسل
    """
    from app.services.ai_data_processor import enhance_data_from_excel

    data_dir = get_data_import_path()
    backend_file = data_dir / "Backend_Database.xlsm"

    if not backend_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Backend_Database.xlsm not found in data-import directory"
        )

    try:
        stats = await enhance_data_from_excel(db, backend_file)
        return {
            "success": True,
            "message": "Data enhancement completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )
