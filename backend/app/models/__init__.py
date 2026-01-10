"""
Database Models Package
مدل‌های دیتابیس سیستم عملیات بانکی
طراحی جامع بر اساس تحلیل فایل‌های اکسل
"""
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.models.user import User, UserRole, UserSession
from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
from app.models.deposit import Deposit
from app.models.kyc import KYCRecord
from app.models.checklist import Checklist, ChecklistItem, ChecklistTask
from app.models.attachment import Attachment
from app.models.note import Note, PersonalNote, Reminder
from app.models.journal import JournalEntry
from app.models.settings import SystemSetting, UserSetting
from app.models.task import CustomTask, TaskStatus, TaskPriority
from app.models.security import Security, SecurityCategory, SecurityStatus

# New comprehensive models
from app.models.branch import Branch
from app.models.category import Category
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.partner import Partner
from app.models.property_valuation import PropertyValuation, PropertyInsurance
from app.models.security_record import SecurityRecord, SecurityRecordCategory

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",

    # Users
    "User",
    "UserRole",
    "UserSession",

    # Core Entities
    "Customer",
    "CustomerProfile",
    "AccountType",
    "CustomerStatus",

    # Organization
    "Branch",
    "Category",

    # Documents & Partners
    "Document",
    "DocumentType",
    "DocumentStatus",
    "Partner",

    # Facilities
    "Facility",
    "FacilityType",
    "FacilityStatus",

    # Guarantors
    "Guarantor",
    "GuarantorCheque",

    # Properties
    "Property",
    "PropertyLocation",
    "PropertyType",
    "PropertyStatus",
    "PropertyValuation",
    "PropertyInsurance",

    # Financial
    "Deposit",
    "Security",
    "SecurityCategory",
    "SecurityStatus",
    "SecurityRecord",
    "SecurityRecordCategory",

    # KYC & Compliance
    "KYCRecord",

    # Tasks & Workflow
    "Checklist",
    "ChecklistItem",
    "ChecklistTask",
    "CustomTask",
    "TaskStatus",
    "TaskPriority",

    # Documents & Files
    "Attachment",
    "Note",
    "PersonalNote",
    "Reminder",

    # System
    "JournalEntry",
    "SystemSetting",
    "UserSetting",
]
