"""The multi-year Securities List register (cheques / FDs / collateral held).

Imported verbatim from the yearly ``Securities_List_*.xlsx`` workbooks (Retail +
Corporate sheets). This is the full historical register that the Excel tool's
ConnectToSecuritiesList / SyncGuarantorsFromSecuritiesList read from; here it is
a first-class table, linked to each account by ``account_no`` so a customer's
complete securities history shows on their credit file.
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, Index
from sqlalchemy.sql import func

from app.database import Base


class Security(Base):
    __tablename__ = "securities"

    id = Column(String(40), primary_key=True)          # stable SEC-{year}-{seg}-{n}
    year = Column(String(8), index=True)
    segment = Column(String(20))                        # retail / corporate
    date = Column(String(30))                           # entry date (text — years vary)
    seq_no = Column(String(10))
    branch = Column(String(20))
    account_no = Column(String(50), index=True)
    customer_name = Column(String(200))
    fd = Column(String(200))
    guarantor = Column(Text)
    cheque_no = Column(Text)                            # may list several cheques
    issuing_bank = Column(Text)
    cheque_amount = Column(Text)                        # verbatim ("Each chq. AED: 60,000/-")
    cheque_amount_num = Column(Numeric(18, 2), default=0)  # parsed total for aggregation
    undertaking = Column(String(40))                    # Available / -
    guarantee = Column(String(40))
    credit_facility = Column(String(40))
    original_offer = Column(String(40))
    property_no = Column(Text)
    mortgage_aed = Column(String(60))
    remarks = Column(Text)
    stored_date = Column(String(30))
    taken_out_date = Column(String(30))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Speeds up the per-account history lookup on the customer file.
Index("ix_securities_acc_year", Security.account_no, Security.year)
