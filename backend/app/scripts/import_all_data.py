"""
Comprehensive Data Import Script
اسکریپت جامع وارد کردن داده‌ها از تمام فایل‌های اکسل

Usage:
    cd backend
    python -m app.scripts.import_all_data
"""
import os
import sys
import json
import shutil
import asyncio
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional
from decimal import Decimal
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text, func

# Import models
from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.deposit import Deposit
from app.models.journal import JournalEntry
from app.models.task import CustomTask, TaskStatus, TaskPriority
from app.models.security import Security, SecurityCategory, SecurityStatus
from app.models.base import generate_uuid, generate_short_id
from app.core.config import settings


# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent  # ALLIN1 root
DATA_IMPORT_DIR = BASE_DIR / "data-import"
ARCHIVE_DIR = BASE_DIR / "archive" / "imported-data"


class ComprehensiveDataImporter:
    """کلاس جامع برای وارد کردن همه داده‌ها"""

    def __init__(self):
        self.database_url = settings.DATABASE_URL
        # Convert postgres:// to postgresql+asyncpg://
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgresql://") and "+asyncpg" not in self.database_url:
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.stats = {
            "customers": 0,
            "facilities": 0,
            "properties": 0,
            "guarantors": 0,
            "tasks": 0,
            "securities": 0,
            "journal": 0,
            "errors": []
        }
        self.customer_cache = {}  # account_no -> customer_id

    async def run(self):
        """اجرای عملیات واردکردن"""
        print("\n" + "=" * 70)
        print("🚀 Comprehensive Data Import - شروع وارد کردن جامع داده‌ها")
        print("=" * 70)

        # Ensure archive directory exists
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        files = list(DATA_IMPORT_DIR.glob("*.xls*"))
        files = [f for f in files if f.name != "README.md"]

        if not files:
            print("📭 هیچ فایل اکسلی یافت نشد!")
            return

        print(f"\n📁 {len(files)} فایل اکسل یافت شد")

        async with self.async_session() as session:
            # Step 1: Import Customers first (base data)
            await self.import_customers_from_backend(session)

            # Step 2: Import Facilities
            await self.import_facilities_from_backend(session)

            # Step 3: Import Guarantors
            await self.import_guarantors_from_backend(session)

            # Step 4: Import Custom Tasks
            await self.import_tasks_from_backend(session)

            # Step 5: Import Properties (Iran & UAE)
            await self.import_properties(session)

            # Step 6: Import Securities Lists
            await self.import_securities(session)

            # Step 7: Import Journal
            await self.import_journal_from_backend(session)

            await session.commit()
            print("\n✅ همه داده‌ها با موفقیت commit شدند")

        # Archive files
        self.archive_files()

        # Print summary
        self.print_summary()

    async def import_customers_from_backend(self, session: AsyncSession):
        """وارد کردن مشتریان از Backend_Database.xlsm"""
        print("\n" + "-" * 50)
        print("👤 در حال وارد کردن مشتریان...")

        backend_file = DATA_IMPORT_DIR / "Backend_Database.xlsm"
        if not backend_file.exists():
            print("   ⚠️ فایل Backend_Database.xlsm یافت نشد")
            return

        try:
            df = pd.read_excel(backend_file, sheet_name="Customers")
            df = df.dropna(how='all')
            df = df[df['Account No'].notna()]  # Only rows with account number

            for _, row in df.iterrows():
                account_no = str(int(row.get('Account No', 0)))
                if not account_no or account_no == '0':
                    continue

                # Check if customer exists
                result = await session.execute(
                    select(Customer).where(Customer.account_no == account_no)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    self.customer_cache[account_no] = existing.id
                    continue

                # Parse account type
                category = str(row.get('Category', '')).lower()
                if 'corporate' in category:
                    account_type = AccountType.CORPORATE
                elif 'individual' in category or 'retail' in category:
                    account_type = AccountType.RETAIL
                else:
                    account_type = AccountType.RETAIL

                customer = Customer(
                    id=generate_uuid(),
                    account_no=account_no,
                    customer_name=str(row.get('Account Name', '')).strip() or 'Unknown',
                    branch=str(int(row.get('Branch', 0))) if pd.notna(row.get('Branch')) else None,
                    account_type=account_type,
                    status=CustomerStatus.ACTIVE,
                    country="UAE",
                )
                session.add(customer)
                self.customer_cache[account_no] = customer.id
                self.stats["customers"] += 1

            print(f"   ✅ {self.stats['customers']} مشتری وارد شد")

        except Exception as e:
            print(f"   ❌ خطا: {e}")
            self.stats["errors"].append(f"Customers: {e}")

    async def import_facilities_from_backend(self, session: AsyncSession):
        """وارد کردن تسهیلات"""
        print("\n" + "-" * 50)
        print("💳 در حال وارد کردن تسهیلات...")

        backend_file = DATA_IMPORT_DIR / "Backend_Database.xlsm"
        if not backend_file.exists():
            return

        try:
            df = pd.read_excel(backend_file, sheet_name="Facilities")
            df = df.dropna(how='all')

            for _, row in df.iterrows():
                account_no = str(int(row.get('AccountNo', 0)))
                customer_id = self.customer_cache.get(account_no)

                if not customer_id:
                    continue

                # Parse facility type
                ftype = str(row.get('FacilityType', '')).lower()
                if 'overdraft' in ftype or 'od' in ftype:
                    facility_type = FacilityType.OD
                elif 'personal' in ftype or 'loan' in ftype:
                    facility_type = FacilityType.LOAN
                elif 'lg' in ftype or 'guarantee' in ftype:
                    facility_type = FacilityType.LG
                else:
                    facility_type = FacilityType.OTHER

                # Parse amount
                amount_str = str(row.get('Amount', '0'))
                amount = self.parse_amount(amount_str)

                facility = Facility(
                    id=str(row.get('FacilityID')) or generate_short_id("FAC-"),
                    customer_id=customer_id,
                    facility_type=facility_type,
                    facility_name=str(row.get('FacilityNo', '')) or None,
                    reference_no=str(row.get('FacilityNo', '')) or None,
                    status=FacilityStatus.ACTIVE if row.get('IsActive', 1) == 1 else FacilityStatus.CLOSED,
                    approved_amount=Decimal(str(amount)) if amount else Decimal('0'),
                    currency=str(row.get('Currency', 'AED')),
                    sanction_date=self.parse_date(row.get('ApprovalDate')),
                    notes=str(row.get('Notes', '')) or None,
                )
                session.add(facility)
                self.stats["facilities"] += 1

            print(f"   ✅ {self.stats['facilities']} تسهیلات وارد شد")

        except Exception as e:
            print(f"   ❌ خطا: {e}")
            self.stats["errors"].append(f"Facilities: {e}")

    async def import_guarantors_from_backend(self, session: AsyncSession):
        """وارد کردن ضامنین"""
        print("\n" + "-" * 50)
        print("👥 در حال وارد کردن ضامنین...")

        backend_file = DATA_IMPORT_DIR / "Backend_Database.xlsm"
        if not backend_file.exists():
            return

        try:
            df = pd.read_excel(backend_file, sheet_name="Guarantors")
            df = df.dropna(how='all')

            for _, row in df.iterrows():
                account_no = str(int(row.get('AccountNo', 0)))
                customer_id = self.customer_cache.get(account_no)

                if not customer_id:
                    continue

                guarantor = Guarantor(
                    id=str(row.get('GuarantorID')) or generate_short_id("GNT-"),
                    customer_id=customer_id,
                    guarantor_name=str(row.get('GuarantorName', '')).strip() or 'Unknown',
                    phone=str(row.get('GuarantorAccount', '')) if pd.notna(row.get('GuarantorAccount')) else None,
                )
                session.add(guarantor)

                # Add cheque if exists
                cheque_no = row.get('ChequeNo')
                if pd.notna(cheque_no) and str(cheque_no).strip():
                    cheque = GuarantorCheque(
                        id=generate_short_id("CHQ-"),
                        guarantor_id=guarantor.id,
                        cheque_no=str(cheque_no),
                        bank_name=str(row.get('IssuingBank', '')) or None,
                        amount=Decimal(str(self.parse_amount(str(row.get('ChequeAmount', '0'))))) if row.get('ChequeAmount') else None,
                        currency="AED",
                    )
                    session.add(cheque)

                self.stats["guarantors"] += 1

            print(f"   ✅ {self.stats['guarantors']} ضامن وارد شد")

        except Exception as e:
            print(f"   ❌ خطا: {e}")
            self.stats["errors"].append(f"Guarantors: {e}")

    async def import_tasks_from_backend(self, session: AsyncSession):
        """وارد کردن وظایف سفارشی"""
        print("\n" + "-" * 50)
        print("📋 در حال وارد کردن وظایف...")

        backend_file = DATA_IMPORT_DIR / "Backend_Database.xlsm"
        if not backend_file.exists():
            return

        try:
            df = pd.read_excel(backend_file, sheet_name="CustomTasks")
            df = df.dropna(how='all')

            for _, row in df.iterrows():
                account_no = str(int(row.get('AccountNo', 0))) if pd.notna(row.get('AccountNo')) else None
                customer_id = self.customer_cache.get(account_no) if account_no else None

                # Parse status
                status_str = str(row.get('Status', '')).lower()
                if 'complete' in status_str:
                    status = TaskStatus.COMPLETED
                elif 'progress' in status_str:
                    status = TaskStatus.IN_PROGRESS
                elif 'cancel' in status_str:
                    status = TaskStatus.CANCELLED
                else:
                    status = TaskStatus.PENDING

                # Parse priority
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
                    follow_up_date=self.parse_date(row.get('FollowUpDate')),
                    notes=str(row.get('Notes', '')) if pd.notna(row.get('Notes')) else None,
                    is_active=row.get('IsActive', 1) == 1,
                )
                session.add(task)
                self.stats["tasks"] += 1

            print(f"   ✅ {self.stats['tasks']} وظیفه وارد شد")

        except Exception as e:
            print(f"   ❌ خطا: {e}")
            self.stats["errors"].append(f"Tasks: {e}")

    async def import_properties(self, session: AsyncSession):
        """وارد کردن املاک ایران و امارات"""
        print("\n" + "-" * 50)
        print("🏠 در حال وارد کردن املاک...")

        # Import Iran Properties
        await self.import_iran_properties(session)

        # Import UAE Properties
        await self.import_uae_properties(session)

    async def import_iran_properties(self, session: AsyncSession):
        """وارد کردن املاک ایران"""
        iran_file = DATA_IMPORT_DIR / "PROPERTIES - IRAN.xlsx"
        if not iran_file.exists():
            print("   ⚠️ فایل PROPERTIES - IRAN.xlsx یافت نشد")
            return

        try:
            df = pd.read_excel(iran_file, sheet_name="IRAN")
            df = df.dropna(how='all')
            count = 0

            for _, row in df.iterrows():
                account_no = str(int(row.get('شماره حساب', 0))) if pd.notna(row.get('شماره حساب')) else None
                customer_id = self.customer_cache.get(account_no) if account_no else None

                # If no customer found, create one
                if not customer_id and account_no:
                    customer = Customer(
                        id=generate_uuid(),
                        account_no=account_no,
                        customer_name=str(row.get('نام مشتری', '')).strip() or 'Unknown',
                        account_type=AccountType.CORPORATE,
                        status=CustomerStatus.ACTIVE,
                        country="IRAN",
                    )
                    session.add(customer)
                    customer_id = customer.id
                    self.customer_cache[account_no] = customer_id
                    self.stats["customers"] += 1

                if not customer_id:
                    continue

                # Parse property type
                prop_type = str(row.get('نوع', '')).lower()
                if 'آپارتمان' in prop_type:
                    property_type = PropertyType.APARTMENT
                elif 'ویلا' in prop_type:
                    property_type = PropertyType.VILLA
                elif 'زمین' in prop_type:
                    property_type = PropertyType.LAND
                elif 'مغازه' in prop_type or 'تجاری' in prop_type:
                    property_type = PropertyType.SHOP
                elif 'اداری' in prop_type:
                    property_type = PropertyType.OFFICE
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
                    area_sqm=self.parse_decimal(row.get('مساحت زمین (م۲)')),
                    currency="IRR",
                    owner_name=str(row.get('نام مشتری', '')) if pd.notna(row.get('نام مشتری')) else None,
                )
                session.add(prop)
                count += 1

            self.stats["properties"] += count
            print(f"   ✅ {count} ملک ایران وارد شد")

        except Exception as e:
            print(f"   ❌ خطا در املاک ایران: {e}")
            self.stats["errors"].append(f"Iran Properties: {e}")

    async def import_uae_properties(self, session: AsyncSession):
        """وارد کردن املاک امارات"""
        uae_file = DATA_IMPORT_DIR / "PROPERTIES - UAE.xlsx"
        if not uae_file.exists():
            print("   ⚠️ فایل PROPERTIES - UAE.xlsx یافت نشد")
            return

        try:
            df = pd.read_excel(uae_file, sheet_name="U.A.E")
            df = df.dropna(how='all')
            count = 0

            for _, row in df.iterrows():
                account_no = str(int(row.get('AC  No', 0))) if pd.notna(row.get('AC  No')) else None
                customer_id = self.customer_cache.get(account_no) if account_no else None

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
                    session.add(customer)
                    customer_id = customer.id
                    self.customer_cache[account_no] = customer_id
                    self.stats["customers"] += 1

                if not customer_id:
                    continue

                # Parse property type
                prop_type = str(row.get('TYPE', '')).lower()
                if 'building' in prop_type:
                    property_type = PropertyType.BUILDING
                elif 'residential' in prop_type or 'apartment' in prop_type:
                    property_type = PropertyType.APARTMENT
                elif 'villa' in prop_type:
                    property_type = PropertyType.VILLA
                elif 'land' in prop_type:
                    property_type = PropertyType.LAND
                elif 'shop' in prop_type or 'commercial' in prop_type:
                    property_type = PropertyType.SHOP
                elif 'office' in prop_type:
                    property_type = PropertyType.OFFICE
                else:
                    property_type = PropertyType.OTHER

                # Parse value
                value_2025 = self.parse_amount(str(row.get('AED Value 2025', 0)))

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
                session.add(prop)
                count += 1

            self.stats["properties"] += count
            print(f"   ✅ {count} ملک امارات وارد شد")

        except Exception as e:
            print(f"   ❌ خطا در املاک امارات: {e}")
            self.stats["errors"].append(f"UAE Properties: {e}")

    async def import_securities(self, session: AsyncSession):
        """وارد کردن اوراق بهادار از فایل‌های Securities List"""
        print("\n" + "-" * 50)
        print("📜 در حال وارد کردن اوراق بهادار...")

        security_files = sorted(DATA_IMPORT_DIR.glob("Securities List*.xlsx"))
        total_count = 0

        for sec_file in security_files:
            year = self.extract_year_from_filename(sec_file.name)
            try:
                xl = pd.ExcelFile(sec_file)

                for sheet in xl.sheet_names:
                    # Determine category
                    if 'retail' in sheet.lower():
                        category = SecurityCategory.RETAIL
                    else:
                        category = SecurityCategory.CORPORATE

                    df = pd.read_excel(xl, sheet_name=sheet, header=None)
                    df = df.dropna(how='all')

                    # Find header row (usually contains 'Account No' or similar)
                    header_row = None
                    for i, row in df.iterrows():
                        row_str = ' '.join(str(x).lower() for x in row.values if pd.notna(x))
                        if 'account' in row_str and ('no' in row_str or '#' in row_str):
                            header_row = i
                            break

                    if header_row is None:
                        continue

                    # Set header and skip rows before data
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:]
                    df = df.dropna(how='all')

                    count = 0
                    for _, row in df.iterrows():
                        # Find account number column
                        account_no = None
                        for col in df.columns:
                            if 'account' in str(col).lower():
                                account_no = row.get(col)
                                break

                        if pd.isna(account_no):
                            continue

                        account_no = str(int(account_no)) if isinstance(account_no, float) else str(account_no)
                        customer_id = self.customer_cache.get(account_no)

                        # Get customer name
                        customer_name = None
                        for col in df.columns:
                            if 'customer' in str(col).lower() or 'name' in str(col).lower():
                                customer_name = row.get(col)
                                break

                        # Get branch
                        branch = None
                        for col in df.columns:
                            if 'branch' in str(col).lower():
                                branch = row.get(col)
                                break

                        # Get guarantor info
                        guarantor_info = None
                        for col in df.columns:
                            if 'guarantor' in str(col).lower():
                                guarantor_info = row.get(col)
                                break

                        # Get cheque info
                        cheque_no = None
                        for col in df.columns:
                            if 'chq' in str(col).lower() or 'cheque' in str(col).lower():
                                if 'no' in str(col).lower() or '#' in str(col).lower():
                                    cheque_no = row.get(col)
                                    break

                        security = Security(
                            id=generate_short_id("SEC-"),
                            customer_id=customer_id,
                            account_no=account_no,
                            branch=str(int(branch)) if pd.notna(branch) and isinstance(branch, (int, float)) else str(branch) if pd.notna(branch) else None,
                            customer_name=str(customer_name).strip() if pd.notna(customer_name) else None,
                            category=category,
                            year=year,
                            guarantors=[str(guarantor_info)] if pd.notna(guarantor_info) and str(guarantor_info).strip() else [],
                            cheque_numbers=[str(cheque_no)] if pd.notna(cheque_no) and str(cheque_no).strip() else [],
                            status=SecurityStatus.ACTIVE,
                            source_file=sec_file.name,
                        )
                        session.add(security)
                        count += 1

                    total_count += count
                    print(f"   📄 {sec_file.name} / {sheet}: {count} رکورد")

            except Exception as e:
                print(f"   ❌ خطا در {sec_file.name}: {e}")
                self.stats["errors"].append(f"Securities {sec_file.name}: {e}")

        self.stats["securities"] = total_count
        print(f"   ✅ مجموع {total_count} اوراق بهادار وارد شد")

    async def import_journal_from_backend(self, session: AsyncSession):
        """وارد کردن ژورنال"""
        print("\n" + "-" * 50)
        print("📝 در حال وارد کردن ژورنال...")

        backend_file = DATA_IMPORT_DIR / "Backend_Database.xlsm"
        if not backend_file.exists():
            return

        try:
            df = pd.read_excel(backend_file, sheet_name="Journal")
            df = df.dropna(how='all')
            # Skip header marker row
            df = df[df['Record ID'] != '--- Data Below ---']
            count = 0

            for _, row in df.iterrows():
                account_no = str(int(row.get('Account No', 0))) if pd.notna(row.get('Account No')) else None
                customer_id = self.customer_cache.get(account_no) if account_no else None

                # Parse timestamp
                entry_date = self.parse_date(row.get('Date'))
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
                        "status": str(row.get('Status', '')) if pd.notna(row.get('Status')) else None,
                        "priority": str(row.get('Priority', '')) if pd.notna(row.get('Priority')) else None,
                        "source": str(row.get('Source', '')) if pd.notna(row.get('Source')) else None,
                        "user": str(row.get('User', '')) if pd.notna(row.get('User')) else None,
                    }
                )
                session.add(entry)
                count += 1

            self.stats["journal"] = count
            print(f"   ✅ {count} ورودی ژورنال وارد شد")

        except Exception as e:
            print(f"   ❌ خطا: {e}")
            self.stats["errors"].append(f"Journal: {e}")

    def archive_files(self):
        """انتقال فایل‌ها به آرشیو"""
        print("\n" + "-" * 50)
        print("📦 در حال انتقال فایل‌ها به آرشیو...")

        files = list(DATA_IMPORT_DIR.glob("*.xls*"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for f in files:
            if f.name == "README.md":
                continue
            archive_name = f"{f.stem}_{timestamp}{f.suffix}"
            archive_path = ARCHIVE_DIR / archive_name
            shutil.move(str(f), str(archive_path))
            print(f"   📁 {f.name} → archive/")

    def print_summary(self):
        """چاپ خلاصه عملیات"""
        print("\n" + "=" * 70)
        print("📊 خلاصه عملیات وارد کردن داده")
        print("=" * 70)
        print(f"   👤 مشتریان: {self.stats['customers']}")
        print(f"   💳 تسهیلات: {self.stats['facilities']}")
        print(f"   🏠 املاک: {self.stats['properties']}")
        print(f"   👥 ضامنین: {self.stats['guarantors']}")
        print(f"   📋 وظایف: {self.stats['tasks']}")
        print(f"   📜 اوراق بهادار: {self.stats['securities']}")
        print(f"   📝 ژورنال: {self.stats['journal']}")

        total = sum([
            self.stats['customers'],
            self.stats['facilities'],
            self.stats['properties'],
            self.stats['guarantors'],
            self.stats['tasks'],
            self.stats['securities'],
            self.stats['journal']
        ])
        print(f"\n   📈 مجموع رکوردها: {total}")

        if self.stats['errors']:
            print(f"\n   ⚠️ خطاها ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:5]:
                print(f"      - {err}")

        print("=" * 70 + "\n")

    # Helper methods
    def parse_amount(self, value) -> float:
        """تبدیل مبلغ به عدد"""
        if pd.isna(value) or value is None:
            return 0
        value = str(value)
        # Remove common currency indicators and formatting
        value = re.sub(r'[^\d.]', '', value.replace(',', '').replace('/-', ''))
        try:
            return float(value) if value else 0
        except:
            return 0

    def parse_decimal(self, value) -> Optional[Decimal]:
        """تبدیل به Decimal"""
        amount = self.parse_amount(value)
        return Decimal(str(amount)) if amount > 0 else None

    def parse_date(self, value) -> Optional[date]:
        """تبدیل تاریخ"""
        if pd.isna(value) or value is None:
            return None
        try:
            if isinstance(value, (datetime, date)):
                return value if isinstance(value, date) else value.date()
            # Try common formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(str(value).split()[0], fmt).date()
                except:
                    continue
        except:
            pass
        return None

    def extract_year_from_filename(self, filename: str) -> Optional[int]:
        """استخراج سال از نام فایل"""
        match = re.search(r'20\d{2}', filename)
        return int(match.group()) if match else None


async def main():
    """تابع اصلی"""
    importer = ComprehensiveDataImporter()
    await importer.run()


if __name__ == "__main__":
    asyncio.run(main())
