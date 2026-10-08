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

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
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

#: How long a claim on an urgent sheet is honoured before another run may take
#: it. Long enough for a real answer (the supervisor reads files, walks
#: dependencies, edits code), short enough that a crashed run does not park a
#: sheet for a day. A claim is a courtesy between runs, not a lock on the truth.
URGENT_CLAIM_TTL_S = 45 * 60


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
    #: v150 — THE PRECISE RECORD, by the owner's instruction: «مختصاتِ فوق‌العاده
    #: دقیقِ جایی که کادر کشیده شده و ابعاد». Document coordinates, the viewport
    #: and scroll they were taken under, the device pixel ratio, and — the part
    #: that actually survives — the anchor element's verified selector with the
    #: box stored as FRACTIONS of it, so the highlight follows the content when
    #: the layout moves instead of pointing at empty space.
    #:
    #: `rect_json`/`viewport_json` above are deliberately untouched: they are what
    #: v141 callers read, and this is an addition, not a replacement.
    geometry_json = Column(Text, default="")

    #: The conversation: a JSON list of notes (see `schemas/inspection.py`).
    notes_json = Column(Text, default="[]")
    #: What the supervisor found this sheet depends on — its own JSON list.
    #: The owner asked for this explicitly: «وقتی هر کاری بخواد بکنه وابستگی‌ها
    #: رو چک کنه». An answer with no dependency walk is an unreviewed answer.
    deps_json = Column(Text, default="[]")

    # --- v155: «همین الان برو سراغش» ------------------------------------
    #
    # The supervisor runs twice a week. A sheet the owner needs answered now
    # would otherwise wait up to four days, so they can put one at the front of
    # a separate, frequently-checked queue.
    #
    # THE FOUR FIELDS ARE FOUR DIFFERENT QUESTIONS, and merging any two of them
    # would break the queue:
    #   * `urgent_at`      — WHEN it was asked for. This is the sort key, so
    #                        «whichever I pressed first» is answered by the data
    #                        and not by whatever order a query happens to return.
    #   * `urgent_claimed_at` + `_by` — a run has TAKEN this one. A second run
    #                        skips it instead of doing the same work twice and
    #                        writing two contradictory answers to one sheet.
    #                        Time-stamped so a run that died mid-way releases it
    #                        (see `URGENT_CLAIM_TTL_S`) rather than wedging the
    #                        queue forever.
    #   * `urgent_done_at` — it has been dealt with. Kept rather than clearing
    #                        `urgent_at`, so the page can say «this one is done»
    #                        and the owner sees the result of what they asked for.
    urgent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    urgent_claimed_at = Column(DateTime(timezone=True), nullable=True)
    urgent_claimed_by = Column(String(80), default="")
    urgent_done_at = Column(DateTime(timezone=True), nullable=True)

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


class InspectionFile(Base):
    """v146 — ANY file attached to a sheet, and the proof the supervisor read it.

    WHY THIS IS NOT JUST «another shot» (owner, 2026-09-28)
    ------------------------------------------------------
    The owner asked to be able to hand the supervisor a *sample* rather than a
    screenshot: «یه نمونه غیرِ عکس … یا یه فرمتِ سند … نسخهٔ ورد یا پی‌دی‌افِ
    نمونه بهش بدم تا ایجاد کنه». So this accepts any type, up to 100 MB, and the
    supervisor must attend to THREE things together: the file's full content, the
    caption written about it, and the screenshot.

    THE LOAD-BEARING DESIGN DECISION
    --------------------------------
    The owner's last sentence is the requirement: «حجم هم باعث نشه ناظر نتونه
    بگه من نمیخونمش» — size must never become an excuse. A 100 MB PDF cannot be
    read as bytes by a reviewer, so the TEXT IS EXTRACTED AT UPLOAD TIME and kept
    here, and the reading endpoint serves it in slices while recording how far
    the supervisor got (`read_chars`). `add_note` then REFUSES a supervisor reply
    while any readable file is unread. «نمی‌خوانمش» stops being a choice.

    `extract_status` never collapses «nothing to read» into «I read nothing»:
    `unsupported`, `failed`, `empty` and `image` are distinct states, each with
    its reason in `extract_note`. That is the binding lesson from
    `experiences/a-monitor-must-distinguish-unmeasured-from-zero.md`.

    THE BYTES LIVE IN DRIVE, not in this row and not on the container disk: the
    container's filesystem is wiped on every deploy (OPEN_ITEMS #2), so a sample
    the owner uploaded would silently vanish. `store` records where they really
    are, so a reader is never guessing.
    """

    __tablename__ = "inspection_files"

    id = Column(String(40), primary_key=True)
    report_id = Column(String(40), index=True, nullable=False)
    #: The note this file was attached to (a sheet's conversation can grow files).
    note_id = Column(String(40), index=True, default="")
    uploaded_by = Column(String(80), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filename = Column(String(260), default="")
    mime = Column(String(120), default="application/octet-stream")
    byte_size = Column(Integer, default=0)
    sha256 = Column(String(64), default="")
    #: The owner's words about THIS file — «توضیح بدم» is part of the request.
    caption = Column(Text, default="")

    # --- where the bytes actually are -------------------------------------
    #: `drive` = durable · `local` = container disk, EPHEMERAL (lost on deploy)
    store = Column(String(12), default="")
    drive_id = Column(String(80), default="")
    drive_link = Column(String(400), default="")
    local_path = Column(String(400), default="")
    #: Why the durable store was not used, when it was not. Never silent.
    store_note = Column(Text, default="")

    # --- what the supervisor must read ------------------------------------
    #: ok · empty · unsupported · failed · image · pending — never merged
    extract_status = Column(String(12), default="pending")
    extract_note = Column(Text, default="")
    #: The extracted text. Served in slices, never in one response.
    text = Column(Text, default="")
    text_chars = Column(Integer, default=0)
    #: For a PDF: how many pages the text came from, so «all of it» is checkable.
    page_count = Column(Integer, default=0)
    #: True when the extraction stopped at a ceiling (character cap, or a PDF
    #: whose later pages had no text layer). Then the TEXT IS NOT THE WHOLE
    #: CONTENT, and reading all of it does not discharge the duty — the file
    #: itself must be opened too. Without this flag a truncated sample would
    #: report `fully_read` after the part we kept: a cap reported as a total.
    text_truncated = Column(Boolean, default=False)

    # --- the proof it was read --------------------------------------------
    #: The furthest character the reader has actually been served.
    read_chars = Column(Integer, default=0)
    read_at = Column(DateTime(timezone=True), nullable=True)
    read_by = Column(String(80), default="")
    #: An image has no text; looking at it is fetching the bytes. Recorded so the
    #: guard can demand it instead of waving images through.
    viewed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<InspectionFile({self.filename!r}, {self.byte_size}B, {self.extract_status})>"


#: The states in which a file HAS text that a reviewer is obliged to finish.
READABLE = ("ok",)
#: Extraction outcomes, and what each one means to a reader.
EXTRACT_LABEL = {
    "ok": "متن استخراج شد — ناظر باید کاملش را بخواند",
    "empty": "فایل باز شد ولی متنی نداشت",
    "unsupported": "برای این نوع، استخراجِ متن نداریم — ناظر باید خودِ فایل را باز کند",
    "failed": "استخراج شکست خورد — دلیلش ثبت شده",
    "image": "تصویر است — ناظر باید نگاهش کند (متنی برای خواندن ندارد)",
    "pending": "در صفِ رونویسی/استخراج — هنوز متن ندارد",
}


def file_read_debt(files: list) -> list:
    """Which attached files a supervisor still owes a read on, and how much.

    Returns one entry per unfinished file. An empty list is the only thing that
    lets a supervisor answer the sheet — see the guard in `routers/inspection`.

    Deliberately NOT «is read_chars > 0»: a reviewer that fetched the first slice
    of a 90-page sample and stopped has not read it. The debt is the remainder.
    """
    debt = []
    for f in files or []:
        status = str(getattr(f, "extract_status", "") or "")
        name = str(getattr(f, "filename", "") or "?")
        if status in READABLE:
            total = int(getattr(f, "text_chars", 0) or 0)
            got = int(getattr(f, "read_chars", 0) or 0)
            if total and got < total:
                debt.append({
                    "file_id": getattr(f, "id", ""), "filename": name,
                    "reason": "text", "read_chars": got, "text_chars": total,
                    "remaining": total - got,
                })
            elif getattr(f, "text_truncated", False) and getattr(f, "viewed_at", None) is None:
                # The text we kept is not the whole file, so finishing it is not
                # finishing the sample — the file itself still has to be opened.
                debt.append({
                    "file_id": getattr(f, "id", ""), "filename": name,
                    "reason": "truncated", "read_chars": got, "text_chars": total,
                    "remaining": 1,
                })
        elif status == "pending":
            # audio/video not transcribed yet: opening the bytes is not hearing
            # them — clears only once the full transcript exists and is read
            debt.append({
                "file_id": getattr(f, "id", ""), "filename": name,
                "reason": "pending", "read_chars": 0, "text_chars": 0,
                "remaining": 1,
            })
        elif status in ("image", "unsupported"):
            # No text to finish — but it must still have been OPENED, or the
            # sample the owner sent was never actually looked at.
            if getattr(f, "viewed_at", None) is None:
                debt.append({
                    "file_id": getattr(f, "id", ""), "filename": name,
                    "reason": "unopened", "read_chars": 0, "text_chars": 0,
                    "remaining": 1,
                })
    return debt


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
