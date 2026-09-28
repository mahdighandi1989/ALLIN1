"""v141 — «نظارت و سرکشی»: the owner's own inspection rounds over the system's
screens, from what they saw to what the supervisor did about it.

WHY THIS EXISTS (owner, 2026-09-28): the owner walks the app, finds a fault or
has a suggestion, draws a box around it and files a sheet — instead of pasting a
screenshot into a chat every time. The weekly supervisor reads the sheets, does
the work, and writes the result back UNDER the sheet. The owner then looks,
ticks it, and the next round archives it.

THE THREE RULES THIS SHAPE ENFORCES — each one paid for in the sibling project
(`detective`, whose implementation this is modelled on; it is a read-only
reference and was not touched):

  1. **`status` is where the conversation is; `outcome` is what actually
     happened.** They used to be one field, and a supervisor that merely REPLIED
     («نشد», «رفت به صف») turned the sheet the same green as one that was really
     fixed. The owner's verdict on that: «برای همه نوشته انجام شده ولی هیچکدوم
     درست نشده». The colour the owner sees is derived from `outcome`, never from
     `status`.
  2. **A claim of «fixed» needs the picture that proves it.** `outcome='fixed'`
     without an after-shot is refused at the API. Being wrong about a fix is
     worse than being slow, because the owner stops looking at a green sheet.
  3. **Only the owner may tick.** In the sibling this was a written rule; here it
     is a GUARD — the supervisor's own account is refused by the approve
     endpoint, so the tick cannot be self-served even by mistake.

Screenshots live in their own table, so the list endpoint never ships megabytes
and a report row stays small.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base

# ---------------------------------------------------------------------------
# The life of a sheet — where it is in the conversation, NOT how it went.
# ---------------------------------------------------------------------------
STATUS_OPEN = "open"            # ثبت شد، منتظرِ ناظر
STATUS_ANSWERED = "answered"    # ناظر زیرش نوشت (هر جوابی، حتی «نشد»)
STATUS_APPROVED = "approved"    # مالک تیک زد
STATUS_FILED = "filed"          # بایگانی شد
STATUSES = (STATUS_OPEN, STATUS_ANSWERED, STATUS_APPROVED, STATUS_FILED)

STATUS_LABEL = {
    STATUS_OPEN: "در انتظارِ ناظر",
    STATUS_ANSWERED: "ناظر پاسخ داد",
    STATUS_APPROVED: "تأییدِ مالک",
    STATUS_FILED: "بایگانی‌شده",
}

# ---------------------------------------------------------------------------
# What ACTUALLY happened — the supervisor's verdict on its own work.
#
# There is deliberately NO value meaning «I think I fixed it». A supervisor that
# cannot show the after-picture writes `not-done`.
# ---------------------------------------------------------------------------
OUTCOME_FIXED = "fixed"
OUTCOME_PARTIAL = "partial"
OUTCOME_NEEDS_OWNER = "needs-owner"
OUTCOME_NOT_DONE = "not-done"
OUTCOMES = (OUTCOME_FIXED, OUTCOME_PARTIAL, OUTCOME_NEEDS_OWNER, OUTCOME_NOT_DONE)

OUTCOME_LABEL = {
    OUTCOME_FIXED: "✓ درست شد",
    OUTCOME_PARTIAL: "◑ نیمه‌کاره",
    OUTCOME_NEEDS_OWNER: "؟ منتظرِ انتخابِ مالک",
    OUTCOME_NOT_DONE: "✗ درست نشد",
}

OUTCOME_HINT = {
    OUTCOME_FIXED: "ناظر تغییر را انجام داد و بعدش خودش نگاه کرد — تصویرِ بعدش روی برگه است.",
    OUTCOME_PARTIAL: "بخشی از خواسته انجام شد؛ بقیه‌اش زیرِ همین برگه توضیح داده شده.",
    OUTCOME_NEEDS_OWNER: "خواسته با ساختار/منطقِ سامانه نمی‌خواند. گزینه‌ها نوشته شده — انتخاب با مالک است.",
    OUTCOME_NOT_DONE: "انجام نشد. دلیلش زیرِ همین برگه است. این برگه هنوز کارِ نکرده دارد.",
}

#: How many sheets one binder holds before a new one is started.
BINDER_CAPACITY = 40


class InspectionReport(Base):
    """One sheet: where the owner was, what they saw, and the conversation on it."""

    __tablename__ = "inspection_reports"

    id = Column(String(40), primary_key=True)
    #: Sequential, so the owner and the supervisor can say «گزارشِ ۷».
    number = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    status = Column(String(12), index=True, default=STATUS_OPEN, nullable=False)
    #: First line of the first note — the sheet's headline.
    title = Column(String(200), default="")
    created_by = Column(String(80), default="")

    # --- WHERE IN THE INTERFACE -------------------------------------------
    # A screen has no coordinates worth keeping — pixel positions change with
    # the window. What a supervisor needs is the way BACK.
    #: The page's route, e.g. `/customers`.
    page = Column(String(200), default="", index=True)
    page_label = Column(String(200), default="")
    #: The section inside it, when the surface marks one.
    section_id = Column(String(120), default="")
    section_label = Column(String(200), default="")
    #: THE load-bearing field: one string that puts the supervisor back here.
    reopen = Column(String(240), default="", index=True)
    #: The DOM path of what the rectangle covered — narrowest useful ancestor.
    dom_path = Column(String(400), default="")
    #: The text inside the rectangle — what the owner was actually looking at.
    covered_text = Column(Text, default="")
    #: The rectangle and the viewport it was measured in, as JSON.
    rect_json = Column(Text, default="")
    viewport_json = Column(Text, default="")

    #: The conversation: a JSON list of notes (see `schemas/inspection.py`).
    notes_json = Column(Text, default="[]")
    #: What the supervisor found this sheet depends on — its own JSON list.
    #: The owner asked for this explicitly: «وقتی هر کاری بخواد بکنه وابستگی‌ها
    #: رو چک کنه». An answer with no dependency walk is an unreviewed answer.
    deps_json = Column(Text, default="[]")

    #: Set when filed.
    binder_id = Column(String(40), default="")
    binder_number = Column(Integer, default=0)
    binder_page = Column(Integer, default=0)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<InspectionReport(number={self.number}, status='{self.status}')>"


class InspectionShot(Base):
    """A cropped image belonging to one note.

    Kept out of the report row on purpose: a list of sheets must not carry
    megabytes of base64, and a sheet with a long conversation must not grow a
    row the database has to rewrite on every reply.
    """

    __tablename__ = "inspection_shots"

    id = Column(String(40), primary_key=True)
    report_id = Column(String(40), index=True, nullable=False)
    #: The note this belongs to, and which side of it.
    note_id = Column(String(40), index=True, default="")
    #: `before` = what the owner saw · `after` = the supervisor's proof of a fix.
    kind = Column(String(10), default="before")
    mime = Column(String(40), default="image/jpeg")
    #: base64 payload WITHOUT the data-URL prefix.
    data = Column(Text, default="")
    byte_size = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InspectionBinder(Base):
    """A binder in the archive: where ticked sheets go to rest."""

    __tablename__ = "inspection_binders"

    id = Column(String(40), primary_key=True)
    number = Column(Integer, nullable=False)
    label = Column(String(120), default="")
    subtitle = Column(String(240), default="")
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    #: Report ids, oldest first, as JSON.
    report_ids_json = Column(Text, default="[]")


def sheet_glow(status: str, notes: list) -> dict:
    """THE COLOUR THE OWNER SEES — derived, never stored.

    A sheet is green only when the supervisor says it is fixed AND attached the
    picture that proves it. Everything else gets its own colour, because a wall
    of green sheets that means nothing is worse than no colour at all.

    `approved` wins over everything: that is the owner's own tick.
    """
    if status == STATUS_APPROVED:
        return {"key": STATUS_APPROVED, "label": STATUS_LABEL[STATUS_APPROVED], "tone": "approved"}
    if status == STATUS_FILED:
        return {"key": STATUS_FILED, "label": STATUS_LABEL[STATUS_FILED], "tone": "filed"}
    if status == STATUS_OPEN:
        return {"key": STATUS_OPEN, "label": STATUS_LABEL[STATUS_OPEN], "tone": "open"}

    last = next((n for n in reversed(notes or []) if n.get("by") == "reviewer"), None)
    outcome = (last or {}).get("outcome")
    if not outcome:
        # A reply from before outcomes existed. Not evidence of a fix.
        return {"key": "stale", "label": "پاسخِ قدیمی — بدونِ نتیجه", "tone": "stale"}
    if outcome == OUTCOME_FIXED and not (last or {}).get("after_shot_id"):
        # Proof, not word.
        return {"key": OUTCOME_PARTIAL, "label": "ادعای انجام، بدونِ تصویرِ بعدش",
                "tone": OUTCOME_PARTIAL, "outcome": OUTCOME_PARTIAL}
    return {"key": outcome, "label": OUTCOME_LABEL[outcome], "tone": outcome, "outcome": outcome}
