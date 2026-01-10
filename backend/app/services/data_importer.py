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

# Core models
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.journal import JournalEntry
from app.models.task import CustomTask, TaskStatus, TaskPriority
from app.models.security import Security, SecurityCategory, SecurityStatus
from app.models.note import Note, NoteCategory, NotePriority

# New comprehensive models
from app.models.branch import Branch
from app.models.category import Category
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.partner import Partner
from app.models.property_valuation import PropertyValuation, PropertyInsurance
from app.models.security_record import SecurityRecord, SecurityRecordCategory

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


def clean_str(value) -> Optional[str]:
    """Clean string value"""
    if pd.isna(value) or value is None:
        return None
    val = str(value).strip()
    return val if val and val.lower() not in ['nan', 'none', ''] else None


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

        # Caches for relationships
        customer_cache: Dict[str, str] = {}  # account_no -> customer_id
        branch_cache: Dict[str, str] = {}  # branch_code -> branch_id
        category_cache: Dict[str, str] = {}  # category_name -> category_id
        property_cache: Dict[str, str] = {}  # property key -> property_id

        stats = {
            "branches": 0,
            "categories": 0,
            "customers": 0,
            "profiles": 0,
            "documents": 0,
            "partners": 0,
            "facilities": 0,
            "guarantors": 0,
            "tasks": 0,
            "notes": 0,
            "properties": 0,
            "valuations": 0,
            "securities": 0,
            "journal": 0,
            "errors": []
        }

        try:
            backend_file = data_dir / "Backend_Database.xlsm"

            if backend_file.exists():
                # ==============================================================
                # PHASE 1: Import Branches (extract from customer data)
                # ==============================================================
                logger.info("Phase 1: Extracting branches...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Customers")
                    df = df.dropna(how='all')

                    branches_set = set()
                    for _, row in df.iterrows():
                        branch = row.get('Branch')
                        if pd.notna(branch):
                            branches_set.add(str(int(branch)) if isinstance(branch, float) else str(branch))

                    for branch_code in branches_set:
                        branch = Branch(
                            id=generate_uuid(),
                            branch_code=branch_code,
                            branch_name=f"Branch {branch_code}",
                            country="UAE",
                        )
                        db.add(branch)
                        branch_cache[branch_code] = branch.id
                        stats["branches"] += 1

                    logger.info(f"Created {stats['branches']} branches")
                except Exception as e:
                    logger.error(f"Error extracting branches: {e}")
                    stats["errors"].append(f"Branches: {e}")

                # ==============================================================
                # PHASE 2: Import Categories
                # ==============================================================
                logger.info("Phase 2: Creating categories...")
                try:
                    categories = ["Retail", "Corporate", "VIP", "Staff", "Government"]
                    for cat_name in categories:
                        category = Category(
                            id=generate_uuid(),
                            name=cat_name,
                            category_type="customer",
                            is_active=True,
                        )
                        db.add(category)
                        category_cache[cat_name.lower()] = category.id
                        stats["categories"] += 1

                    # Add document categories
                    doc_categories = ["Trade License", "Passport", "Emirates ID", "Visa", "Tenancy"]
                    for cat_name in doc_categories:
                        category = Category(
                            id=generate_uuid(),
                            name=cat_name,
                            category_type="document",
                            is_active=True,
                        )
                        db.add(category)
                        stats["categories"] += 1

                    logger.info(f"Created {stats['categories']} categories")
                except Exception as e:
                    logger.error(f"Error creating categories: {e}")
                    stats["errors"].append(f"Categories: {e}")

                # ==============================================================
                # PHASE 3: Import Customers
                # ==============================================================
                logger.info("Phase 3: Importing customers...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Customers")
                    df = df.dropna(how='all')
                    df = df[df['Account No'].notna()]

                    for _, row in df.iterrows():
                        try:
                            account_no = str(int(row.get('Account No', 0)))
                            if not account_no or account_no == '0':
                                continue

                            # Skip if already processed (avoid duplicates)
                            if account_no in customer_cache:
                                continue

                            category = str(row.get('Category', '')).lower()
                            account_type = AccountType.CORPORATE if 'corporate' in category else AccountType.RETAIL

                            branch_code = str(int(row.get('Branch', 0))) if pd.notna(row.get('Branch')) else None

                            customer = Customer(
                                id=generate_uuid(),
                                account_no=account_no,
                                customer_name=clean_str(row.get('Account Name')) or 'Unknown',
                                branch=branch_code,
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

                # ==============================================================
                # PHASE 4: Import Customer Profiles, Documents, Partners
                # ==============================================================
                logger.info("Phase 4: Importing customer profiles, documents, and partners...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="CustomerProfileData")
                    df = df.dropna(how='all')

                    for _, row in df.iterrows():
                        try:
                            account_no = str(int(row.get('AccountNo', 0))) if pd.notna(row.get('AccountNo')) else None
                            if not account_no:
                                continue

                            customer_id = customer_cache.get(account_no)
                            if not customer_id:
                                continue

                            stats["profiles"] += 1

                            # Create Documents
                            doc_types = [
                                ('TradeLicense', DocumentType.TradeLicense),
                                ('Passport', DocumentType.Passport),
                                ('EmiratesID', DocumentType.EmiratesID),
                                ('Visa', DocumentType.Visa),
                                ('Tenancy', DocumentType.Tenancy),
                            ]

                            for prefix, doc_type in doc_types:
                                doc_no = clean_str(row.get(f'{prefix}No'))
                                if doc_no:
                                    doc = Document(
                                        id=generate_short_id("DOC-"),
                                        customer_id=customer_id,
                                        document_type=doc_type,
                                        document_no=doc_no,
                                        issue_date=parse_date(row.get(f'{prefix}Issue')),
                                        expiry_date=parse_date(row.get(f'{prefix}Expiry')),
                                        remarks=clean_str(row.get(f'{prefix}Remarks')),
                                        status=DocumentStatus.ACTIVE,
                                    )
                                    db.add(doc)
                                    stats["documents"] += 1

                            # Create Partners (up to 4)
                            for i in range(1, 5):
                                partner_name = clean_str(row.get(f'Partner{i}Name'))
                                if partner_name:
                                    share_pct = row.get(f'Partner{i}Share')
                                    partner = Partner(
                                        id=generate_short_id("PTR-"),
                                        customer_id=customer_id,
                                        partner_name=partner_name,
                                        nationality=clean_str(row.get(f'Partner{i}Nationality')),
                                        share_percent=Decimal(str(share_pct)) if pd.notna(share_pct) else None,
                                        order_no=i,
                                    )
                                    db.add(partner)
                                    stats["partners"] += 1

                        except Exception as e:
                            stats["errors"].append(f"Profile row error: {e}")

                    logger.info(f"Imported {stats['profiles']} profiles, {stats['documents']} documents, {stats['partners']} partners")
                except Exception as e:
                    logger.error(f"Error importing profiles: {e}")
                    stats["errors"].append(f"Profiles: {e}")

                # ==============================================================
                # PHASE 5: Import Facilities
                # ==============================================================
                logger.info("Phase 5: Importing facilities...")
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
                            elif 'lg' in ftype or 'guarantee' in ftype:
                                facility_type = FacilityType.LG
                            elif 'lc' in ftype or 'credit' in ftype:
                                facility_type = FacilityType.LC
                            elif 'tr' in ftype or 'trust' in ftype:
                                facility_type = FacilityType.TR
                            else:
                                facility_type = FacilityType.OTHER

                            amount = parse_amount(str(row.get('Amount', '0')))

                            facility = Facility(
                                id=clean_str(row.get('FacilityID')) or generate_short_id("FAC-"),
                                customer_id=customer_id,
                                facility_type=facility_type,
                                facility_name=clean_str(row.get('FacilityNo')),
                                reference_no=clean_str(row.get('FacilityNo')),
                                status=FacilityStatus.ACTIVE if row.get('IsActive', 1) == 1 else FacilityStatus.CLOSED,
                                approved_amount=Decimal(str(amount)) if amount else Decimal('0'),
                                currency=clean_str(row.get('Currency')) or 'AED',
                                sanction_date=parse_date(row.get('ApprovalDate')),
                                notes=clean_str(row.get('Notes')),
                            )
                            db.add(facility)
                            stats["facilities"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Facility row error: {e}")

                    logger.info(f"Imported {stats['facilities']} facilities")
                except Exception as e:
                    logger.error(f"Error importing facilities: {e}")
                    stats["errors"].append(f"Facilities: {e}")

                # ==============================================================
                # PHASE 6: Import Guarantors
                # ==============================================================
                logger.info("Phase 6: Importing guarantors...")
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
                                id=clean_str(row.get('GuarantorID')) or generate_short_id("GNT-"),
                                customer_id=customer_id,
                                guarantor_name=clean_str(row.get('GuarantorName')) or 'Unknown',
                                phone=clean_str(row.get('GuarantorAccount')),
                            )
                            db.add(guarantor)

                            cheque_no = row.get('ChequeNo')
                            if pd.notna(cheque_no) and str(cheque_no).strip():
                                cheque = GuarantorCheque(
                                    id=generate_short_id("CHQ-"),
                                    guarantor_id=guarantor.id,
                                    cheque_no=str(cheque_no),
                                    bank_name=clean_str(row.get('IssuingBank')),
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

                # ==============================================================
                # PHASE 7: Import Custom Tasks
                # ==============================================================
                logger.info("Phase 7: Importing tasks...")
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
                            elif 'hold' in status_str:
                                status = TaskStatus.ON_HOLD
                            else:
                                status = TaskStatus.PENDING

                            priority_str = str(row.get('Priority', '')).lower()
                            if 'urgent' in priority_str:
                                priority = TaskPriority.URGENT
                            elif 'high' in priority_str:
                                priority = TaskPriority.HIGH
                            elif 'low' in priority_str:
                                priority = TaskPriority.LOW
                            else:
                                priority = TaskPriority.MEDIUM

                            task = CustomTask(
                                id=generate_short_id("TSK-"),
                                task_id=clean_str(row.get('TaskID')),
                                customer_id=customer_id,
                                account_no=account_no,
                                task_name=clean_str(row.get('TaskName')) or 'Unnamed Task',
                                status=status,
                                priority=priority,
                                follow_up_date=parse_date(row.get('FollowUpDate')),
                                notes=clean_str(row.get('Notes')),
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

                # ==============================================================
                # PHASE 8: Import Customer Notes
                # ==============================================================
                logger.info("Phase 8: Importing customer notes...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="CustomerNotes")
                    df = df.dropna(how='all')

                    for _, row in df.iterrows():
                        try:
                            account_no = str(int(row.get('AccountNo', 0))) if pd.notna(row.get('AccountNo')) else None
                            customer_id = customer_cache.get(account_no) if account_no else None
                            if not customer_id:
                                continue

                            cat_str = str(row.get('Category', '')).lower()
                            if 'follow' in cat_str:
                                note_category = NoteCategory.FOLLOW_UP
                            elif 'meeting' in cat_str:
                                note_category = NoteCategory.MEETING
                            elif 'call' in cat_str:
                                note_category = NoteCategory.CALL
                            elif 'email' in cat_str:
                                note_category = NoteCategory.EMAIL
                            elif 'document' in cat_str or 'doc' in cat_str:
                                note_category = NoteCategory.DOCUMENT
                            elif 'risk' in cat_str:
                                note_category = NoteCategory.RISK
                            elif 'compliance' in cat_str:
                                note_category = NoteCategory.COMPLIANCE
                            else:
                                note_category = NoteCategory.GENERAL

                            priority_str = str(row.get('Priority', '')).lower()
                            if 'high' in priority_str or 'urgent' in priority_str:
                                note_priority = NotePriority.HIGH
                            elif 'low' in priority_str:
                                note_priority = NotePriority.LOW
                            else:
                                note_priority = NotePriority.MEDIUM

                            note = Note(
                                id=clean_str(row.get('NoteID')) or generate_short_id("NTE-"),
                                customer_id=customer_id,
                                title=clean_str(row.get('Title')) or 'Note',
                                content=clean_str(row.get('Content')) or '',
                                category=note_category,
                                priority=note_priority,
                            )
                            db.add(note)
                            stats["notes"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Note row error: {e}")

                    logger.info(f"Imported {stats['notes']} notes")
                except Exception as e:
                    logger.error(f"Error importing notes: {e}")
                    stats["errors"].append(f"Notes: {e}")

                # ==============================================================
                # PHASE 9: Import Journal Entries
                # ==============================================================
                logger.info("Phase 9: Importing journal entries...")
                try:
                    df = pd.read_excel(backend_file, sheet_name="Journal")
                    df = df.dropna(how='all')
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
                                action_type=clean_str(row.get('Action')) or 'import',
                                entity_type='customer' if customer_id else 'general',
                                entity_id=customer_id,
                                description=clean_str(row.get('Notes')) or clean_str(row.get('Item')),
                                details={
                                    "account_no": account_no,
                                    "branch": clean_str(row.get('Branch')),
                                    "category": clean_str(row.get('Category')),
                                    "item": clean_str(row.get('Item')),
                                    "status": clean_str(row.get('Status')),
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

            # ==============================================================
            # PHASE 10: Import Iran Properties
            # ==============================================================
            iran_file = data_dir / "PROPERTIES - IRAN.xlsx"
            if iran_file.exists():
                logger.info("Phase 10: Importing Iran properties...")
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
                                    customer_name=clean_str(row.get('نام مشتری')) or 'Unknown',
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
                                plate_no=clean_str(row.get('شماره پلاک ثبتی')),
                                city=clean_str(row.get('شهر')),
                                address=clean_str(row.get('نشانی ملک')),
                                currency="IRR",
                                owner_name=clean_str(row.get('نام مشتری')),
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

            # ==============================================================
            # PHASE 11: Import UAE Properties with Valuations
            # ==============================================================
            uae_file = data_dir / "PROPERTIES - UAE.xlsx"
            if uae_file.exists():
                logger.info("Phase 11: Importing UAE properties with valuations...")
                try:
                    df = pd.read_excel(uae_file, sheet_name="U.A.E")
                    df = df.dropna(how='all')
                    count = 0
                    valuation_count = 0

                    for _, row in df.iterrows():
                        try:
                            account_no = str(int(row.get('AC  No', 0))) if pd.notna(row.get('AC  No')) else None
                            customer_id = customer_cache.get(account_no) if account_no else None

                            if not customer_id and account_no:
                                customer = Customer(
                                    id=generate_uuid(),
                                    account_no=account_no,
                                    customer_name=clean_str(row.get('Name')) or 'Unknown',
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
                            elif 'warehouse' in prop_type:
                                property_type = PropertyType.WAREHOUSE
                            elif 'office' in prop_type:
                                property_type = PropertyType.OFFICE
                            else:
                                property_type = PropertyType.OTHER

                            value_2025 = parse_amount(str(row.get('AED Value 2025', 0)))

                            prop = Property(
                                id=generate_short_id("PRP-"),
                                customer_id=customer_id,
                                location=PropertyLocation.UAE,
                                property_type=property_type,
                                status=PropertyStatus.MORTGAGED,
                                deed_no=clean_str(row.get('Deed No.')),
                                city=clean_str(row.get('City')),
                                area=clean_str(row.get('Zone')),
                                current_value=Decimal(str(value_2025)) if value_2025 else None,
                                currency="AED",
                                owner_name=clean_str(row.get('Name.1')),
                            )
                            db.add(prop)
                            property_cache[f"{account_no}-{prop.deed_no}"] = prop.id
                            count += 1

                            # Create PropertyValuation records for each year
                            for year in [2021, 2022, 2023, 2024, 2025]:
                                value_col = f'AED Value {year}'
                                if value_col in row.index:
                                    value = parse_amount(str(row.get(value_col, 0)))
                                    if value > 0:
                                        valuation = PropertyValuation(
                                            id=generate_short_id("VAL-"),
                                            property_id=prop.id,
                                            valuation_year=year,
                                            valuation_date=date(year, 1, 1),
                                            market_value=Decimal(str(value)),
                                            currency="AED",
                                        )
                                        db.add(valuation)
                                        valuation_count += 1

                        except Exception as e:
                            stats["errors"].append(f"UAE property row error: {e}")

                    stats["properties"] += count
                    stats["valuations"] = valuation_count
                    logger.info(f"Imported {count} UAE properties with {valuation_count} valuations")
                except Exception as e:
                    logger.error(f"Error importing UAE properties: {e}")
                    stats["errors"].append(f"UAE Properties: {e}")

            # ==============================================================
            # PHASE 12: Import Securities from yearly files
            # ==============================================================
            security_files = sorted(data_dir.glob("Securities List*.xlsx"))
            for sec_file in security_files:
                logger.info(f"Phase 12: Importing securities from {sec_file.name}...")
                year_match = re.search(r'20\d{2}', sec_file.name)
                year = int(year_match.group()) if year_match else None
                count = 0

                try:
                    xl = pd.ExcelFile(sec_file)

                    for sheet in xl.sheet_names:
                        cat_str = sheet.lower()
                        if 'retail' in cat_str:
                            category = SecurityRecordCategory.RETAIL
                        elif 'corporate' in cat_str:
                            category = SecurityRecordCategory.CORPORATE
                        else:
                            continue

                        df = pd.read_excel(xl, sheet_name=sheet, header=None)
                        df = df.dropna(how='all')

                        # Find header row
                        header_row = None
                        for i, row_data in df.iterrows():
                            row_str = ' '.join(str(x).lower() for x in row_data.values if pd.notna(x))
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

                                # Use SecurityRecord model (new)
                                security_record = SecurityRecord(
                                    id=generate_short_id("SCR-"),
                                    customer_id=customer_id,
                                    account_no=account_no,
                                    branch=str(int(branch)) if pd.notna(branch) and isinstance(branch, (int, float)) else clean_str(branch),
                                    customer_name=clean_str(customer_name),
                                    category=category,
                                    year=year,
                                    source_file=sec_file.name,
                                )
                                db.add(security_record)
                                count += 1
                            except Exception as e:
                                stats["errors"].append(f"Security row error: {e}")

                    stats["securities"] += count
                    logger.info(f"Imported {count} securities from {sec_file.name}")
                except Exception as e:
                    logger.error(f"Error importing securities from {sec_file.name}: {e}")
                    stats["errors"].append(f"Securities {sec_file.name}: {e}")

            # ==============================================================
            # COMMIT ALL CHANGES
            # ==============================================================
            await db.commit()

            total = sum([
                stats['branches'], stats['categories'], stats['customers'],
                stats['profiles'], stats['documents'], stats['partners'],
                stats['facilities'], stats['guarantors'], stats['tasks'],
                stats['notes'], stats['properties'], stats['valuations'],
                stats['securities'], stats['journal']
            ])

            logger.info(
                "Auto-import completed successfully",
                branches=stats['branches'],
                categories=stats['categories'],
                customers=stats['customers'],
                profiles=stats['profiles'],
                documents=stats['documents'],
                partners=stats['partners'],
                facilities=stats['facilities'],
                guarantors=stats['guarantors'],
                tasks=stats['tasks'],
                notes=stats['notes'],
                properties=stats['properties'],
                valuations=stats['valuations'],
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
