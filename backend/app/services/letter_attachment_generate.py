"""Generate a REAL file attachment for a letter from the owner's instruction.

Review-first, server-is-ground-truth: the model only ever proposes a STRICT
JSON *spec* (kind/filename/title + sheets for Excel or paragraphs for Word);
a deterministic validator clamps everything, and the actual file is rendered
SERVER-SIDE (openpyxl / python-docx) and stored through the very same
Drive+disk+DB path as manual uploads. The stored record carries an
``AI_GENERATED`` marker in its notes so the attachment-extraction tool can
exclude these by default — their data came out of the database in the first
place (feeding them back in would be a circular write).

Data discipline mirrors the letter assistant: values come ONLY from the
database facts or the instruction itself; anything unavailable stays EMPTY and
is reported in ``warnings`` — never invented.
"""
from __future__ import annotations

import io
import json
import re
from typing import Any, Dict, List, Tuple

AI_GENERATED_MARK = "AI_GENERATED"

MAX_SHEETS = 3
MAX_ROWS = 500
MAX_COLS = 30
MAX_PARAGRAPHS = 150
MAX_CELL = 500

SYSTEM_PROMPT = (
    "تو سازندهٔ «پیوستِ رسمیِ» یک نامهٔ بانکی هستی. بر اساسِ دستورِ کاربر، زمینهٔ نامه و "
    "«حقایقِ پایگاه‌داده» فقط و فقط یک شیءِ JSON برگردان — بدونِ متنِ اضافه، بدونِ markdown.\n"
    "قواعدِ الزامی:\n"
    "1) دادهٔ واقعی فقط از «حقایقِ پایگاه‌داده» یا خودِ دستورِ کاربر می‌آید؛ هرگز عدد/تاریخ/نام/مبلغ "
    "نساز. اگر قلمی خواسته شده و موجود نیست، خانه/بخش را خالی بگذار و دلیل را در warnings بنویس.\n"
    "2) لحن و نگارش باید هم‌سطحِ نامهٔ رسمیِ بانکی و هماهنگ با متنِ نامه باشد (رسمی، سوم‌شخص، بدونِ اغراق).\n"
    "3) kind را خودت هوشمندانه انتخاب کن مگر کاربر صریحاً گفته باشد: جدولی/عددی ⇒ \"excel\"، "
    "متنی/توضیحی ⇒ \"word\".\n"
    "4) ساختارِ خروجی:\n"
    "{\"kind\": \"excel\"|\"word\", \"filename\": \"نامِ کوتاهِ فارسیِ فایل بدون پسوند\", "
    "\"title\": \"عنوانِ سند\", \"warnings\": [\"...\"],\n"
    " \"sheets\": [{\"name\": \"...\", \"columns\": [\"...\"], \"rows\": [[\"...\"]]}]   ← فقط برای excel\n"
    " \"paragraphs\": [{\"text\": \"...\", \"heading\": true|false, \"bold\": true|false, "
    "\"align\": \"right\"|\"center\"|\"justify\"}]   ← فقط برای word }\n"
    f"5) سقف‌ها: {MAX_SHEETS} شیت، {MAX_ROWS} ردیف، {MAX_COLS} ستون، {MAX_PARAGRAPHS} پاراگراف.\n"
    "6) سرستون‌ها فارسی و روشن؛ اعدادِ مبلغ با جداکنندهٔ هزارگان؛ ستونِ آخرِ هر شیت را اگر مفید است "
    "«ملاحظات» بگذار.\n"
    "7) filename کوتاه، فارسی، بدونِ / \\ : * ? \" < > |."
)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def build_prompt(facts: Dict[str, Any], letter_ctx: Dict[str, str], instruction: str) -> str:
    parts: List[str] = []
    parts.append("### زمینهٔ نامه (برای لحن و موضوع):")
    for k, label in (("subject", "موضوع"), ("recipient", "گیرنده"), ("body_excerpt", "گزیدهٔ متن")):
        v = (letter_ctx.get(k) or "").strip()
        if v:
            parts.append(f"- {label}: {v[:1200]}")
    parts.append("\n### حقایقِ پایگاه‌داده (تنها منبعِ مجازِ داده):")
    parts.append(json.dumps(facts, ensure_ascii=False, indent=1) if facts else "(بدون رکورد مرتبط — فقط از خودِ دستور استفاده کن و کمبودها را در warnings بگو)")
    parts.append("\n### دستورِ کاربر (پیوستی که باید ساخته شود):")
    parts.append(instruction.strip()[:3000])
    parts.append("\nحالا فقط JSON مشخصاتِ پیوست را برگردان.")
    return "\n".join(parts)


def _clean_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', "-", (name or "").strip())
    name = re.sub(r"\s+", " ", name).strip(" .-") or "پیوست"
    return name[:80]


def parse_spec(raw_text: str) -> Tuple[Dict[str, Any], List[str]]:
    """Parse + CLAMP the model's spec. Raises ValueError when unusable."""
    m = _JSON_RE.search(raw_text or "")
    if not m:
        raise ValueError("no_json")
    try:
        data = json.loads(m.group(0))
    except Exception as exc:  # noqa: BLE001
        raise ValueError("bad_json") from exc
    if not isinstance(data, dict):
        raise ValueError("bad_json")

    kind = str(data.get("kind") or "").strip().lower()
    if kind not in ("excel", "word"):
        # infer: sheets ⇒ excel, paragraphs ⇒ word
        kind = "excel" if data.get("sheets") else "word"

    warnings = [str(w)[:300] for w in (data.get("warnings") or []) if str(w).strip()][:10]
    spec: Dict[str, Any] = {
        "kind": kind,
        "filename": _clean_filename(str(data.get("filename") or "پیوست")),
        "title": str(data.get("title") or "").strip()[:200],
    }

    if kind == "excel":
        sheets_in = data.get("sheets") or []
        if not isinstance(sheets_in, list) or not sheets_in:
            raise ValueError("no_sheets")
        sheets: List[Dict[str, Any]] = []
        for sh in sheets_in[:MAX_SHEETS]:
            if not isinstance(sh, dict):
                continue
            cols = [str(c)[:120] for c in (sh.get("columns") or [])][:MAX_COLS]
            if not cols:
                continue
            rows: List[List[str]] = []
            for row in (sh.get("rows") or [])[:MAX_ROWS]:
                if not isinstance(row, list):
                    continue
                rows.append([("" if c is None else str(c))[:MAX_CELL] for c in row[: len(cols)]])
            name = re.sub(r"[\\/*?\[\]:]+", "-", str(sh.get("name") or "برگه"))[:30] or "برگه"
            sheets.append({"name": name, "columns": cols, "rows": rows})
        if not sheets:
            raise ValueError("no_sheets")
        spec["sheets"] = sheets
    else:
        paras_in = data.get("paragraphs") or []
        if not isinstance(paras_in, list) or not paras_in:
            raise ValueError("no_paragraphs")
        paras: List[Dict[str, Any]] = []
        for p in paras_in[:MAX_PARAGRAPHS]:
            if isinstance(p, str):
                p = {"text": p}
            if not isinstance(p, dict):
                continue
            text = str(p.get("text") or "").strip()
            if not text:
                continue
            align = str(p.get("align") or "").lower()
            paras.append({
                "text": text[:4000],
                "heading": bool(p.get("heading")),
                "bold": bool(p.get("bold")),
                "align": align if align in ("right", "center", "justify") else "justify",
            })
        if not paras:
            raise ValueError("no_paragraphs")
        spec["paragraphs"] = paras

    return spec, warnings


# ---------------------------------------------------------------------------
# Renderers — clean, official-looking output (RTL, Persian-friendly fonts).
# ---------------------------------------------------------------------------

def render_excel(spec: Dict[str, Any]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    wb.remove(wb.active)
    thin = Side(style="thin", color="444444")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    head_fill = PatternFill("solid", fgColor="DCE6F1")
    head_font = Font(name="B Nazanin", bold=True, size=12)
    cell_font = Font(name="B Nazanin", size=11)
    title_font = Font(name="B Titr", bold=True, size=13)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    right = Alignment(horizontal="right", vertical="center", wrap_text=True)

    for sh in spec["sheets"]:
        ws = wb.create_sheet(title=sh["name"])
        ws.sheet_view.rightToLeft = True
        ncols = len(sh["columns"])
        r0 = 1
        if spec.get("title"):
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(1, ncols))
            tc = ws.cell(row=1, column=1, value=spec["title"])
            tc.font = title_font
            tc.alignment = center
            ws.row_dimensions[1].height = 26
            r0 = 2
        for ci, col in enumerate(sh["columns"], start=1):
            c = ws.cell(row=r0, column=ci, value=col)
            c.font = head_font
            c.fill = head_fill
            c.border = border
            c.alignment = center
        ws.row_dimensions[r0].height = 22
        for ri, row in enumerate(sh["rows"], start=r0 + 1):
            for ci in range(1, ncols + 1):
                val = row[ci - 1] if ci - 1 < len(row) else ""
                c = ws.cell(row=ri, column=ci, value=val)
                c.font = cell_font
                c.border = border
                c.alignment = right
        # column widths sized to content (clamped so the sheet stays printable)
        for ci in range(1, ncols + 1):
            longest = max(
                [len(str(sh["columns"][ci - 1]))]
                + [len(str(r[ci - 1])) if ci - 1 < len(r) else 0 for r in sh["rows"]]
                or [8]
            )
            ws.column_dimensions[get_column_letter(ci)].width = min(60, max(10, longest + 4))
        ws.freeze_panes = ws.cell(row=r0 + 1, column=1)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def render_word(spec: Dict[str, Any]) -> bytes:
    import docx  # python-docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    def make_rtl(paragraph) -> None:
        pPr = paragraph._p.get_or_add_pPr()
        bidi = OxmlElement("w:bidi")
        pPr.append(bidi)

    def style_run(run, *, bold: bool, size: int) -> None:
        run.font.name = "B Nazanin"
        run.font.size = Pt(size)
        run.bold = bold
        rPr = run._r.get_or_add_rPr()
        rfonts = rPr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rPr.append(rfonts)
        rfonts.set(qn("w:cs"), "B Nazanin")
        szcs = OxmlElement("w:szCs")
        szcs.set(qn("w:val"), str(size * 2))
        rPr.append(szcs)
        if bold:
            bcs = OxmlElement("w:bCs")
            rPr.append(bcs)

    doc = docx.Document()
    if spec.get("title"):
        p = doc.add_paragraph()
        make_rtl(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style_run(p.add_run(spec["title"]), bold=True, size=15)
    for para in spec["paragraphs"]:
        p = doc.add_paragraph()
        make_rtl(p)
        p.alignment = {
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
            "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        }[para["align"]]
        style_run(
            p.add_run(para["text"]),
            bold=bool(para["bold"] or para["heading"]),
            size=14 if para["heading"] else 12,
        )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def render(spec: Dict[str, Any]) -> Tuple[bytes, str, str]:
    """Render the validated spec → (bytes, full filename, mimetype)."""
    if spec["kind"] == "excel":
        data = render_excel(spec)
        return data, f"{spec['filename']}.xlsx", (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    data = render_word(spec)
    return data, f"{spec['filename']}.docx", (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
