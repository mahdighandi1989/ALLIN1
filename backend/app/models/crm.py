"""CRM entities merged from the legacy Excel system, all keyed by ``account_no``.

These extend the customer into a full "credit file":
  * CustomerProfile     — the comprehensive profile (identity + KYC docs with
                          expiry + the full 200-field record kept in data_json).
  * ChecklistProgress   — the 9-step credit-file workflow status per customer.
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    account_no = Column(String(50), primary_key=True)
    customer_name = Column(String(200))
    account_type = Column(String(30))
    branch = Column(String(20))
    business_type = Column(String(200))
    rating = Column(String(10))
    customer_status = Column(String(50))
    # KYC documents — number + expiry (for the KYC panel and expiry alerts).
    trade_license_no = Column(String(80))
    trade_license_expiry = Column(String(30))
    passport_no = Column(String(80))
    passport_expiry = Column(String(30))
    emirates_id_no = Column(String(80))
    emirates_id_expiry = Column(String(30))
    visa_no = Column(String(80))
    visa_expiry = Column(String(30))
    tenancy_no = Column(String(80))
    tenancy_expiry = Column(String(30))
    profile_completeness = Column(String(20))
    updated_by = Column(String(80))
    last_updated = Column(String(30))
    # Full 200-field record verbatim (partners, securities, collateral, mortgage,
    # guarantors summary, undertakings, attachments, …) so nothing is lost.
    data_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# The 9 workflow steps (item1..item9), in order:
CHECKLIST_STEPS = [
    "Offer Letter", "Document Verification", "Document Scanning", "Add to Table",
    "Central Folder Upload", "Regulatory Document (Contra)", "K.Y.C", "Summary", "Archive",
]


class ChecklistProgress(Base):
    __tablename__ = "checklist_progress"

    account_no = Column(String(50), primary_key=True)
    branch = Column(String(20))
    account_name = Column(String(200))
    category = Column(String(40))
    first_action = Column(String(30))
    last_action = Column(String(30))
    total = Column(String(10))
    item1 = Column(String(10))
    item2 = Column(String(10))
    item3 = Column(String(10))
    item4 = Column(String(10))
    item5 = Column(String(10))
    item6 = Column(String(10))
    item7 = Column(String(10))
    item8 = Column(String(10))
    item9 = Column(String(10))
    last_user = Column(String(80))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CustomTask(Base):
    """Follow-up tasks per customer/facility."""
    __tablename__ = "custom_tasks"

    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True)
    facility_id = Column(String(60))
    task_name = Column(String(200))
    status = Column(String(30))
    followup_date = Column(String(30))
    notes = Column(Text)
    priority = Column(String(20))
    created_by = Column(String(80))
    created_date = Column(String(30))
    completed_date = Column(String(30))
    is_active = Column(String(5))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Attachment(Base):
    """Document attachments per customer/facility (metadata; files live on the
    bank's S: share, so only the metadata is mirrored here)."""
    __tablename__ = "attachments"

    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True)
    facility_id = Column(String(60))
    row_index = Column(String(10))
    file_name = Column(String(255))
    original_name = Column(String(255))
    file_path = Column(Text)
    file_size = Column(String(20))
    upload_date = Column(String(30))
    uploaded_by = Column(String(80))
    is_shared = Column(String(10))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JournalEntry(Base):
    """Per-customer activity log (who did what / which workflow step)."""
    __tablename__ = "journal_entries"

    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True)
    branch = Column(String(20))
    account_name = Column(String(200))
    category = Column(String(40))
    item = Column(String(100))
    status = Column(String(20))
    date = Column(String(30))
    time = Column(String(20))
    user = Column(String(80))
    priority = Column(String(20))
    notes = Column(Text)
    source = Column(String(60))
    action = Column(String(60))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
