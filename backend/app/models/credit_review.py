"""Credit-committee review / approval (مصوبه) — a first-class record so the data
captured on the sanction form (and parsed from drafts) is queryable and
reportable, not just buried in the profile JSON blob.

One row per (account, review date) — re-saving the same review updates in place
(no duplicates), a new review date adds a row (history). The free-form matrices
(limit structure, financials, reciprocity, guarantors, other banks) are kept as
JSON so the structure stays faithful to the Word template without a column
explosion; the headline scalars are real columns for filtering/reporting.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


def _rid() -> str:
    return "CR" + uuid.uuid4().hex[:10].upper()


class CreditReview(Base):
    __tablename__ = "credit_reviews"

    id = Column(String(14), primary_key=True, default=_rid)
    account_no = Column(String(50), index=True, nullable=False)
    customer_name = Column(String(200))
    account_type = Column(String(30))
    branch = Column(String(60))
    borrower_type = Column(String(60))
    request_type = Column(String(60))
    date_of_review = Column(String(30), index=True)
    credit_application_no = Column(String(80))
    business_activity = Column(String(200))
    existing_rating = Column(String(20))
    proposed_rating = Column(String(20))
    rating_notes = Column(Text)
    relationship_date = Column(String(30))
    established_since = Column(String(30))
    ca_expiry_existing = Column(String(120))
    ca_expiry_proposed = Column(String(120))
    purpose = Column(Text)
    major_changes = Column(Text)
    background = Column(Text)
    pep = Column(String(120))
    account_conduct = Column(Text)
    aecb_score = Column(String(20))
    cru_findings = Column(Text)
    cru_recommendation = Column(Text)
    monthly_salary = Column(String(40))
    auditor = Column(String(120))
    proposed_facility = Column(String(80))
    proposed_amount = Column(String(40))
    proposed_tenor = Column(String(40))
    proposed_rate = Column(String(40))
    # Faithful matrices, kept verbatim as JSON-encoded text.
    limits_json = Column(Text)
    recip_json = Column(Text)
    fin_json = Column(Text)
    guarantors_json = Column(Text)
    banks_json = Column(Text)
    source = Column(String(30))  # "sanction_form" | "draft_extract"
    created_by = Column(String(80))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<CreditReview {self.id} acc={self.account_no} review={self.date_of_review}>"
