"""«نظارت و سرکشی» — readers for every format the base extractor gave up on.

The owner's rule (2026-10-08, the same across all of their projects): «هر نوع
فرمتی باید خونده بشه توسط ناظر … و حتی کامل هم خونده بشه نه خلاصه و یا اوایل
اون فایل». This module is a PLUG-IN to the project's own extractor: that
extractor keeps every format it already reads (PDF, Word, Excel, …) and calls
`extract_extra()` wherever it used to answer «unsupported». Nothing it already
did changes.

    .doc   Word 97–2003 — the piece table, straight from the OLE container
    .xls   Excel 97–2003 — every sheet, every non-empty cell (xlrd)
    .rtf   rich text (striprtf; \\uN unicode escapes included)
    .odt .ods .odp   OpenDocument — content.xml
    .epub  every chapter, in spine order
    .eml   e-mail — headers, every text part, and every attachment (recursively)
    .msg   Outlook — subject, sender, body, and every attachment (recursively)
    .zip   EVERY member, recursively, each through the project's own extractor
    .svg   its whole source (it is text)
    *      anything that is really text, whatever its extension
    audio / video   → status «pending»: the full transcript is made by
                    `inspection_media.transcribe` (no summary), and a pending
                    file is a read debt that opening its bytes does NOT clear

Returned shape (the same the base extractors use):
    {status, text, note, page_count, truncated}
Dependencies are optional — a missing one is reported as `failed` with the
exact `pip install` to run, never as «nothing to read».
"""
from __future__ import annotations

import contextvars
import email
import email.policy
import html as _html
import io
import mimetypes
import re
import struct
import zipfile
from pathlib import Path
from typing import Callable, Optional

#: archive safety — a zip bomb must not take the server down; hitting a cap is
#: REPORTED (truncated=True), never silent
ZIP_MAX_MEMBERS = 3000
ZIP_MAX_TOTAL_BYTES = 600 * 1024 * 1024
ZIP_MAX_DEPTH = 4

MEDIA_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".oga", ".opus", ".flac", ".aac", ".amr", ".wma",
             ".aif", ".aiff", ".weba", ".mp4", ".mov", ".mkv", ".webm", ".avi", ".3gp", ".m4v",
             ".wmv", ".mpeg", ".mpg", ".mts")

_depth: contextvars.ContextVar[int] = contextvars.ContextVar("inspection_extract_depth", default=0)

Base = Callable[[bytes, str, str], dict]


def is_media(name: str, mime: str = "") -> bool:
    mime = (mime or "").lower()
    return mime.startswith(("audio/", "video/")) or Path((name or "").lower()).suffix in MEDIA_EXT


def guess_mime(name: str) -> str:
    return mimetypes.guess_type(name or "")[0] or ""


def _done(status: str, text: str = "", note: str = "", pages: int = 0, truncated: bool = False) -> dict:
    return {"status": status, "text": text or "", "note": note, "page_count": pages, "truncated": truncated}


def _text_or_empty(text: str, ok: str, empty: str) -> dict:
    return _done("ok", text, ok) if (text or "").strip() else _done("empty", "", empty)


def _need(lib: str, pkg: str) -> dict:
    return _done("failed", "", f"کتابخانهٔ «{lib}» نصب نیست — `pip install {pkg}` (در requirements هست؛ دیپلویِ تازه)")


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------
def extract_extra(data: bytes, filename: str, mime: str = "", *, base: Optional[Base] = None) -> Optional[dict]:
    """The full text for a format the base extractor does not read — or None
    when this module has nothing to add (the caller keeps its own answer)."""
    name = (filename or "").lower()
    mime = (mime or "").lower()
    ext = Path(name).suffix
    try:
        if is_media(name, mime):
            return _done("pending", "", "صوت/ویدیو — در صفِ رونویسیِ کامل (متنِ کامل با زمان‌بندی؛ "
                                        "برای ویدیو، شرحِ تصویر هم) — نه خلاصه")
        if ext == ".svg" or mime == "image/svg+xml":
            return _text_or_empty(_decode(data), "منبعِ کاملِ SVG (متن)", "SVG خالی است")
        if ext == ".doc" or mime == "application/msword":
            try:
                return _text_or_empty(doc_text(data), "از Word ِ قدیمی (.doc) — متنِ کامل", "فایلِ .doc متنی نداشت")
            except ImportError:
                return _need("olefile", "olefile")
        if ext == ".xls" or mime == "application/vnd.ms-excel":
            try:
                return _text_or_empty(xls_text(data), "از Excel ِ قدیمی (.xls) — همهٔ کاربرگ‌ها",
                                      "کاربرگ سلولِ پُری نداشت")
            except ImportError:
                return _need("xlrd", "xlrd")
        if ext == ".rtf" or mime in ("application/rtf", "text/rtf"):
            try:
                return _text_or_empty(rtf_text(data), "از RTF — متنِ کامل", "RTF متنی نداشت")
            except ImportError:
                return _need("striprtf", "striprtf")
        if ext in (".odt", ".ods", ".odp") or "opendocument" in mime:
            return _text_or_empty(odf_text(data), "از OpenDocument — متنِ کامل", "سند متنی نداشت")
        if ext == ".epub" or mime == "application/epub+zip":
            return _text_or_empty(epub_text(data), "از EPUB — همهٔ فصل‌ها به ترتیب", "کتاب متنی نداشت")
        if ext == ".eml" or mime == "message/rfc822":
            return _text_or_empty(eml_text(data, base), "ایمیل — سرآیندها، متن و همهٔ پیوست‌ها", "ایمیل خالی است")
        if ext == ".msg" or mime == "application/vnd.ms-outlook":
            try:
                return _text_or_empty(msg_text(data, base), "ایمیلِ Outlook — متن و همهٔ پیوست‌ها", "ایمیل خالی است")
            except ImportError:
                return _need("olefile", "olefile")
        if ext == ".zip" or mime in ("application/zip", "application/x-zip-compressed") or (
                not ext.endswith(("x", "m")) and zipfile.is_zipfile(io.BytesIO(data))):
            text, truncated, note, media = zip_text(data, base)
            if media:
                return _done("pending", text, note + f" — {media} صوت/ویدیو منتظرِ رونویسیِ کامل", truncated=truncated)
            return _done("ok", text, note, truncated=truncated) if text.strip() else _done("empty", "", note)
        sniffed = sniff_text(data)
        if sniffed is not None:
            return _text_or_empty(sniffed, f"متنِ کامل (قالبِ «{ext or mime or 'بی‌پسوند'}» متنی بود)", "فایل خالی است")
        return None
    except Exception as exc:  # noqa: BLE001 — the reason is the useful part
        return _done("failed", "", f"استخراج شکست خورد: {type(exc).__name__}: {exc}"[:400])


def read_member(data: bytes, name: str, base: Optional[Base]) -> dict:
    """One file inside an archive/e-mail: the project's own extractor first; this
    module for whatever that one does not read."""
    mime = guess_mime(name)
    res = base(data, name, mime) if base else None
    if res is None or res.get("status") in ("unsupported", None):
        extra = extract_extra(data, name, mime, base=base)
        if extra is not None:
            return extra
    return res or _done("unsupported", "", "قالبِ ناشناخته")


# ---------------------------------------------------------------------------
# text, whatever the extension
# ---------------------------------------------------------------------------
def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1256"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def sniff_text(data: bytes) -> Optional[str]:
    """The text, when the bytes ARE text whatever the extension says. None for binary."""
    if not data:
        return None
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            return None
    if b"\x00" in data[:65536]:
        return None
    for enc in ("utf-8-sig", "cp1256"):
        try:
            text = data.decode(enc)
        except UnicodeDecodeError:
            continue
        sample = text[:20000]
        if sum(ch.isprintable() or ch in "\r\n\t" for ch in sample) >= 0.97 * len(sample):
            return text
    return None


def html_visible(data: bytes) -> str:
    txt = _decode(data)
    txt = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", txt)
    txt = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return _html.unescape(re.sub(r"[ \t]+", " ", txt))


# ---------------------------------------------------------------------------
# Word 97–2003 (.doc), Excel 97–2003 (.xls), RTF
# ---------------------------------------------------------------------------
def doc_text(data: bytes) -> str:
    """The document text from the piece table (CLX), in order — 8-bit (cp1252)
    and UTF-16 pieces both (Persian text is UTF-16)."""
    import olefile

    ole = olefile.OleFileIO(io.BytesIO(data))
    wd = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    table = ole.openstream("1Table" if flags & 0x0200 else "0Table").read()
    fc_clx, lcb_clx = struct.unpack_from("<II", wd, 0x01A2)
    clx = table[fc_clx:fc_clx + lcb_clx]
    i = 0
    while i < len(clx) and clx[i] == 0x01:
        i += 3 + struct.unpack_from("<H", clx, i + 1)[0]
    if i >= len(clx) or clx[i] != 0x02:
        raise ValueError("جدولِ قطعه‌ها (CLX) پیدا نشد")
    lcb = struct.unpack_from("<I", clx, i + 1)[0]
    plc = clx[i + 5:i + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from(f"<{n + 1}I", plc, 0)
    out = []
    for k in range(n):
        pcd = plc[(n + 1) * 4 + k * 8:(n + 1) * 4 + k * 8 + 8]
        fc = struct.unpack_from("<I", pcd, 2)[0]
        count = cps[k + 1] - cps[k]
        if fc & 0x40000000:
            start = (fc & 0x3FFFFFFF) // 2
            out.append(wd[start:start + count].decode("cp1252", "replace"))
        else:
            out.append(wd[fc:fc + 2 * count].decode("utf-16-le", "replace"))
    text = "".join(out)
    text = re.sub(r"\x13[^\x14\x15]*\x14?", "", text)
    text = text.replace("\x07", " | ").replace("\x0b", "\n").replace("\r", "\n").replace("\x0c", "\n")
    return re.sub(r"[\x00-\x08\x0e-\x1f]", "", text)


def xls_text(data: bytes) -> str:
    import xlrd

    book = xlrd.open_workbook(file_contents=data)
    parts = []
    for sh in book.sheets():
        parts.append(f"=== کاربرگ: {sh.name} ({sh.nrows}×{sh.ncols}) ===")
        for r in range(sh.nrows):
            cells = [str(v).strip() for v in sh.row_values(r)]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def rtf_text(data: bytes) -> str:
    from striprtf.striprtf import rtf_to_text

    return rtf_to_text(data.decode("latin-1"), errors="ignore")


# ---------------------------------------------------------------------------
# OpenDocument, EPUB
# ---------------------------------------------------------------------------
def odf_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("content.xml").decode("utf-8", "replace")
    xml = re.sub(r"<(text:p|text:h|table:table-row)\b[^>]*/>", "\n", xml)
    xml = re.sub(r"</(text:p|text:h|table:table-row|text:list-item)>", "\n", xml)
    xml = re.sub(r"</table:table-cell>", " | ", xml)
    xml = re.sub(r"<text:tab/>", "\t", xml)
    xml = re.sub(r"<text:line-break/>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return _html.unescape(re.sub(r"\n{3,}", "\n\n", xml))


def epub_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        order: list[str] = []
        try:
            container = z.read("META-INF/container.xml").decode("utf-8", "replace")
            opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
            opf = z.read(opf_path).decode("utf-8", "replace")
            base_dir = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""
            items = dict(re.findall(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf))
            items.update({k: v for v, k in re.findall(r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf)})
            order = [base_dir + items[i] for i in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf) if i in items]
        except Exception:  # noqa: BLE001 — fall back to name order
            order = []
        if not order:
            order = sorted(n for n in names if n.lower().endswith((".xhtml", ".html", ".htm")))
        return "\n\n".join(f"=== {n} ===\n" + html_visible(z.read(n)) for n in order if n in names)


# ---------------------------------------------------------------------------
# e-mail (.eml) and Outlook (.msg) — with their attachments
# ---------------------------------------------------------------------------
def eml_text(data: bytes, base: Optional[Base]) -> str:
    msg = email.message_from_bytes(data, policy=email.policy.default)
    head = [f"{h}: {msg[h]}" for h in ("From", "To", "Cc", "Date", "Subject") if msg[h]]
    parts, plain_seen = [], False
    for part in msg.walk():
        if part.is_multipart():
            continue
        fname = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        ctype = part.get_content_type()
        if fname:
            sub = read_member(payload, fname, base)
            parts.append(f"=== پیوستِ ایمیل: {fname} ({sub['status']}) ===\n{sub['text'] or sub['note']}")
        elif ctype == "text/plain":
            plain_seen = True
            parts.append(payload.decode(part.get_content_charset() or "utf-8", "replace"))
        elif ctype == "text/html" and not plain_seen:
            parts.append(html_visible(payload))
    return "\n".join(head) + "\n\n" + "\n\n".join(parts)


def msg_text(data: bytes, base: Optional[Base]) -> str:
    import olefile

    ole = olefile.OleFileIO(io.BytesIO(data))

    def s(path: str) -> str:
        for suffix, enc in (("001F", "utf-16-le"), ("001E", "cp1252")):
            if ole.exists(path + suffix):
                return ole.openstream(path + suffix).read().decode(enc, "replace").rstrip("\x00")
        return ""

    out = [f"From: {s('__substg1.0_0C1A')} <{s('__substg1.0_0C1F')}>",
           f"To: {s('__substg1.0_0E04')}", f"Subject: {s('__substg1.0_0037')}", "", s("__substg1.0_1000")]
    seen = set()
    for entry in ole.listdir():
        if entry and entry[0].startswith("__attach_version1.0_") and entry[0] not in seen:
            seen.add(entry[0])
            root = entry[0] + "/"
            name = s(root + "__substg1.0_3707") or s(root + "__substg1.0_3704") or entry[0]
            if ole.exists(root + "__substg1.0_37010102"):
                sub = read_member(ole.openstream(root + "__substg1.0_37010102").read(), name, base)
                out.append(f"\n=== پیوستِ ایمیل: {name} ({sub['status']}) ===\n{sub['text'] or sub['note']}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# zip — every member, through the project's own extractor
# ---------------------------------------------------------------------------
def zip_text(data: bytes, base: Optional[Base]) -> tuple[str, bool, str, int]:
    """`(text, truncated, note, media_pending)` for an archive and everything in it."""
    depth = _depth.get()
    if depth >= ZIP_MAX_DEPTH:
        return "", True, f"آرشیوِ تو در تو عمیق‌تر از {ZIP_MAX_DEPTH} لایه — بقیه را باید جدا باز کرد", 0
    token = _depth.set(depth + 1)
    try:
        parts, total, truncated, counts = [], 0, False, {}
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            if len(infos) > ZIP_MAX_MEMBERS:
                infos, truncated = infos[:ZIP_MAX_MEMBERS], True
            for info in infos:
                total += info.file_size
                if total > ZIP_MAX_TOTAL_BYTES:
                    truncated = True
                    parts.append(f"=== {info.filename} — از سقفِ حجمِ بازشده گذشت؛ بقیه خوانده نشد ===")
                    break
                sub = read_member(z.read(info), info.filename, base)
                counts[sub["status"]] = counts.get(sub["status"], 0) + 1
                truncated = truncated or bool(sub.get("truncated"))
                body = sub["text"] if sub.get("text") else f"[{sub.get('note') or ''}]"
                parts.append(f"===== {info.filename} ({sub['status']}) =====\n{body}")
    finally:
        _depth.reset(token)
    note = (f"آرشیو: {sum(counts.values())} فایل، هر کدام با خوانندهٔ خودش — "
            + "، ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
            + ("؛ تصویر/صوت/ویدیوی داخلش را `inspection.py pull` جدا باز می‌کند"
               if counts.get("image") or counts.get("pending") else ""))
    return "\n\n".join(parts), truncated, note, counts.get("pending", 0)
