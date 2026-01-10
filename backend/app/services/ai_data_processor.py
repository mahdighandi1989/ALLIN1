"""
AI-Powered Data Processor Service
سرویس پردازش داده با هوش مصنوعی
Analyzes uploaded files and merges data into database
"""
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import structlog

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.partner import Partner
from app.models.base import generate_uuid, generate_short_id

logger = structlog.get_logger()


def clean_str(value) -> Optional[str]:
    """Clean string value"""
    if pd.isna(value) or value is None:
        return None
    val = str(value).strip()
    return val if val and val.lower() not in ['nan', 'none', '', 'nat'] else None


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


def parse_amount(value) -> Optional[Decimal]:
    """Parse amount to Decimal"""
    if pd.isna(value) or value is None:
        return None
    value = str(value)
    value = re.sub(r'[^\d.]', '', value.replace(',', '').replace('/-', ''))
    try:
        return Decimal(value) if value else None
    except:
        return None


class AIDataProcessor:
    """
    AI-powered data processor that can:
    1. Analyze uploaded files (Excel, PDF, etc.)
    2. Extract structured data using AI
    3. Match data to existing customers
    4. Merge/update database records
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.customer_cache: Dict[str, str] = {}  # account_no -> customer_id
        self.stats = {
            "customers_updated": 0,
            "profiles_updated": 0,
            "documents_added": 0,
            "partners_added": 0,
            "facilities_added": 0,
            "guarantors_added": 0,
            "properties_added": 0,
            "errors": []
        }

    async def load_customer_cache(self):
        """Load existing customers into cache"""
        result = await self.db.execute(select(Customer))
        for customer in result.scalars().all():
            self.customer_cache[customer.account_no] = customer.id

    async def process_excel_file(self, file_path: Path) -> Dict[str, Any]:
        """Process an Excel file and extract all data"""
        logger.info(f"Processing Excel file: {file_path}")

        try:
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names
            logger.info(f"Found sheets: {sheets}")

            # Load customer cache first
            await self.load_customer_cache()

            # Process different sheet types
            for sheet in sheets:
                sheet_lower = sheet.lower()
                try:
                    df = pd.read_excel(xl, sheet_name=sheet)
                    df = df.dropna(how='all')

                    if 'customerprofile' in sheet_lower or 'customer profile' in sheet_lower:
                        await self._process_customer_profile_sheet(df)
                    elif 'profile' in sheet_lower and 'customer' not in sheet_lower:
                        await self._process_profile_sheet(df)
                    elif 'facilities' in sheet_lower or 'facility' in sheet_lower:
                        await self._process_facilities_sheet(df)
                    elif 'guarantor' in sheet_lower:
                        await self._process_guarantors_sheet(df)
                    elif 'journal' in sheet_lower:
                        await self._process_journal_sheet(df)
                    elif 'task' in sheet_lower:
                        await self._process_tasks_sheet(df)
                    elif 'note' in sheet_lower:
                        await self._process_notes_sheet(df)

                except Exception as e:
                    self.stats["errors"].append(f"Sheet {sheet}: {str(e)}")
                    logger.error(f"Error processing sheet {sheet}: {e}")

            await self.db.commit()
            return self.stats

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error processing file: {e}")
            raise

    async def _process_customer_profile_sheet(self, df: pd.DataFrame):
        """Process CustomerProfile sheet with 200 columns"""
        logger.info(f"Processing CustomerProfile sheet with {len(df)} rows")

        for _, row in df.iterrows():
            try:
                account_no = clean_str(row.get('AccountNo'))
                if not account_no:
                    continue

                customer_id = self.customer_cache.get(account_no)
                if not customer_id:
                    # Create new customer
                    customer = Customer(
                        id=generate_uuid(),
                        account_no=account_no,
                        customer_name=clean_str(row.get('CustomerName')) or 'Unknown',
                        branch=clean_str(row.get('Branch')),
                        account_type=AccountType.CORPORATE if clean_str(row.get('AccountType', '')).lower() == 'corporate' else AccountType.RETAIL,
                        status=CustomerStatus.ACTIVE,
                    )
                    self.db.add(customer)
                    customer_id = customer.id
                    self.customer_cache[account_no] = customer_id
                    self.stats["customers_updated"] += 1

                # Update or create profile
                result = await self.db.execute(
                    select(CustomerProfile).where(CustomerProfile.customer_id == customer_id)
                )
                profile = result.scalar_one_or_none()

                if not profile:
                    profile = CustomerProfile(
                        id=generate_uuid(),
                        customer_id=customer_id
                    )
                    self.db.add(profile)

                # Update profile fields
                profile.trade_license_no = clean_str(row.get('TradeLicenseNo')) or profile.trade_license_no
                profile.trade_license_issue_date = parse_date(row.get('TradeLicenseIssue')) or profile.trade_license_issue_date
                profile.trade_license_expiry_date = parse_date(row.get('TradeLicenseExpiry')) or profile.trade_license_expiry_date

                profile.passport_no = clean_str(row.get('PassportNo')) or profile.passport_no
                profile.passport_issue_date = parse_date(row.get('PassportIssue')) or profile.passport_issue_date
                profile.passport_expiry_date = parse_date(row.get('PassportExpiry')) or profile.passport_expiry_date
                profile.nationality = clean_str(row.get('PassportNationality')) or profile.nationality

                profile.emirates_id_no = clean_str(row.get('EmiratesIDNo')) or profile.emirates_id_no
                profile.emirates_id_issue_date = parse_date(row.get('EmiratesIDIssue')) or profile.emirates_id_issue_date
                profile.emirates_id_expiry_date = parse_date(row.get('EmiratesIDExpiry')) or profile.emirates_id_expiry_date

                profile.visa_no = clean_str(row.get('VisaNo')) or profile.visa_no
                profile.visa_issue_date = parse_date(row.get('VisaIssue')) or profile.visa_issue_date
                profile.visa_expiry_date = parse_date(row.get('VisaExpiry')) or profile.visa_expiry_date
                profile.visa_type = clean_str(row.get('VisaType')) or profile.visa_type

                profile.tenancy_no = clean_str(row.get('TenancyNo')) or profile.tenancy_no
                profile.tenancy_start_date = parse_date(row.get('TenancyIssue')) or profile.tenancy_start_date
                profile.tenancy_end_date = parse_date(row.get('TenancyExpiry')) or profile.tenancy_end_date

                # Securities info
                profile.underlien_aed = parse_amount(row.get('Sec_Underlien_AED')) or profile.underlien_aed
                profile.underlien_usd = parse_amount(row.get('Sec_Underlien_USD')) or profile.underlien_usd
                profile.collateral_aed = parse_amount(row.get('Sec_Collateral_AED')) or profile.collateral_aed

                # Undertakings
                profile.undertaking_127 = bool(row.get('Undertaking127')) if pd.notna(row.get('Undertaking127')) else profile.undertaking_127
                profile.personal_guarantee = bool(row.get('UndertakingFromGuarantors')) if pd.notna(row.get('UndertakingFromGuarantors')) else profile.personal_guarantee

                self.stats["profiles_updated"] += 1

                # Process Documents
                await self._create_documents_from_profile(customer_id, row)

                # Process Partners (up to 8)
                await self._create_partners_from_profile(customer_id, row)

                # Process Guarantors (up to 6)
                await self._create_guarantors_from_profile(customer_id, row)

                # Process Facilities
                await self._create_facilities_from_profile(customer_id, row)

            except Exception as e:
                self.stats["errors"].append(f"Profile row error: {str(e)}")
                logger.error(f"Error processing profile row: {e}")

    async def _create_documents_from_profile(self, customer_id: str, row: pd.Series):
        """Create Document records from profile data"""
        doc_mappings = [
            ('TradeLicenseNo', 'TradeLicenseIssue', 'TradeLicenseExpiry', 'TradeLicenseRemarks', DocumentType.TradeLicense),
            ('PassportNo', 'PassportIssue', 'PassportExpiry', 'PassportRemarks', DocumentType.Passport),
            ('EmiratesIDNo', 'EmiratesIDIssue', 'EmiratesIDExpiry', 'EmiratesIDRemarks', DocumentType.EmiratesID),
            ('VisaNo', 'VisaIssue', 'VisaExpiry', None, DocumentType.Visa),
            ('TenancyNo', 'TenancyIssue', 'TenancyExpiry', 'TenancyAddress', DocumentType.Tenancy),
        ]

        for no_col, issue_col, expiry_col, remarks_col, doc_type in doc_mappings:
            doc_no = clean_str(row.get(no_col))
            if doc_no:
                # Check if document already exists
                result = await self.db.execute(
                    select(Document).where(
                        Document.customer_id == customer_id,
                        Document.document_type == doc_type
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.document_no = doc_no
                    existing.issue_date = parse_date(row.get(issue_col)) or existing.issue_date
                    existing.expiry_date = parse_date(row.get(expiry_col)) or existing.expiry_date
                    if remarks_col:
                        existing.remarks = clean_str(row.get(remarks_col)) or existing.remarks
                else:
                    # Create new
                    doc = Document(
                        id=generate_short_id("DOC-"),
                        customer_id=customer_id,
                        document_type=doc_type,
                        document_no=doc_no,
                        issue_date=parse_date(row.get(issue_col)),
                        expiry_date=parse_date(row.get(expiry_col)),
                        remarks=clean_str(row.get(remarks_col)) if remarks_col else None,
                        status=DocumentStatus.ACTIVE,
                    )
                    self.db.add(doc)
                    self.stats["documents_added"] += 1

    async def _create_partners_from_profile(self, customer_id: str, row: pd.Series):
        """Create Partner records from profile data"""
        for i in range(1, 9):  # Partner1 to Partner8
            name = clean_str(row.get(f'Partner{i}Name'))
            if name:
                # Check if partner already exists
                result = await self.db.execute(
                    select(Partner).where(
                        Partner.customer_id == customer_id,
                        Partner.partner_name == name
                    )
                )
                if not result.scalar_one_or_none():
                    share = row.get(f'Partner{i}Share')
                    partner = Partner(
                        id=generate_short_id("PTR-"),
                        customer_id=customer_id,
                        partner_name=name,
                        nationality=clean_str(row.get(f'Partner{i}Nationality')),
                        share_percent=Decimal(str(share)) if pd.notna(share) else None,
                        order_no=i,
                    )
                    self.db.add(partner)
                    self.stats["partners_added"] += 1

    async def _create_guarantors_from_profile(self, customer_id: str, row: pd.Series):
        """Create Guarantor records from profile data"""
        for i in range(1, 7):  # Guarantor1 to Guarantor6
            name = clean_str(row.get(f'Guarantor{i}_Name'))
            if name:
                # Check if guarantor already exists
                result = await self.db.execute(
                    select(Guarantor).where(
                        Guarantor.customer_id == customer_id,
                        Guarantor.guarantor_name == name
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    guarantor = Guarantor(
                        id=generate_short_id("GNT-"),
                        customer_id=customer_id,
                        guarantor_name=name,
                        phone=clean_str(row.get(f'Guarantor{i}_Account')),
                    )
                    self.db.add(guarantor)
                    self.stats["guarantors_added"] += 1

                    # Add cheque if available
                    cheque_no = clean_str(row.get(f'Guarantor{i}_ChqNo'))
                    if cheque_no:
                        cheque = GuarantorCheque(
                            id=generate_short_id("CHQ-"),
                            guarantor_id=guarantor.id,
                            cheque_no=cheque_no,
                            amount=parse_amount(row.get(f'Guarantor{i}_ChqAmount')),
                            currency="AED",
                        )
                        self.db.add(cheque)

    async def _create_facilities_from_profile(self, customer_id: str, row: pd.Series):
        """Create Facility records from profile data"""
        facility_types = [
            ('OD', FacilityType.OD, ['OD_Amount', 'OD_Rate', 'OD_ApprovalDate', 'OD_Expiry', 'OD_FacilityID']),
            ('Loan', FacilityType.LOAN, ['Loan_Amount', 'Loan_Rate', 'Loan_ApprovalDate', 'Loan_Maturity', 'Loan_FacilityID']),
            ('LG', FacilityType.LG, ['LG_Amount', 'LG_Rate', None, 'LG_Expiry', 'LG_FacilityID']),
            ('TR', FacilityType.TR, ['TR_Amount', 'TR_Rate', None, 'TR_Expiry', 'TR_FacilityID']),
            ('LC', FacilityType.LC, ['LC_Sight_Amount', 'LC_Sight_Margin', None, 'LC_Sight_Expiry', 'LC_Sight_FacilityID']),
        ]

        for fac_name, fac_type, columns in facility_types:
            amount_col, rate_col, approval_col, expiry_col, id_col = columns
            amount = parse_amount(row.get(amount_col))

            if amount and amount > 0:
                # Check if facility already exists
                fac_id = clean_str(row.get(id_col)) if id_col else None

                if fac_id:
                    result = await self.db.execute(
                        select(Facility).where(Facility.id == fac_id)
                    )
                    if result.scalar_one_or_none():
                        continue  # Already exists

                facility = Facility(
                    id=fac_id or generate_short_id("FAC-"),
                    customer_id=customer_id,
                    facility_type=fac_type,
                    facility_name=fac_name,
                    approved_amount=amount,
                    status=FacilityStatus.ACTIVE,
                    sanction_date=parse_date(row.get(approval_col)) if approval_col else None,
                    maturity_date=parse_date(row.get(expiry_col)) if expiry_col else None,
                    currency="AED",
                )
                self.db.add(facility)
                self.stats["facilities_added"] += 1

    async def _process_profile_sheet(self, df: pd.DataFrame):
        """Process Profile sheet (summary view)"""
        logger.info(f"Processing Profile sheet with {len(df)} rows")
        # This sheet has summary info - mostly already covered

    async def _process_facilities_sheet(self, df: pd.DataFrame):
        """Process Facilities sheet"""
        logger.info(f"Processing Facilities sheet with {len(df)} rows")

        for _, row in df.iterrows():
            try:
                account_no = clean_str(str(int(row.get('AccountNo', 0)))) if pd.notna(row.get('AccountNo')) else None
                if not account_no:
                    continue

                customer_id = self.customer_cache.get(account_no)
                if not customer_id:
                    continue

                fac_id = clean_str(row.get('FacilityID'))
                if fac_id:
                    result = await self.db.execute(
                        select(Facility).where(Facility.id == fac_id)
                    )
                    if result.scalar_one_or_none():
                        continue  # Already exists

                ftype = clean_str(row.get('FacilityType')) or ''
                ftype_lower = ftype.lower()
                if 'overdraft' in ftype_lower or 'od' in ftype_lower:
                    facility_type = FacilityType.OD
                elif 'loan' in ftype_lower:
                    facility_type = FacilityType.LOAN
                elif 'lg' in ftype_lower:
                    facility_type = FacilityType.LG
                elif 'lc' in ftype_lower:
                    facility_type = FacilityType.LC
                elif 'tr' in ftype_lower:
                    facility_type = FacilityType.TR
                else:
                    facility_type = FacilityType.OTHER

                facility = Facility(
                    id=fac_id or generate_short_id("FAC-"),
                    customer_id=customer_id,
                    facility_type=facility_type,
                    facility_name=clean_str(row.get('FacilityNo')),
                    reference_no=clean_str(row.get('FacilityNo')),
                    approved_amount=parse_amount(row.get('Amount')) or Decimal('0'),
                    currency=clean_str(row.get('Currency')) or 'AED',
                    sanction_date=parse_date(row.get('ApprovalDate')),
                    status=FacilityStatus.ACTIVE if row.get('IsActive', 1) == 1 else FacilityStatus.CLOSED,
                    notes=clean_str(row.get('Notes')),
                )
                self.db.add(facility)
                self.stats["facilities_added"] += 1

            except Exception as e:
                self.stats["errors"].append(f"Facility row: {str(e)}")

    async def _process_guarantors_sheet(self, df: pd.DataFrame):
        """Process Guarantors sheet"""
        logger.info(f"Processing Guarantors sheet with {len(df)} rows")

        for _, row in df.iterrows():
            try:
                account_no = clean_str(str(int(row.get('AccountNo', 0)))) if pd.notna(row.get('AccountNo')) else None
                if not account_no:
                    continue

                customer_id = self.customer_cache.get(account_no)
                if not customer_id:
                    continue

                gnt_id = clean_str(row.get('GuarantorID'))
                if gnt_id:
                    result = await self.db.execute(
                        select(Guarantor).where(Guarantor.id == gnt_id)
                    )
                    if result.scalar_one_or_none():
                        continue

                name = clean_str(row.get('GuarantorName'))
                if not name:
                    continue

                guarantor = Guarantor(
                    id=gnt_id or generate_short_id("GNT-"),
                    customer_id=customer_id,
                    guarantor_name=name,
                    phone=clean_str(row.get('GuarantorAccount')),
                )
                self.db.add(guarantor)
                self.stats["guarantors_added"] += 1

                cheque_no = clean_str(row.get('ChequeNo'))
                if cheque_no:
                    cheque = GuarantorCheque(
                        id=generate_short_id("CHQ-"),
                        guarantor_id=guarantor.id,
                        cheque_no=cheque_no,
                        bank_name=clean_str(row.get('IssuingBank')),
                        amount=parse_amount(row.get('ChequeAmount')),
                        currency="AED",
                    )
                    self.db.add(cheque)

            except Exception as e:
                self.stats["errors"].append(f"Guarantor row: {str(e)}")

    async def _process_journal_sheet(self, df: pd.DataFrame):
        """Process Journal sheet"""
        pass  # Already handled in main import

    async def _process_tasks_sheet(self, df: pd.DataFrame):
        """Process Tasks sheet"""
        pass  # Already handled in main import

    async def _process_notes_sheet(self, df: pd.DataFrame):
        """Process Notes sheet"""
        pass  # Already handled in main import


async def enhance_data_from_excel(db: AsyncSession, file_path: Path) -> Dict[str, Any]:
    """
    Enhance existing data with more information from Excel files
    This is called to add MORE data without deleting existing
    """
    processor = AIDataProcessor(db)
    return await processor.process_excel_file(file_path)
