"""گزارش خلاصهٔ پروندهٔ حقوقی — the legal case-file summary report.

The branch sends the Legal & Debt-Recovery department a comprehensive report on a
non-performing account: how the company was formed, what it was lent, when the
account went stagnant and was classified, what the books and the court say it owes,
what has been collected and from whom, what collateral is held and what was done
with it, which committees approved what, and where the judgment stands.

Storage follows this repository's existing form-backed-document pattern
(``CreditReview``): one row per report, SCALAR columns for everything scalar and a
``*_json`` column per repeating table. Amounts are stored VERBATIM as text because
the source documents use bank-Persian formatting that carries meaning and must
print back byte-identical («95/22.645 درهم», «-/312,240»); the three headline
figures additionally get a parsed numeric mirror so the register can be summed and
sorted without digging through text — the same verbatim + ``*_num`` pairing
``Security.cheque_amount``/``cheque_amount_num`` already uses.

A report is stored either UNDER a customer account (``account_no`` set) or as a
GENERAL report (no account), exactly like ``Letter`` — so the same two entrances the
owner knows from «نامهٔ حساب/مشتری» and «نامهٔ عمومی» work here too.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


def generate_case_report_id() -> str:
    return uuid.uuid4().hex


class CaseReport(Base):
    __tablename__ = "case_reports"

    id = Column(String(32), primary_key=True, default=generate_case_report_id)
    account_no = Column(String(50), index=True)                    # blank/None → general
    category = Column(String(20), default="account", index=True)   # account | general
    title = Column(String(255))

    # ── header (سربرگ: تاریخ / شماره / طبقه‌بندی / گیرنده / موضوع) ──────────────
    letter_date = Column(String(30))            # «تاریخ: 02/10/2025» — as printed
    letter_no = Column(String(80))              # «شماره: 2025/734/2900/182»
    classification = Column(String(40))         # داخلی / عادی / محرمانه / خیلی محرمانه
    recipient_name = Column(String(200))        # جناب آقای …
    recipient_title = Column(String(300))       # ریاست محترم دایرهٔ حقوقی و پیگیری وصول مطالبات
    subject = Column(String(500))               # the whole «موضوع» line, as printed
    subject_entity = Column(String(300))        # موسسه AGHA TRADING FZE
    subject_account = Column(String(50), index=True)
    subject_branch = Column(String(100))

    # ── the two letters this report answers («عطف به نامهٔ …، وفق مفاد نامهٔ …») ──
    ref_letter_no = Column(String(80))
    ref_letter_date = Column(String(30))
    ref_letter_dept = Column(String(300))
    basis_letter_no = Column(String(80))
    basis_letter_date = Column(String(30))

    # ── ۱) خلاصهٔ وضعیت شرکت ─────────────────────────────────────────────────
    company_name = Column(String(300))
    established_year = Column(String(10))
    licence_no = Column(String(60))
    free_zone = Column(String(120))
    activity = Column(String(300))
    is_active = Column(String(20))              # فعال / غیرفعال — text, not bool: the
                                                # source says «هم اکنون غیر فعال می‌باشد»
    manager_name = Column(String(200))
    account_open_date = Column(String(30))
    first_facility_year = Column(String(10))
    company_summary = Column(Text)              # the narrative paragraph, editable as written
    partners_json = Column(Text)                # [{name, national_id, share, role}]

    # ── ۲/۳) تسهیلات: آخرین اعطایی، و تسویه‌نشده (مطالباتی) ────────────────────
    facilities_granted_json = Column(Text)      # [{type, amount, grant_date, rate}]
    facilities_unsettled_json = Column(Text)    # [{type, principal, grant_date, rate}]

    # ── ۴) وضعیت رکود و طبقه‌بندی حساب ───────────────────────────────────────
    stagnation_date = Column(String(30))
    stagnation_balance = Column(String(60))
    classification_date = Column(String(30))
    classification_balance = Column(String(60))
    stagnation_note = Column(Text)              # «تاریخ رکود به‌طور سیستماتیک نبوده…»

    # ── ۵) مانده بدهی طبق دفاتر بانک ─────────────────────────────────────────
    offbalance_date = Column(String(30))        # «به زیر خط ترازنامه انتقال یافته است»
    books_note = Column(Text)
    books_principal = Column(String(60))        # اصل بدهی (+ سود قبل از طبقه‌بندی)
    books_overdue_interest = Column(String(60)) # سود معوق و جرایم تأخیر
    books_aed_costs = Column(String(60))        # هزینه‌های درهمی
    books_total = Column(String(60))
    # No ``default=0`` on the three *_num mirrors, deliberately: a column default
    # fires on INSERT whenever the attribute is NULL, which would turn «could not
    # read this amount» into «this amount is zero» and quietly under-report the
    # bank's own claim. NULL means unparsed; 0 means genuinely nothing.
    books_total_num = Column(Numeric(18, 2))
    books_provisions = Column(String(60))       # ذخایر
    books_irr_costs = Column(String(60))        # هزینه‌های ریالی

    # ── ۵-ب) مانده بدهی طبق حکم دادگاه ───────────────────────────────────────
    court_principal = Column(String(60))
    court_interest = Column(String(60))
    court_interest_rate = Column(String(20))    # «10 %»
    court_interest_from = Column(String(30))    # «از تاریخ 20/10/2019»
    court_legal_costs = Column(String(60))
    court_collected = Column(String(60))
    court_total = Column(String(60))
    court_total_num = Column(Numeric(18, 2))

    # ── ۶) مبالغ دریافتی از مدیونین/ضامنین (از تاریخ رکود) ───────────────────
    collections_json = Column(Text)             # [{date, amount, currency, source,
                                                #   principal, interest, legal_cost}]
    collections_total = Column(String(60))
    collections_total_num = Column(Numeric(18, 2))

    # ── ۷) وثایق و پشتوانه‌های مأخوذه ────────────────────────────────────────
    collaterals_json = Column(Text)             # [{type, reference_no, amount}]

    # ── ۸) مصوبات · اقدامات روی وثایق · چک‌های تنزیل‌شده ─────────────────────
    approvals_json = Column(Text)               # [{authority, date, subject, result}]
    collateral_actions_json = Column(Text)      # [{type, amount, actions}]
    discounted_cheques_json = Column(Text)      # [{row, cheque_no, beneficiary,
                                                #   drawer, bank, amount}]

    # ── ۹) تعهدات مستقیم و غیرمستقیم ─────────────────────────────────────────
    commitments_json = Column(Text)             # [{subject, description, amount}]
    commitments_note = Column(Text)

    # ── ۱۰) مشخصات حکم ───────────────────────────────────────────────────────
    judgment_action_date = Column(String(30))
    judgment_final_date = Column(String(30))
    judgment_sent_iran_date = Column(String(30))

    # ── ۱۱) سایر توضیحات + پانویس ────────────────────────────────────────────
    other_notes = Column(Text)
    branch_name = Column(String(120))
    branch_code = Column(String(20))
    prepared_by = Column(String(120))           # «اقدام کننده: …»

    # Per-report presentation freedom — identical in role to Letter's three: edits to
    # fields/positions/labels belong to THIS report, never to the master template.
    values_json = Column(Text)
    layout_json = Column(Text)
    labels_json = Column(Text)

    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(80))
    updated_by = Column(String(80))

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        who = self.account_no or "general"
        return f"<CaseReport(id='{self.id}', account='{who}', title='{self.title}')>"
