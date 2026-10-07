"""v146 — attachments on «نظارت و سرکشی» sheets: store them, and make them READ.

WHAT THE OWNER ASKED FOR (2026-09-28)
-------------------------------------
    «باید بشه فایل هم اپلود کرد … هر نوع فایلی … حجمِ هر فایل بتونه تا ۵۰ مگ یا
    ۱۰۰ مگ هم باشه و ناظر بتونه کامل بخونتش … و حجم هم باعث نشه ناظر نتونه بگه
    من نمیخونمش»

Three requirements, and the third is the one that shapes the module:

  1. **Any type.** A sample of a document format (Word/PDF), a picture pulled off
     the web, a spreadsheet — not only cropped screenshots.
  2. **Up to 100 MB**, which rules out holding the bytes in memory or in a table
     row, and rules out the container disk as the real home (it is wiped on every
     deploy — OPEN_ITEMS #2). Drive is the durable store.
  3. **Size must never become an excuse not to read it.** So the text is pulled
     out ONCE, here, at upload time. The reviewer then reads text in slices, and
     the router records how far it got. Nobody has to open a 100 MB file to
     answer the sheet, so «نمی‌خوانمش» has no remaining justification.

WHAT THIS MODULE REFUSES TO DO
------------------------------
It never reports «no text» when it means «I could not try». `unsupported`,
`failed`, `empty` and `image` are four different answers, each carrying its
reason in Persian, because a reader who cannot tell them apart will treat all
four as «nothing to see» — the exact failure recorded in
`experiences/a-monitor-must-distinguish-unmeasured-from-zero.md` and again in
`experiences/a-cap-is-not-a-total.md`.
"""
from __future__ import annotations

import hashlib
import io
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger("app.inspection_files")

#: The ceiling the owner named. 100 MB by default; an operator may lower it.
MAX_MB = int(os.getenv("INSPECTION_MAX_FILE_MB", "100"))
MAX_BYTES = MAX_MB * 1024 * 1024

#: How much extracted text one file may keep. A real document sample never comes
#: close — 20 million characters is on the order of 6,000 pages — so this only
#: catches a pathological dump. Raised from 4M once a 60 MB text file showed that
#: the lower cap turned a complete read into a 6% one.
#:
#: HITTING IT IS NOT A SILENT TRUNCATION. `extract` returns `truncated: True`,
#: which becomes read DEBT: the reviewer must finish the text AND open the file
#: itself, because the text is no longer all of the content. Without that, a
#: truncated file would report `fully_read` after the part we kept — a cap
#: reported as a total, the exact fault v144 had to fix in the data-quality
#: reports (`experiences/a-cap-is-not-a-total.md`).
MAX_TEXT_CHARS = int(os.getenv("INSPECTION_MAX_TEXT_CHARS", str(20_000_000)))

#: One slice of text a reader is served at a time, when it does not say.
#:
#: Measured, not guessed: at 40,000 a 20-million-character sample needed 500
#: round trips, each with its own commit, and the supervisor's pull crawled. The
#: reading duty is only fair if reading is cheap, so the default slice is large
#: and a caller may ask for more (bounded by `MAX_SLICE_CHARS`). A reader that
#: wants small pieces still passes its own `limit`.
SLICE_CHARS = int(os.getenv("INSPECTION_SLICE_CHARS", "400000"))
#: The largest slice one request may ask for. Caps the response, not the reading.
MAX_SLICE_CHARS = int(os.getenv("INSPECTION_MAX_SLICE_CHARS", "2000000"))

#: Where the bytes go in Drive — one folder per SHEET, under a category folder,
#: matching the taxonomy the rest of the app already uses (`["backups",
#: "database"]`, `["attachments", "cust-…", "fac-…"]`). `ensure_folder_path`
#: creates whatever is missing and is idempotent, so the owner gets
#: `inspection/report-7/` without anyone making it by hand.
#:
#: The file keeps its ORIGINAL NAME (with a short content hash in front, so two
#: samples called «نمونه.docx» can coexist). This deliberately does NOT use
#: `drive_sync.build_name`: that scheme names artefacts the SYSTEM generates, and
#: its machine-readable form would hand the owner a folder of unrecognisable
#: filenames. A sample is the owner's own document — they have to find it again.
DRIVE_ROOT = "inspection"

_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff",
              ".svg", ".heic", ".heif", ".avif")
_TEXTY_EXT = (".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".yaml", ".yml",
              ".xml", ".html", ".htm", ".log", ".ini", ".cfg", ".toml", ".sql",
              ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".sh", ".bat", ".rst")


def safe_filename(name: str) -> str:
    """A filename safe for Drive and for a URL, keeping it recognisable.

    Non-ASCII is KEPT — the owner's files have Persian names and stripping them
    would hand the supervisor «file1.pdf» with no idea what it was.
    """
    name = (name or "").strip().replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\r\n\t]", "", name)
    name = re.sub(r'[<>:"|?*]', "_", name).strip(" .")
    return (name or "file")[:200]


def human_size(n: int) -> str:
    n = int(n or 0)
    for unit in ("بایت", "کیلوبایت", "مگابایت", "گیگابایت"):
        if n < 1024 or unit == "گیگابایت":
            return f"{n:.0f} {unit}" if unit == "بایت" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} گیگابایت"


# ---------------------------------------------------------------------------
# Text extraction — one function per family, all returning the same triple.
# ---------------------------------------------------------------------------
def _pdf_text(data: bytes) -> tuple[str, int, int]:
    """Text per page, the page count, and HOW MANY PAGES ACTUALLY HAD TEXT.

    That third number is load-bearing. The page markers below are themselves
    text, so a scanned PDF with no text layer would come back «non-empty» and be
    filed as readable — and a reviewer would dutifully read forty characters of
    «--- page 3 ---» and believe it had read the document. The caller decides
    `ok` vs `unsupported` from the count of pages with real content, never from
    whether the assembled string is blank.
    """
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    with_text = 0
    for i, page in enumerate(reader.pages, start=1):
        try:
            t = page.extract_text() or ""
        except Exception as exc:  # one broken page must not lose the rest
            t = f"[صفحهٔ {i} خوانده نشد: {type(exc).__name__}]"
        if t.strip():
            with_text += 1
        # The page number travels WITH the text: a reviewer quoting the sample
        # can say where it came from, and «all of it» becomes checkable.
        parts.append(f"\n--- صفحهٔ {i} ---\n{t}")
        if sum(len(p) for p in parts) > MAX_TEXT_CHARS:
            parts.append(f"\n[استخراج در صفحهٔ {i} به سقفِ {MAX_TEXT_CHARS} نویسه رسید]")
            break
    return "".join(parts), len(reader.pages), with_text


def _docx_text(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    out: list[str] = [p.text for p in doc.paragraphs]
    # Tables carry the actual content of a form sample, so they are NOT skipped.
    for ti, table in enumerate(doc.tables, start=1):
        out.append(f"\n--- جدولِ {ti} ---")
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                out.append(" | ".join(cells))
    return "\n".join(x for x in out if x is not None)


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1256", "windows-1256", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", "replace")


def extract(data: bytes, filename: str, mime: str = "") -> dict:
    """Pull readable text out of one file.

    Returns ``{status, text, note, page_count}`` where ``status`` is one of
    ``ok | empty | unsupported | failed | image`` — four different ways of having
    no text, never collapsed into one.
    """
    name = (filename or "").lower()
    mime = (mime or "").lower()
    ext = Path(name).suffix

    def done(status: str, text: str = "", note: str = "", pages: int = 0,
             truncated: bool = False) -> dict:
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS]
            truncated = True
            note = (note + " " if note else "") + (
                f"متن در {MAX_TEXT_CHARS} نویسه بریده شد — بقیه‌اش فقط در خودِ فایل است، "
                "پس خواندنِ این متن «کاملش را خواندم» نیست و باید خودِ فایل را هم باز کنی")
        return {"status": status, "text": text, "note": note, "page_count": pages,
                "truncated": truncated}

    try:
        if mime.startswith("image/") or ext in _IMAGE_EXT:
            return done("image", "", "تصویر است — متنی برای استخراج ندارد؛ ناظر باید بازش کند و نگاه کند")

        if ext == ".pdf" or mime == "application/pdf":
            text, pages, with_text = _pdf_text(data)
            if with_text:
                note = f"از {pages} صفحهٔ PDF" + (
                    f" — ولی فقط {with_text} صفحه لایهٔ متنی داشت؛ بقیه احتمالاً "
                    "اسکن‌اند و باید خودِ فایل دیده شود" if with_text < pages else "")
                # a page-level stop is a truncation too: the later pages are only
                # in the file, so «I read the text» is not «I saw the document»
                return done("ok", text, note, pages,
                            truncated=("به سقفِ" in text or with_text < pages))
            # Pages exist, but not one of them carries text. That is NOT «empty»
            # and must not be «ok» either — the reviewer has to open the file.
            return done(
                "unsupported", "", pages=pages,
                note=(f"PDF {pages} صفحه دارد ولی هیچ صفحه‌ای لایهٔ متنی ندارد "
                      "(اسکن‌شده است) — ناظر باید خودِ فایل را باز کند و ببیند"))

        if ext == ".docx" or "wordprocessingml" in mime:
            text = _docx_text(data)
            return done("ok", text, "از فایلِ Word") if text.strip() else done(
                "empty", "", "فایلِ Word باز شد ولی متنی نداشت")

        if ext == ".doc" or mime == "application/msword":
            return done("unsupported", "", "قالبِ قدیمیِ .doc — استخراج‌کننده نداریم؛ "
                                           "ناظر باید بازش کند (یا مالک .docx بفرستد)")

        if ext in (".xlsx", ".xlsm", ".xls", ".csv"):
            from app.services.doc_ingest import workbook_to_text
            text = workbook_to_text(data, filename)
            return done("ok", text, "از کاربرگ") if text.strip() else done(
                "empty", "", "کاربرگ باز شد ولی سلولِ پُری نداشت")

        if ext in _TEXTY_EXT or mime.startswith("text/") or mime in (
                "application/json", "application/xml"):
            text = _decode(data)
            return done("ok", text, "متنِ ساده") if text.strip() else done(
                "empty", "", "فایل خالی است")

        if ext == ".pptx" or "presentationml" in mime:
            try:
                from pptx import Presentation  # optional dependency
            except Exception:
                return done("unsupported", "", "برای PowerPoint استخراج‌کننده نصب نیست — "
                                               "ناظر باید خودِ فایل را باز کند")
            prs = Presentation(io.BytesIO(data))
            out = []
            for i, slide in enumerate(prs.slides, start=1):
                out.append(f"\n--- اسلایدِ {i} ---")
                for shp in slide.shapes:
                    if getattr(shp, "has_text_frame", False):
                        out.append(shp.text_frame.text)
            text = "\n".join(out)
            return done("ok", text, "از PowerPoint") if text.strip() else done(
                "empty", "", "اسلایدها متنی نداشتند")

        if ext == ".zip" or mime in ("application/zip", "application/x-zip-compressed"):
            import zipfile
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()[:500]
            listing = "\n".join(names)
            return done("ok", f"--- فهرستِ محتویاتِ آرشیو ---\n{listing}",
                        "فقط فهرستِ فایل‌ها؛ برای دیدنِ محتوا باید بازش کرد")

        # Deliberately NOT «empty»: we never tried, and saying so is the point.
        return done("unsupported", "",
                    f"برای «{ext or mime or 'این نوع'}» استخراج‌کنندهٔ متن نداریم — "
                    "ناظر باید خودِ فایل را از درایو باز کند و کامل ببیند")
    except Exception as exc:  # noqa: BLE001 - the reason is the useful part
        logger.warning("inspection file extract failed: %s", exc)
        return done("failed", "", f"استخراج شکست خورد: {type(exc).__name__}: {exc}"[:400])


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def local_dir() -> Path:
    base = os.getenv("INSPECTION_FILE_DIR") or "storage/inspection"
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


async def store(*, data: bytes, filename: str, mime: str, report_number: int = 0,
                path_parts: list | None = None, stored_name: str = "",
                local_prefix: str = "") -> dict:
    """Put the bytes where they will still be there next month.

    Drive first, because the container disk does not survive a deploy. A local
    copy is the fallback so the feature never simply fails — but it is recorded
    AS a fallback, with the reason, so nobody mistakes it for durable storage.

    v152 — TWO THINGS THIS HAS TO DO THAT THE FIRST VERSION DID NOT:
      * ``drive_sync.prepare()`` first. In OAuth mode the blocking Drive client
        has no credentials until the refresh token is resolved and handed to it;
        `drive_sync` does that before every operation and even exposes a public
        `prepare()` «for other Drive-facing features». Calling `upload_file`
        without it fails with «Google Drive is not connected — no OAuth refresh
        token» while the status endpoint cheerfully reports `connected: true`,
        because status resolves the token itself. Measured on production: both
        of the owner's samples fell back to the container disk.
      * run the upload in a THREAD. `upload_file` is blocking, and a 100 MB
        sample would hold the event loop — freezing every other request — for as
        long as it took. Every other Drive caller in this app already does this.
    """
    import asyncio
    name = safe_filename(filename)
    sha = hashlib.sha256(data).hexdigest()
    # a distinct name per upload, so two samples with the same filename coexist.
    # (KB chat passes its own coded ``stored_name`` / ``path_parts`` /
    # ``local_prefix``; the sheet defaults below are unchanged.)
    stored_name = stored_name or f"{sha[:8]}-{name}"
    out = {"filename": name, "mime": mime, "byte_size": len(data), "sha256": sha,
           "store": "", "drive_id": "", "drive_link": "", "local_path": "",
           "store_note": ""}

    try:
        from app.services import drive_sync, google_drive as gd
        if gd.is_configured():
            # authenticate the blocking client for the active mode FIRST
            await drive_sync.prepare()
            res = await asyncio.to_thread(
                gd.upload_file,
                path_parts=path_parts or [DRIVE_ROOT, f"report-{int(report_number)}"],
                filename=stored_name, data=data,
                mimetype=mime or "application/octet-stream")
            out.update(store="drive", drive_id=res.get("id") or "",
                       drive_link=res.get("link") or "")
            return out
        reason = "Google Drive تنظیم نشده"
    except Exception as exc:  # noqa: BLE001
        logger.warning("inspection file → Drive failed: %s", exc)
        reason = f"آپلود به Drive شکست خورد: {type(exc).__name__}: {exc}"[:300]

    path = local_dir() / f"{local_prefix or 'r' + str(int(report_number)) + '-'}{stored_name}"
    path.write_bytes(data)
    out.update(store="local", local_path=str(path),
               store_note=(reason + " — فایل روی دیسکِ کانتینر ذخیره شد و "
                           "با دیپلویِ بعدی از بین می‌رود؛ درایو را تنظیم کن"))
    return out


async def load(row) -> bytes:
    """Fetch one stored file's bytes back, from wherever it really is."""
    import asyncio

    if getattr(row, "store", "") == "drive" and getattr(row, "drive_id", ""):
        from app.services import drive_sync, google_drive as gd
        await drive_sync.prepare()          # same credential step as the upload
        return await asyncio.to_thread(gd.download_file, row.drive_id)
    p = getattr(row, "local_path", "") or ""
    if p and Path(p).exists():
        return Path(p).read_bytes()
    raise FileNotFoundError(
        "فایل در دسترس نیست" + (" — روی دیسکِ کانتینر بود و با دیپلوی پاک شد"
                                if getattr(row, "store", "") == "local" else ""))
