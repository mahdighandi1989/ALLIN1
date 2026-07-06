"""Generic, first-class profile↔profile links (روابط بین مشتری‌ها).

The derived relationships (guarantor rows etc. via services.relationships) stay
as-is; this table adds EXPLICIT links for everything else — a letter that ties
two accounts together, an AI-extracted connection, a manual note — always with
the *kind* and the *exact recorded reason*, plus where it came from. Links are
directionless in meaning but stored once (account_no → related_account); the
relationships service surfaces them on BOTH profiles.
"""
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class CustomerLink(Base):
    __tablename__ = "customer_links"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    account_no = Column(String(50), index=True, nullable=False)
    related_account = Column(String(50), index=True, nullable=False)
    # e.g. guarantor | letter | co_signer | family | business_partner | other
    kind = Column(String(40), default="other", nullable=False)
    # The exact human-readable WHY («ضامن تسهیلات طبق نامه ۱۸۲/۴/۳۷۹»...) — required.
    reason = Column(Text, nullable=False)
    # Where it came from: manual | letter | letter_attachment_ai | import_ai | ...
    source = Column(String(40), default="manual")
    source_ref = Column(String(80))  # letter id / job id / ...
    created_by = Column(String(80))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)
