"""
Auto Data Importer Service
سرویس واردکردن خودکار داده‌ها از فایل‌های اکسل
Runs automatically on application startup
"""
import os
import re
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
import structlog

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.base import generate_uuid, generate_short_id
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.journal import JournalEntry
from app.models.task import CustomTask, TaskStatus, TaskPriority
from app.models.security import Security, SecurityCategory, SecurityStatus

logger = structlog.get_logger()


def get_data_import_path() -> Path:
    """Get the data-import directory path"""
    this_file = Path(__file__).resolve()
    backend_dir = this_file.parent.parent  # backend/
    project_root = backend_dir.parent  # ALLIN1/ or /opt/render/project/src/

    possible_paths = [
        project_root / "data-import",
        Path("/opt/render/project/src/data-import"),
        Path("/app/data-import"),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return possible_paths[0]


def parse_amount(value) -> float:
    """Convert amount string to float"""
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


async def auto_import_data():
    """
    Auto-import data from Excel files on startup
    Only imports if database is empty (no customers)
    """
    # Create database connection
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check if data already exists
        result = await db.execute(select(func.count(Customer.id)))
        customer_count = result.scalar() or 0

        if customer_count > 0:
            logger.info(f"Database already has {customer_count} customers, skipping import")
            return

        logger.info("Database is empty, starting auto-import...")

        data_dir = get_data_import_path()
        if not data_dir.exists():
            logger.warning(f"Data import directory not found: {data_dir}")
            return

        files = list(data_dir.glob("*.xls*"))
        if not files:
            logger.warning("No Excel files found for import")
            return

        logger.info(f"Found {len(files)} Excel files to import")

        customer_cache: Dict[str, str] = {}  # account_no -> customer_id
        stats = {
            "customers": 0,
            "facilities": 0,
            "properties": 0,
            "guarantors": 0,
            "tasks": 0,
            "securities": 0,
            "journal": 0,
            "errors": []
        }

        try:
            # 1. Import Customers from Backend_Database.xlsm
            backend_file = data_dir / "Backend_Database.xlsm"
            if backend_file.exists():
                logger.info("Importing customers from Backend_Database.xlsm...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Customers")
                    df = df.dropna(how='all')
                    df = df[df['Account No'].notna()]

                    for _, row in df.iterrows():
                        try:
                            account_no = str(int(row.get('Account No', 0)))
                            if not account_no or account_no == '0':
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
                            stats["customers"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Customer row error: {e}")

                    logger.info(f"Imported {stats['customers']} customers")
                except Exception as e:
                    logger.error(f"Error importing customers: {e}")
                    stats["errors"].append(f"Customers: {e}")

                # 2. Import Facilities
                logger.info("Importing facilities...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Facilities")
                    df = df.dropna(how='all')

                    for _, row in df.iterrows():
                        try:
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
                                notes=str(row.get('Notes', '')) if pd.notna(row.get('Notes')) else None,
                            )
                            db.add(facility)
                            stats["facilities"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Facility row error: {e}")

                    logger.info(f"Imported {stats['facilities']} facilities")
                except Exception as e:
                    logger.error(f"Error importing facilities: {e}")
                    stats["errors"].append(f"Facilities: {e}")

                # 3. Import Guarantors
                logger.info("Importing guarantors...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Guarantors")
                    df = df.dropna(how='all')

                    for _, row in df.iterrows():
                        try:
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
                                    bank_name=str(row.get('IssuingBank', '')) if pd.notna(row.get('IssuingBank')) else None,
                                    amount=Decimal(str(parse_amount(str(row.get('ChequeAmount', '0'))))) if row.get('ChequeAmount') else None,
                                    currency="AED",
                                )
                                db.add(cheque)

                            stats["guarantors"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Guarantor row error: {e}")

                    logger.info(f"Imported {stats['guarantors']} guarantors")
                except Exception as e:
                    logger.error(f"Error importing guarantors: {e}")
                    stats["errors"].append(f"Guarantors: {e}")

                # 4. Import CustomTasks
                logger.info("Importing tasks...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="CustomTasks")
                    df = df.dropna(how='all')

                    for _, row in df.iterrows():
                        try:
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
                            stats["tasks"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Task row error: {e}")

                    logger.info(f"Imported {stats['tasks']} tasks")
                except Exception as e:
                    logger.error(f"Error importing tasks: {e}")
                    stats["errors"].append(f"Tasks: {e}")

                # 5. Import Journal
                logger.info("Importing journal entries...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Journal")
                    df = df.dropna(how='all')
                    # Skip header marker row if exists
                    if 'Record ID' in df.columns:
                        df = df[df['Record ID'] != '--- Data Below ---']

                    for _, row in df.iterrows():
                        try:
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
                            stats["journal"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Journal row error: {e}")

                    logger.info(f"Imported {stats['journal']} journal entries")
                except Exception as e:
                    logger.error(f"Error importing journal: {e}")
                    stats["errors"].append(f"Journal: {e}")

            # 6. Import Iran Properties
            iran_file = data_dir / "PROPERTIES - IRAN.xlsx"
            if iran_file.exists():
                logger.info("Importing Iran properties...")
                try:
                    df = pd.read_excel(iran_file, sheet_name="IRAN")
                    df = df.dropna(how='all')
                    count = 0

                    for _, row in df.iterrows():
                        try:
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
                                stats["customers"] += 1

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
                            count += 1
                        except Exception as e:
                            stats["errors"].append(f"Iran property row error: {e}")

                    stats["properties"] += count
                    logger.info(f"Imported {count} Iran properties")
                except Exception as e:
                    logger.error(f"Error importing Iran properties: {e}")
                    stats["errors"].append(f"Iran Properties: {e}")

            # 7. Import UAE Properties
            uae_file = data_dir / "PROPERTIES - UAE.xlsx"
            if uae_file.exists():
                logger.info("Importing UAE properties...")
                try:
                    df = pd.read_excel(uae_file, sheet_name="U.A.E")
                    df = df.dropna(how='all')
                    count = 0

                    for _, row in df.iterrows():
                        try:
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
                                stats["customers"] += 1

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
                            count += 1
                        except Exception as e:
                            stats["errors"].append(f"UAE property row error: {e}")

                    stats["properties"] += count
                    logger.info(f"Imported {count} UAE properties")
                except Exception as e:
                    logger.error(f"Error importing UAE properties: {e}")
                    stats["errors"].append(f"UAE Properties: {e}")

            # 8. Import Securities from yearly files
            security_files = sorted(data_dir.glob("Securities List*.xlsx"))
            for sec_file in security_files:
                logger.info(f"Importing securities from {sec_file.name}...")
                year_match = re.search(r'20\d{2}', sec_file.name)
                year = int(year_match.group()) if year_match else None
                count = 0

                try:
                    xl = pd.ExcelFile(sec_file)

                    for sheet in xl.sheet_names:
                        category = SecurityCategory.RETAIL if 'retail' in sheet.lower() else SecurityCategory.CORPORATE

                        df = pd.read_excel(xl, sheet_name=sheet, header=None)
                        df = df.dropna(how='all')

                        # Find header row
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
                            try:
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
                                count += 1
                            except Exception as e:
                                stats["errors"].append(f"Security row error: {e}")

                    stats["securities"] += count
                    logger.info(f"Imported {count} securities from {sec_file.name}")
                except Exception as e:
                    logger.error(f"Error importing securities from {sec_file.name}: {e}")
                    stats["errors"].append(f"Securities {sec_file.name}: {e}")

            # Commit all changes
            await db.commit()

            total = sum([
                stats['customers'], stats['facilities'], stats['properties'],
                stats['guarantors'], stats['tasks'], stats['securities'], stats['journal']
            ])

            logger.info(
                "Auto-import completed successfully",
                customers=stats['customers'],
                facilities=stats['facilities'],
                properties=stats['properties'],
                guarantors=stats['guarantors'],
                tasks=stats['tasks'],
                securities=stats['securities'],
                journal=stats['journal'],
                total=total,
                errors=len(stats['errors'])
            )

            if stats['errors']:
                logger.warning(f"Import had {len(stats['errors'])} errors", errors=stats['errors'][:10])

        except Exception as e:
            await db.rollback()
            logger.error(f"Auto-import failed: {e}")
            raise

    await engine.dispose()
