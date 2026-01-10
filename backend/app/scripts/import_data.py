"""
Data Import Script
اسکریپت وارد کردن داده‌ها از فایل‌های اکسل، CSV، JSON به دیتابیس

Usage:
    cd backend
    python -m app.scripts.import_data

این اسکریپت فایل‌ها را از پوشه data-import خوانده و به دیتابیس وارد می‌کند
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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

# Import models
from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.guarantor import Guarantor
from app.models.deposit import Deposit
from app.models.checklist import Checklist, ChecklistItem
from app.models.base import generate_uuid, generate_short_id
from app.core.config import settings


# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent  # ALLIN1 root
DATA_IMPORT_DIR = BASE_DIR / "data-import"
ARCHIVE_DIR = BASE_DIR / "archive" / "imported-data"


class DataImporter:
    """کلاس اصلی برای وارد کردن داده‌ها"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
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
            "deposits": 0,
            "checklists": 0,
            "errors": []
        }

    async def run(self):
        """اجرای عملیات واردکردن"""
        print("\n" + "="*60)
        print("🚀 Data Import Script - شروع وارد کردن داده‌ها")
        print("="*60)

        # Ensure archive directory exists
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Check for files
        if not DATA_IMPORT_DIR.exists():
            print(f"❌ پوشه {DATA_IMPORT_DIR} وجود ندارد!")
            return

        files = list(DATA_IMPORT_DIR.glob("*"))
        files = [f for f in files if f.is_file() and not f.name.startswith('.') and f.name != 'README.md']

        if not files:
            print("📭 هیچ فایلی برای وارد کردن یافت نشد!")
            print(f"   فایل‌های خود را در پوشه {DATA_IMPORT_DIR} قرار دهید")
            return

        print(f"\n📁 {len(files)} فایل یافت شد:")
        for f in files:
            print(f"   - {f.name}")

        # Process each file
        for file_path in files:
            await self.process_file(file_path)

        # Print summary
        self.print_summary()

    async def process_file(self, file_path: Path):
        """پردازش یک فایل"""
        print(f"\n📄 در حال پردازش: {file_path.name}")

        try:
            # Determine file type and data type
            ext = file_path.suffix.lower()
            data_type = self.detect_data_type(file_path.name)

            # Read file based on extension
            if ext in ['.xlsx', '.xls', '.xlsm']:
                data = self.read_excel(file_path)
            elif ext == '.csv':
                data = self.read_csv(file_path)
            elif ext == '.json':
                data = self.read_json(file_path)
            else:
                print(f"   ⚠️ فرمت {ext} پشتیبانی نمی‌شود")
                return

            if data is None or len(data) == 0:
                print(f"   ⚠️ داده‌ای یافت نشد")
                return

            print(f"   📊 {len(data)} ردیف داده خوانده شد")

            # Import based on data type
            async with self.async_session() as session:
                if data_type == 'customers':
                    await self.import_customers(session, data)
                elif data_type == 'facilities':
                    await self.import_facilities(session, data)
                elif data_type == 'properties':
                    await self.import_properties(session, data)
                elif data_type == 'guarantors':
                    await self.import_guarantors(session, data)
                elif data_type == 'deposits':
                    await self.import_deposits(session, data)
                elif data_type == 'checklists':
                    await self.import_checklists(session, data)
                else:
                    # Auto-detect from content
                    await self.auto_import(session, data, file_path.name)

                await session.commit()

            # Move to archive
            self.archive_file(file_path)
            print(f"   ✅ پردازش کامل شد - فایل به آرشیو منتقل شد")

        except Exception as e:
            error_msg = f"خطا در پردازش {file_path.name}: {str(e)}"
            print(f"   ❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            import traceback
            traceback.print_exc()

    def detect_data_type(self, filename: str) -> str:
        """تشخیص نوع داده از نام فایل"""
        filename_lower = filename.lower()

        if 'customer' in filename_lower or 'client' in filename_lower or 'مشتری' in filename_lower:
            return 'customers'
        elif 'facilit' in filename_lower or 'loan' in filename_lower or 'تسهیلات' in filename_lower or 'وام' in filename_lower:
            return 'facilities'
        elif 'propert' in filename_lower or 'ملک' in filename_lower or 'املاک' in filename_lower:
            return 'properties'
        elif 'guarant' in filename_lower or 'ضامن' in filename_lower:
            return 'guarantors'
        elif 'deposit' in filename_lower or 'سپرده' in filename_lower:
            return 'deposits'
        elif 'checklist' in filename_lower or 'چک لیست' in filename_lower:
            return 'checklists'

        return 'auto'

    def read_excel(self, file_path: Path) -> List[Dict]:
        """خواندن فایل اکسل"""
        try:
            # Read all sheets
            xl = pd.ExcelFile(file_path)
            all_data = []

            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                df = df.dropna(how='all')  # Remove empty rows

                if len(df) > 0:
                    # Convert to dict, handling NaN values
                    records = df.to_dict('records')
                    for record in records:
                        # Add sheet name for context
                        record['_sheet_name'] = sheet_name
                        # Clean NaN values
                        record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
                        all_data.append(record)

            return all_data
        except Exception as e:
            print(f"   ❌ خطا در خواندن اکسل: {e}")
            return []

    def read_csv(self, file_path: Path) -> List[Dict]:
        """خواندن فایل CSV"""
        try:
            df = pd.read_csv(file_path)
            df = df.dropna(how='all')
            records = df.to_dict('records')
            return [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]
        except Exception as e:
            print(f"   ❌ خطا در خواندن CSV: {e}")
            return []

    def read_json(self, file_path: Path) -> List[Dict]:
        """خواندن فایل JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # If dict has a 'data' or 'items' key, use that
                for key in ['data', 'items', 'records', 'customers', 'facilities']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            return []
        except Exception as e:
            print(f"   ❌ خطا در خواندن JSON: {e}")
            return []

    async def import_customers(self, session: AsyncSession, data: List[Dict]):
        """وارد کردن مشتریان"""
        for row in data:
            try:
                # Map columns (support both English and Persian)
                customer = Customer(
                    id=generate_uuid(),
                    account_no=str(row.get('account_no') or row.get('شماره حساب') or row.get('Account No') or generate_short_id("ACC-")),
                    customer_name=row.get('customer_name') or row.get('name') or row.get('نام') or row.get('Name') or 'Unknown',
                    customer_name_ar=row.get('customer_name_ar') or row.get('نام فارسی') or None,
                    account_type=self.parse_account_type(row.get('account_type') or row.get('نوع حساب') or row.get('Type')),
                    branch=row.get('branch') or row.get('شعبه') or None,
                    relationship_manager=row.get('relationship_manager') or row.get('rm') or row.get('مدیر ارتباط') or None,
                    status=CustomerStatus.ACTIVE,
                    phone=str(row.get('phone') or row.get('تلفن') or row.get('Phone') or '') or None,
                    mobile=str(row.get('mobile') or row.get('موبایل') or row.get('Mobile') or '') or None,
                    email=row.get('email') or row.get('ایمیل') or row.get('Email') or None,
                    address=row.get('address') or row.get('آدرس') or row.get('Address') or None,
                    city=row.get('city') or row.get('شهر') or row.get('City') or None,
                    country=row.get('country') or row.get('کشور') or row.get('Country') or 'UAE',
                    company_type=row.get('company_type') or row.get('نوع شرکت') or None,
                    industry=row.get('industry') or row.get('صنعت') or None,
                    notes=row.get('notes') or row.get('یادداشت') or row.get('Notes') or None,
                )
                session.add(customer)
                self.stats["customers"] += 1
            except Exception as e:
                self.stats["errors"].append(f"Customer error: {e}")

        print(f"   👤 {self.stats['customers']} مشتری وارد شد")

    async def import_facilities(self, session: AsyncSession, data: List[Dict]):
        """وارد کردن تسهیلات"""
        for row in data:
            try:
                # Get or create customer reference
                customer_id = row.get('customer_id') or row.get('شماره مشتری')
                if not customer_id:
                    # Try to find by account_no or name
                    account_no = row.get('account_no') or row.get('شماره حساب')
                    if account_no:
                        result = await session.execute(
                            select(Customer).where(Customer.account_no == str(account_no))
                        )
                        customer = result.scalar_one_or_none()
                        if customer:
                            customer_id = customer.id

                if not customer_id:
                    continue  # Skip if no customer

                facility = Facility(
                    id=generate_short_id("FAC-"),
                    customer_id=customer_id,
                    facility_type=self.parse_facility_type(row.get('facility_type') or row.get('type') or row.get('نوع')),
                    facility_name=row.get('facility_name') or row.get('نام تسهیلات') or None,
                    reference_no=row.get('reference_no') or row.get('شماره مرجع') or None,
                    status=FacilityStatus.ACTIVE,
                    approved_amount=self.parse_decimal(row.get('approved_amount') or row.get('amount') or row.get('مبلغ') or 0),
                    currency=row.get('currency') or row.get('ارز') or 'AED',
                    outstanding_amount=self.parse_decimal(row.get('outstanding') or row.get('مانده') or 0),
                    interest_rate=self.parse_decimal(row.get('interest_rate') or row.get('نرخ') or None),
                    maturity_date=self.parse_date(row.get('maturity_date') or row.get('سررسید')),
                    notes=row.get('notes') or row.get('یادداشت') or None,
                )
                session.add(facility)
                self.stats["facilities"] += 1
            except Exception as e:
                self.stats["errors"].append(f"Facility error: {e}")

        print(f"   💳 {self.stats['facilities']} تسهیلات وارد شد")

    async def import_properties(self, session: AsyncSession, data: List[Dict]):
        """وارد کردن املاک"""
        for row in data:
            try:
                customer_id = row.get('customer_id') or row.get('شماره مشتری')
                if not customer_id:
                    account_no = row.get('account_no') or row.get('شماره حساب')
                    if account_no:
                        result = await session.execute(
                            select(Customer).where(Customer.account_no == str(account_no))
                        )
                        customer = result.scalar_one_or_none()
                        if customer:
                            customer_id = customer.id

                if not customer_id:
                    continue

                property_obj = Property(
                    id=generate_short_id("PRP-"),
                    customer_id=customer_id,
                    location=self.parse_property_location(row.get('location') or row.get('موقعیت') or row.get('کشور')),
                    property_type=self.parse_property_type(row.get('property_type') or row.get('type') or row.get('نوع')),
                    status=PropertyStatus.FREE,
                    plate_no=row.get('plate_no') or row.get('پلاک') or None,
                    deed_no=row.get('deed_no') or row.get('شماره سند') or None,
                    address=row.get('address') or row.get('آدرس') or None,
                    city=row.get('city') or row.get('شهر') or None,
                    area=row.get('area') or row.get('منطقه') or None,
                    area_sqm=self.parse_decimal(row.get('area_sqm') or row.get('متراژ') or None),
                    current_value=self.parse_decimal(row.get('value') or row.get('current_value') or row.get('ارزش') or None),
                    currency=row.get('currency') or row.get('ارز') or 'AED',
                    owner_name=row.get('owner_name') or row.get('مالک') or None,
                    notes=row.get('notes') or row.get('یادداشت') or None,
                )
                session.add(property_obj)
                self.stats["properties"] += 1
            except Exception as e:
                self.stats["errors"].append(f"Property error: {e}")

        print(f"   🏠 {self.stats['properties']} ملک وارد شد")

    async def import_guarantors(self, session: AsyncSession, data: List[Dict]):
        """وارد کردن ضامنین"""
        for row in data:
            try:
                customer_id = row.get('customer_id')
                facility_id = row.get('facility_id')

                if not customer_id:
                    continue

                guarantor = Guarantor(
                    id=generate_short_id("GNT-"),
                    customer_id=customer_id,
                    facility_id=facility_id,
                    guarantor_name=row.get('name') or row.get('guarantor_name') or row.get('نام') or 'Unknown',
                    relationship_type=row.get('relation') or row.get('relationship_type') or row.get('نسبت') or None,
                    phone=str(row.get('phone') or row.get('تلفن') or '') or None,
                    address=row.get('address') or row.get('آدرس') or None,
                    passport_no=row.get('passport_no') or row.get('پاسپورت') or None,
                    emirates_id=row.get('emirates_id') or row.get('شناسه امارات') or None,
                )
                session.add(guarantor)
                self.stats["guarantors"] += 1
            except Exception as e:
                self.stats["errors"].append(f"Guarantor error: {e}")

        print(f"   👥 {self.stats['guarantors']} ضامن وارد شد")

    async def import_deposits(self, session: AsyncSession, data: List[Dict]):
        """وارد کردن سپرده‌ها"""
        from app.models.deposit import DepositType, DepositStatus

        for row in data:
            try:
                customer_id = row.get('customer_id')
                if not customer_id:
                    # Try to find by account_no
                    account_no = row.get('account_no') or row.get('شماره حساب')
                    if account_no:
                        result = await session.execute(
                            select(Customer).where(Customer.account_no == str(account_no))
                        )
                        customer = result.scalar_one_or_none()
                        if customer:
                            customer_id = customer.id

                if not customer_id:
                    continue

                deposit = Deposit(
                    id=generate_short_id("DEP-"),
                    customer_id=customer_id,
                    deposit_type=self.parse_deposit_type(row.get('deposit_type') or row.get('نوع')),
                    deposit_number=str(row.get('deposit_number') or row.get('شماره سپرده') or generate_short_id("DN-")),
                    principal_amount=self.parse_decimal(row.get('amount') or row.get('principal_amount') or row.get('مبلغ') or 0),
                    currency=row.get('currency') or row.get('ارز') or 'AED',
                    interest_rate=self.parse_decimal(row.get('interest_rate') or row.get('نرخ')),
                    opening_date=self.parse_date(row.get('opening_date') or row.get('تاریخ افتتاح')) or date.today(),
                    maturity_date=self.parse_date(row.get('maturity_date') or row.get('سررسید')),
                    notes=row.get('notes') or row.get('یادداشت') or None,
                )
                session.add(deposit)
                self.stats["deposits"] += 1
            except Exception as e:
                self.stats["errors"].append(f"Deposit error: {e}")

        print(f"   💰 {self.stats['deposits']} سپرده وارد شد")

    def parse_deposit_type(self, value):
        """تبدیل نوع سپرده"""
        from app.models.deposit import DepositType
        if not value:
            return DepositType.FIXED_DEPOSIT
        value = str(value).upper()
        if 'FIXED' in value or 'FD' in value or 'ثابت' in value:
            return DepositType.FIXED_DEPOSIT
        elif 'SAVING' in value or 'پس‌انداز' in value:
            return DepositType.SAVINGS
        elif 'CURRENT' in value or 'جاری' in value:
            return DepositType.CURRENT
        elif 'CALL' in value or 'دیداری' in value:
            return DepositType.CALL_DEPOSIT
        return DepositType.FIXED_DEPOSIT

    async def import_checklists(self, session: AsyncSession, data: List[Dict]):
        """وارد کردن چک لیست‌ها"""
        # Implementation for checklists
        print(f"   📋 چک لیست‌ها در نسخه بعدی اضافه خواهد شد")

    async def auto_import(self, session: AsyncSession, data: List[Dict], filename: str):
        """تشخیص خودکار نوع داده و وارد کردن"""
        if not data:
            return

        # Check column names to detect type
        sample = data[0]
        columns = set(str(k).lower() for k in sample.keys())

        # Detect by column names
        customer_cols = {'customer_name', 'name', 'نام', 'account_no', 'شماره حساب', 'email', 'phone'}
        facility_cols = {'facility_type', 'approved_amount', 'amount', 'مبلغ', 'interest_rate', 'نرخ', 'maturity_date'}
        property_cols = {'property_type', 'نوع ملک', 'address', 'آدرس', 'area_sqm', 'متراژ', 'deed_no'}

        if columns & customer_cols:
            print(f"   🔍 تشخیص خودکار: داده‌های مشتری")
            await self.import_customers(session, data)
        elif columns & facility_cols:
            print(f"   🔍 تشخیص خودکار: داده‌های تسهیلات")
            await self.import_facilities(session, data)
        elif columns & property_cols:
            print(f"   🔍 تشخیص خودکار: داده‌های املاک")
            await self.import_properties(session, data)
        else:
            print(f"   ⚠️ نوع داده قابل تشخیص نیست - ستون‌ها: {', '.join(columns)}")

    def archive_file(self, file_path: Path):
        """انتقال فایل به آرشیو"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        archive_path = ARCHIVE_DIR / archive_name
        shutil.move(str(file_path), str(archive_path))

    # Helper methods for parsing
    def parse_account_type(self, value) -> AccountType:
        if not value:
            return AccountType.RETAIL
        value = str(value).lower()
        if 'corporate' in value or 'شرکت' in value:
            return AccountType.CORPORATE
        elif 'sme' in value:
            return AccountType.SME
        return AccountType.RETAIL

    def parse_facility_type(self, value) -> FacilityType:
        if not value:
            return FacilityType.LOAN
        value = str(value).upper()
        type_map = {
            'OD': FacilityType.OD, 'OVERDRAFT': FacilityType.OD, 'اضافه برداشت': FacilityType.OD,
            'LOAN': FacilityType.LOAN, 'وام': FacilityType.LOAN,
            'LG': FacilityType.LG, 'GUARANTEE': FacilityType.LG, 'ضمانتنامه': FacilityType.LG,
            'LC': FacilityType.LC_SIGHT, 'اعتبار اسنادی': FacilityType.LC_SIGHT,
            'TR': FacilityType.TR, 'TRUST': FacilityType.TR,
        }
        for key, ftype in type_map.items():
            if key in value:
                return ftype
        return FacilityType.OTHER

    def parse_property_location(self, value) -> PropertyLocation:
        if not value:
            return PropertyLocation.UAE
        value = str(value).upper()
        if 'IRAN' in value or 'ایران' in value:
            return PropertyLocation.IRAN
        elif 'UAE' in value or 'امارات' in value or 'DUBAI' in value or 'دبی' in value:
            return PropertyLocation.UAE
        return PropertyLocation.OTHER

    def parse_property_type(self, value) -> PropertyType:
        if not value:
            return PropertyType.OTHER
        value = str(value).upper()
        type_map = {
            'VILLA': PropertyType.VILLA, 'ویلا': PropertyType.VILLA,
            'APARTMENT': PropertyType.APARTMENT, 'آپارتمان': PropertyType.APARTMENT,
            'OFFICE': PropertyType.OFFICE, 'اداری': PropertyType.OFFICE,
            'LAND': PropertyType.LAND, 'زمین': PropertyType.LAND,
            'SHOP': PropertyType.SHOP, 'مغازه': PropertyType.SHOP,
            'BUILDING': PropertyType.BUILDING, 'ساختمان': PropertyType.BUILDING,
        }
        for key, ptype in type_map.items():
            if key in value:
                return ptype
        return PropertyType.OTHER

    def parse_decimal(self, value) -> Optional[Decimal]:
        if value is None or value == '':
            return None
        try:
            # Remove commas and convert
            clean_val = str(value).replace(',', '').replace('،', '').strip()
            return Decimal(clean_val)
        except:
            return None

    def parse_date(self, value) -> Optional[date]:
        if not value:
            return None
        try:
            if isinstance(value, (datetime, date)):
                return value if isinstance(value, date) else value.date()
            # Try common formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(str(value), fmt).date()
                except:
                    continue
        except:
            pass
        return None

    def print_summary(self):
        """چاپ خلاصه عملیات"""
        print("\n" + "="*60)
        print("📊 خلاصه عملیات وارد کردن داده")
        print("="*60)
        print(f"   👤 مشتریان: {self.stats['customers']}")
        print(f"   💳 تسهیلات: {self.stats['facilities']}")
        print(f"   🏠 املاک: {self.stats['properties']}")
        print(f"   👥 ضامنین: {self.stats['guarantors']}")
        print(f"   💰 سپرده‌ها: {self.stats['deposits']}")

        total = sum([
            self.stats['customers'],
            self.stats['facilities'],
            self.stats['properties'],
            self.stats['guarantors'],
            self.stats['deposits']
        ])
        print(f"\n   📈 مجموع رکوردها: {total}")

        if self.stats['errors']:
            print(f"\n   ⚠️ خطاها ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:5]:
                print(f"      - {err}")
            if len(self.stats['errors']) > 5:
                print(f"      ... و {len(self.stats['errors']) - 5} خطای دیگر")

        print("="*60 + "\n")


async def main():
    """تابع اصلی"""
    importer = DataImporter()
    await importer.run()


if __name__ == "__main__":
    asyncio.run(main())
