"""Guarantor model — guarantors and their security cheques per customer.

Merged from the legacy Excel CRM (Guarantors sheet). Linked to a customer by
``account_no`` (the system-wide key), so a customer's profile can list all of
their guarantors and security cheques.
"""
from sqlalchemy import Column, String, Numeric, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class Guarantor(Base):
    __tablename__ = "guarantors"

    # e.g. G-452861-20251211131154-75 (from the source system)
    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True, nullable=False)
    # Optional link to the specific facility this guarantor/cheque secures.
    facility_id = Column(String(60), index=True)
    branch = Column(String(20))
    customer_name = Column(String(200))
    guarantor_name = Column(String(200))
    guarantor_account = Column(String(50))
    national_id = Column(String(40))         # کد ملی ضامن
    cheque_no = Column(String(50))
    cheque_amount = Column(Numeric(15, 2))
    issuing_bank = Column(String(50))
    fd = Column(String(80))
    pim_ref = Column(String(80))
    seclist_row = Column(String(20))
    seclist_year = Column(String(10))
    date_added = Column(String(30))
    created_by = Column(String(80))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)
