"""AI letter-assistant — propose reviewable edits to an official letter.

The philosophy mirrors the rest of the panel: **review-first, never auto-apply**.
This service asks a configured AI model to return a STRICT list of *proposed*
changes; it then **validates every change against the actual letter content** (a
``text_replace`` whose ``find`` is not present is dropped — the hallucination
guard) before handing the sanitized list to the router. Nothing here mutates the
database or the letter; applying happens client-side after the human ticks the
changes they want, and the letter is persisted only through the normal Save flow.

The model is given full, authoritative DB facts for the letter's account so it
can (a) validate figures/names against the record and (b) flag inconsistencies —
but it can only ever *propose*; the deterministic validation below is the gate.
"""
from __future__ import annotations

import html as _html
import json
import re
from typing import Any, Dict, List, Optional

# Scalar fields the assistant may replace WHOLE (short identity/meta fields).
# The body is deliberately excluded — it is rich HTML and may only be edited
# surgically via ``text_replace`` so tables/inline formatting are never destroyed.
SCALAR_FIELDS: Dict[str, str] = {
    "subject": "موضوع نامه",
    "recipientName": "نام گیرنده",
    "recipientTitle": "سمت گیرنده",
    "recipientDept": "اداره/دایره گیرنده",
    "classification": "طبقه‌بندی",
    "sender": "امضاکننده",
    "copyTo": "رونوشت",
    "actionName": "اقدام‌کننده",
    "actionExt": "داخلی اقدام‌کننده",
    "serial": "شماره نامه",
    "year": "سال",
    "date": "تاریخ",
    "attachment": "پیوست",
}
# Fields that carry flowing text and therefore accept surgical text_replace.
TEXT_FIELDS = {"body", "subject", "recipientName", "recipientTitle", "recipientDept", "copyTo", "actionName"}

BODY_FIELD = "body"

VALID_CATEGORIES = {
    "spelling", "grammar", "paragraphs", "tables",
    "consistency", "professional", "validation", "db_extract",
    "complete", "inline_prompts", "other",
}
VALID_SEVERITY = {"low", "medium", "high"}

# Suggested canonical profile keys the extractor maps facts onto (the profile
# blob is free-form, so near-matches are fine; this just steers the model).
CANONICAL_KEYS = [
    "address", "po_box", "city", "emirate", "phone", "mobile", "email",
    "nationality", "date_of_birth", "national_id", "emirates_id_no",
    "passport_no", "passport_expiry", "trade_license_no", "trade_license_expiry",
    "business_type", "company_name", "contact_person", "occupation",
    "employer", "monthly_salary", "iban",
]

# The tools the UI offers; sent into the prompt so the model focuses only on
# what the user ticked. id → (fa label, guidance appended to the prompt).
TOOLS: Dict[str, Dict[str, str]] = {
    "spelling": {
        "label": "یافتن و اصلاح غلط‌های املایی",
        "guide": "غلط‌های املایی/تایپی فارسی و لاتین را بیاب و اصلاح کن (category=spelling).",
    },
    "grammar": {
        "label": "نکات نگارشی و دستوری",
        "guide": "مشکلات نگارشی/دستوری، نیم‌فاصله، علائم سجاوندی و رسم‌الخط را اصلاح کن (category=grammar).",
    },
    "paragraphs": {
        "label": "چینش و انسجام پاراگراف‌ها",
        "guide": "ترتیب و انسجام پاراگراف‌ها، جملات بریده یا تکراری را بهبود بده؛ فقط با text_replace روی متنِ موجود (category=paragraphs).",
    },
    "tables": {
        "label": "بررسی و اصلاح جداول",
        "guide": "ناهماهنگی محتوای جدول‌ها (سرستون‌ها، واحدها، ردیف‌های خالی) را گزارش کن؛ اصلاح محتوایی با text_replace، تغییرات ساختاری صرفاً به‌صورت note (category=tables). برای پر کردنِ محتوای جدول فقط از «حقایقِ پایگاه‌داده» استفاده کن — قلمِ ناموجود را «—» بگذار و در note اعلام کن؛ هیچ داده‌ای نساز.",
    },
    "consistency": {
        "label": "یافتن و اصلاح مغایرت‌ها",
        "guide": "مغایرت میان متنِ نامه و «حقایق پایگاه‌داده» (مبالغ، نرخ، نام‌ها، شماره‌حساب، تاریخ‌ها) و نیز مغایرت‌های درونِ خودِ نامه را بیاب؛ در detail به فیلد پایگاه‌داده استناد کن (category=consistency).",
    },
    "professional": {
        "label": "تنظیم حرفه‌ای و رسمی متن",
        "guide": (
            "لحن را رسمی/اداری/بانکی کن بدون تغییرِ معنا و بدون افزودنِ ادعای جدید. اگر تمامِ متن "
            "یا بخش‌هایی از آن عامیانه/محاوره‌ای نوشته شده (حتی چند کلمه وسطِ متنِ رسمی)، همان بخش‌ها "
            "را به نثرِ رسمیِ اداری-بانکیِ هماهنگ با لحنِ بقیهٔ نامه و مکاتباتِ مشابه بازنویسی کن — "
            "هر جمله/عبارت با یک text_replace جدا تا کاربر تک‌تک تیک بزند؛ متنِ کاملاً عامیانه را هم "
            "پاراگراف‌به‌پاراگراف بازنویسی کن، نه یکجا. "
            "فراتر از اصلاحِ غلط: ویراستارِ ارشد باش — جمله‌بندیِ خام، ناشیانه یا تکراری را حتی وقتی "
            "«غلط» نیست، شیواتر و پخته‌تر بازنویسی کن: تکرارِ واژه‌ها و فعل‌های هم‌شکل در جمله‌های "
            "مجاور را با مترادف‌های اداری تنوع بده، عبارت‌های زائد و حشو را حذف کن، جمله‌های بلند و "
            "درهم را به جمله‌های روان بشکن، و پیوندِ منطقیِ جمله‌ها (لذا، در همین راستا، شایان ذکر "
            "است…) را طبیعی کن. برای هر جمله/پاراگرافِ قابل‌بهبود یک text_replace با نسخهٔ شیوایِ "
            "کامل بده — معنا، اعداد و تعهدها را عوض نکن (category=professional)."
        ),
    },
    "complete": {
        "label": "تکمیلِ جمله‌های ناتمام (علامتِ سؤال / جای خالی)",
        "guide": (
            "جاهایی که نویسنده نتوانسته جمله را ببندد را بیاب و کامل کن: علامتِ سؤالِ تنها "
            "(«؟» یا ?) که به‌جای ادامه/پایانِ جمله گذاشته شده (نه سؤالِ واقعیِ متن)، جملهٔ "
            "نیمه‌کاره، «...»، یا جای خالیِ آشکار. همان جمله را با text_replace به جمله‌ای کامل، "
            "رسمی و روان تبدیل کن: فعل و پایان‌بندیِ اداریِ مناسب انتخاب کن، از تکرارِ واژه‌ها و "
            "فعل‌های جمله‌های مجاور پرهیز کن، و مقصودِ نویسنده را از بافتِ همان پاراگراف بگیر. "
            "هیچ ادعای مالی/عددیِ جدیدی نساز؛ اگر مقصود مبهم است، به‌جای حدسِ پرریسک دو پیشنهادِ "
            "جایگزینِ جدا بده یا note با توضیحِ ابهام (category=complete)."
        ),
    },
    "inline_prompts": {
        "label": "اجرای دستورهای نوشته‌شده داخلِ متن",
        "guide": (
            "جمله‌هایی از متن که «متنِ نامه» نیستند بلکه دستورِ نویسنده خطاب به تو هستند را "
            "تشخیص بده — مثل: «اینجا یه پاراگراف دربارهٔ وضعیت وثایق بنویس»، «این قسمت رو با "
            "ارقامِ تسهیلات پر کن»، «میخوام اینجا اشاره بشه که ...». برای هر دستور یک text_replace "
            "بده که خودِ جملهٔ دستور را با متنِ خواسته‌شده جایگزین کند: رسمی، بانکی، هم‌لحنِ بقیهٔ "
            "نامه، و دقیقاً همان چیزی که دستور خواسته. اگر دستور به داده نیاز دارد، تنها منبعِ مجاز "
            "«حقایقِ پایگاه‌داده» است — قلمِ ناموجود را «________» بگذار و در detail بگو چه چیزی در "
            "پایگاه‌داده نبود؛ هیچ عدد/تاریخ/نامی نساز. اگر دستور می‌گوید داده‌ای در پرونده/پایگاه‌داده "
            "«ثبت شود»، علاوه بر متن، برای هر واقعیت یک op=\"db_write\" هم بده (همان قواعدِ ابزارِ "
            "استخراج: account_no/customer_name/key/value). جملهٔ دستور نباید در متنِ نهایی بماند "
            "(category=inline_prompts)."
        ),
    },
    "validation": {
        "label": "اعتبارسنجی موردِ انتخاب‌شده با پایگاه‌داده",
        "guide": "موردِ انتخاب‌شده را در برابر «حقایق پایگاه‌داده» راستی‌آزمایی کن؛ اگر درست است note با severity=low و اگر غلط است اصلاحِ text_replace/set_field پیشنهاد بده (category=validation).",
    },
    "db_extract": {
        "label": "استخراج و ثبتِ داده‌های مفید در پروفایلِ مشتری(ها)",
        "guide": (
            "داده‌های مفیدِ پروفایلی را از متنِ نامه استخراج کن و برای هرکدام یک تغییر با "
            "op=\"db_write\" بده. **با نهایت دقت**: یک نامه ممکن است چند مشتری را نام ببرد؛ هر "
            "واقعیت را فقط به مشتریِ درستش نسبت بده. برای هر db_write این کلیدها را بده: "
            "account_no (اگر شماره‌حسابِ آن مشتری در متن آمده؛ وگرنه خالی)، customer_name (نامِ "
            "همان مشتری)، key (نامِ فیلدِ کوتاهِ snake_case از این فهرست یا مشابهش: "
            + ", ".join(CANONICAL_KEYS) + ")، value (مقدارِ استخراج‌شده). "
            "فقط واقعیت‌های صریحِ متن؛ چیزی از خودت نساز. اگر واقعیتی به مشتریِ اصلیِ نامه ربط "
            "ندارد، account_no/customer_name همان مشتریِ دیگر را بگذار. (category=db_extract)"
        ),
    },
}

# ---------------------------------------------------------------------------
# Table HTML sanitizer — the ONLY way model-authored HTML ever reaches the
# letter. op="table_replace" lets the model redesign a user-selected table in
# EVERY way (structure + content + basic styling), so the returned HTML must be
# strictly whitelisted: table tags + basic inline emphasis, colspan/rowspan and
# a small set of safe style properties. Everything else (scripts, handlers,
# links, images, unknown tags/attrs) is dropped.
# ---------------------------------------------------------------------------
_TBL_ALLOWED_TAGS = {"table", "thead", "tbody", "tfoot", "tr", "td", "th",
                     "colgroup", "col", "caption", "b", "strong", "i", "em",
                     "u", "s", "br", "span", "div", "p"}
_TBL_VOID_TAGS = {"br", "col"}
_TBL_STYLE_PROPS = {"text-align", "font-weight", "font-style", "text-decoration",
                    "width", "vertical-align", "line-height", "font-size",
                    "direction", "background"}
MAX_TABLES = 8


def _clean_style(style: str) -> str:
    parts = []
    for decl in (style or "").split(";"):
        if ":" not in decl:
            continue
        prop, val = decl.split(":", 1)
        prop, val = prop.strip().lower(), val.strip()
        if prop in _TBL_STYLE_PROPS and "url(" not in val.lower() and "expression" not in val.lower():
            parts.append(f"{prop}:{val}")
    return ";".join(parts)


def sanitize_table_html(html: str) -> str:
    """Whitelist-rebuild a <table> fragment. Returns '' when it isn't one."""
    from html.parser import HTMLParser

    src = (html or "").strip()
    if not src.lower().startswith("<table"):
        return ""

    class _S(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.out: List[str] = []
            self.depth = 0          # open allowed tags
            self.skip = 0           # inside a disallowed tag

        def handle_starttag(self, tag, attrs):
            if tag not in _TBL_ALLOWED_TAGS:
                # HTML void elements (img, input, hr, …) never get an end tag —
                # entering skip-mode for them would swallow the REST of the cell.
                if tag not in ("img", "input", "hr", "meta", "link", "area", "base",
                               "embed", "source", "track", "wbr"):
                    self.skip += 1
                return
            if self.skip:
                return
            keep = []
            for k, v in attrs:
                k = k.lower()
                if k in ("colspan", "rowspan") and str(v or "").isdigit():
                    keep.append(f'{k}="{v}"')
                elif k == "style":
                    cs = _clean_style(v or "")
                    if cs:
                        keep.append(f'style="{cs}"')
            self.out.append(f"<{tag}{(' ' + ' '.join(keep)) if keep else ''}>")
            if tag not in _TBL_VOID_TAGS:
                self.depth += 1

        def handle_startendtag(self, tag, attrs):
            if tag in _TBL_VOID_TAGS and not self.skip:
                self.out.append(f"<{tag}>")

        def handle_endtag(self, tag):
            if tag not in _TBL_ALLOWED_TAGS:
                if self.skip:
                    self.skip -= 1
                return
            if self.skip or tag in _TBL_VOID_TAGS:
                return
            if self.depth > 0:
                self.out.append(f"</{tag}>")
                self.depth -= 1

        def handle_data(self, data):
            if not self.skip and data:
                self.out.append(_html.escape(_html.unescape(data)))

        def handle_entityref(self, name):
            if not self.skip:
                self.out.append(f"&{name};")

        def handle_charref(self, name):
            if not self.skip:
                self.out.append(f"&#{name};")

    s = _S()
    try:
        s.feed(src)
        s.close()
    except Exception:
        return ""
    cleaned = "".join(s.out)
    if not cleaned.lower().startswith("<table") or "<tr" not in cleaned.lower():
        return ""
    return cleaned[:60000]


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t ]+")


def html_to_text(s: Optional[str]) -> str:
    """Strip tags → readable plain text. <br>, </p>, </div>, </tr> → newlines;
    </td>/</th> → a tab-like space so cells stay on one line but separated."""
    if not s:
        return ""
    if "<" not in s:
        return s.strip()
    t = s
    t = re.sub(r"(?i)<\s*br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</\s*(p|div|tr|li)\s*>", "\n", t)
    t = re.sub(r"(?i)</\s*(td|th)\s*>", "  |  ", t)
    t = _TAG_RE.sub("", t)
    t = _html.unescape(t)
    # collapse intra-line runs of spaces, trim trailing spaces per line, cap blanks
    lines = [_WS_RE.sub(" ", ln).rstrip() for ln in t.split("\n")]
    out: List[str] = []
    blank = 0
    for ln in lines:
        if ln.strip():
            blank = 0
            out.append(ln)
        else:
            blank += 1
            if blank <= 1:
                out.append("")
    return "\n".join(out).strip()


def _norm_ws(s: str) -> str:
    return _WS_RE.sub(" ", (s or "").replace("‌", " ")).strip()


def build_facts(customer: Any, profile_data: Dict[str, Any], facilities: List[Any],
                guarantors: List[Any]) -> Dict[str, Any]:
    """Compact, authoritative DB snapshot for the letter's account — the ground
    truth the model validates the letter against. Only plain, non-secret facts."""
    def ev(v):
        return getattr(v, "value", v)

    facts: Dict[str, Any] = {}
    if customer is not None:
        facts["customer"] = {
            "name": customer.name or "",
            "name_ar": getattr(customer, "name_ar", "") or "",
            "account_no": customer.account_no or "",
            "account_type": str(ev(getattr(customer, "account_type", "")) or ""),
            "branch": customer.branch or "",
        }
    if facilities:
        facts["facilities"] = [
            {
                "name": f.name or "",
                "type": str(ev(f.facility_type) or ""),
                "amount": (f"{float(f.amount):,.2f}" if f.amount is not None else ""),
                "currency": getattr(f, "currency", "") or "",
                "interest_rate": (f"{float(f.interest_rate):g}" if f.interest_rate is not None else ""),
                "tenor_months": str(f.tenor_months or ""),
                "installments": str(f.installments or ""),
                "purpose": f.purpose or "",
                "status": str(ev(f.status) or ""),
                "expiry_date": (str(f.expiry_date) if getattr(f, "expiry_date", None) else ""),
            }
            for f in facilities[:25]
        ]
    if guarantors:
        seen = set()
        gl = []
        for g in guarantors:
            key = ((g.guarantor_name or "").strip().lower(), (g.guarantor_account or "").strip())
            if not key[0] or key in seen:
                continue
            seen.add(key)
            gl.append({"name": (g.guarantor_name or "").strip(),
                       "account": (g.guarantor_account or "").strip(),
                       "cheque_no": (g.cheque_no or "").strip(),
                       "cheque_amount": (f"{float(g.cheque_amount):,.2f}" if g.cheque_amount is not None else "")})
        if gl:
            facts["guarantors"] = gl
    # A curated slice of the profile blob (avoid dumping 290 raw fields).
    if isinstance(profile_data, dict) and profile_data:
        keep = {}
        for k in ("POBox", "CityCountry", "Salutation", "business_type", "trade_license_no",
                  "trade_license_expiry", "proposed_facility", "proposed_amount",
                  "proposed_rate", "proposed_tenor"):
            for kk in (k, k.replace(" ", ""), k.lower()):
                v = profile_data.get(kk)
                if v not in (None, "", "-"):
                    keep[k] = str(v)
                    break
        if keep:
            facts["profile"] = keep
    return facts


SYSTEM_PROMPT = (
    "تو ویراستارِ بسیار دقیق و محافظه‌کارِ نامه‌های رسمیِ بانکی (بانک صادرات، فارسی/RTL) هستی. "
    "وظیفه‌ات پیشنهادِ اصلاحاتِ دقیق و قابل‌بازبینی روی نامه است. تو هرگز چیزی را مستقیم اعمال "
    "نمی‌کنی؛ فقط فهرستی از تغییراتِ پیشنهادی برمی‌گردانی که انسان آن‌ها را تیک می‌زند.\n"
    "قواعدِ سخت:\n"
    "1) خروجی فقط و فقط یک JSON معتبر باشد: {\"changes\": [ ... ]}. هیچ متنی بیرون از JSON ننویس.\n"
    "2) هر تغییر این کلیدها را دارد: category, field, op, title, detail, severity, "
    "find, replace, occurrence, before, after, applicable.\n"
    "3) op یکی از این‌هاست: \"text_replace\" (جایگزینیِ جراحی‌وارِ یک عبارتِ موجود)، "
    "\"set_field\" (جایگزینیِ کاملِ یک فیلدِ کوتاه)، \"note\" (فقط تذکر، بدونِ اعمال)، و — "
    "فقط اگر ابزارِ استخراج یا «اجرای دستورهای داخلِ متن» فعال باشد — \"db_write\" (ثبتِ یک واقعیتِ پروفایلی برای یک مشتری، "
    "با کلیدهای account_no/customer_name/key/value)؛ و فقط اگر «جدول‌های انتخاب‌شده» به تو داده "
    "شده باشد — \"table_replace\" (بازطراحیِ کاملِ یکی از همان جدول‌ها: کلیدهای table_index "
    "(شمارهٔ جدول در فهرستِ داده‌شده، از 1) و html (HTML کاملِ جدولِ جدید، فقط تگ‌های جدول/"
    "تأکیدِ ساده، بدون script/link/img)).\n"
    "4) برای op=text_replace، مقدارِ find باید «عیناً» از متنِ فعلیِ همان فیلد کپی شود (کاراکتر‌به‌کاراکتر) "
    "تا قابلِ یافتن باشد؛ کوتاه و یکتا نگه‌اش دار. اگر مطمئن نیستی عبارت دقیقاً وجود دارد، به‌جای آن note بده.\n"
    "5) op=set_field فقط برای فیلدهای کوتاه مجاز است، نه برای body.\n"
    "6) هیچ ادعای مالی/عددی جدیدی از خودت نساز؛ برای اعتبارسنجی فقط به «حقایق پایگاه‌داده» استناد کن. "
    "در شک، به‌جای اصلاح، note بده. title و detail فارسی و کوتاه باشند.\n"
    "7) فقط تغییراتِ واقعی و ارزشمند پیشنهاد بده؛ اگر چیزی برای اصلاح نیست، changes را خالی بگذار."
)

MAX_CHANGES = 60


MAX_SELECTIONS = 12


def build_user_prompt(fields: Dict[str, Any], facts: Dict[str, Any], tools: List[str],
                      instruction: str = "", selection: str = "",
                      selections: Optional[List[str]] = None,
                      tables: Optional[List[str]] = None) -> str:
    """Assemble the user message: the letter's plain-text fields + DB facts +
    the requested tools + optional free-form instruction and the user's SELECTED
    snippets. ``selections`` is the list the user gathered (many, separate pieces);
    ``selection`` is kept for back-compat and merged in as one more item."""
    parts: List[str] = []
    parts.append("### فیلدهای نامه (متنِ فعلی — برای text_replace از همین‌ها عیناً کپی کن):")
    field_lines = []
    for key, label in SCALAR_FIELDS.items():
        val = html_to_text(str(fields.get(key, "") or ""))
        if val:
            field_lines.append(f"- {key} ({label}): {val}")
    parts.append("\n".join(field_lines) or "(خالی)")

    body_txt = html_to_text(str(fields.get(BODY_FIELD, "") or ""))
    parts.append("\n### متنِ نامه (body):")
    parts.append(body_txt or "(خالی)")

    parts.append("\n### حقایقِ پایگاه‌داده (منبعِ حقیقت برای اعتبارسنجی):")
    parts.append(json.dumps(facts, ensure_ascii=False, indent=1) if facts else "(بدون رکورد مرتبط)")

    parts.append("\n### ابزارهای درخواستی (فقط روی این‌ها تمرکز کن):")
    guides = [f"- {TOOLS[t]['guide']}" for t in tools if t in TOOLS]
    parts.append("\n".join(guides) or "- اصلاحاتِ عمومیِ ویرایشی")

    # Gather the user's selected items (de-duped, order-preserving, capped).
    items: List[str] = []
    for s in ([selection] if selection else []) + list(selections or []):
        s = (s or "").strip()
        if s and s not in items:
            items.append(s[:2000])
        if len(items) >= MAX_SELECTIONS:
            break
    if items:
        parts.append(
            "\n### موارد انتخاب‌شده توسطِ کاربر برای اعتبارسنجی (هر مورد را جداگانه در برابرِ "
            "«حقایقِ پایگاه‌داده» بررسی کن؛ برای هرکدام یک change جدا بده — درست⇒note، غلط⇒اصلاح):"
        )
        for i, s in enumerate(items, 1):
            parts.append(f"{i}. «{s}»")

    # The user's SELECTED tables (raw HTML) — full AI control over these only.
    tbls = [t for t in (tables or []) if (t or "").strip()][:MAX_TABLES]
    if tbls:
        parts.append(
            "\n### جدول‌های انتخاب‌شده توسطِ کاربر (HTML فعلی — شماره‌ها برای table_index):"
        )
        for i, t in enumerate(tbls, 1):
            parts.append(f"[جدول {i}]\n{t[:20000]}")
        parts.append(
            "قواعدِ کار با جدول‌های انتخاب‌شده:\n"
            "- اگر «دستورِ اختصاصیِ کاربر» خواسته‌ای دربارهٔ جدول(ها) دارد، آن را کامل و همه‌جانبه "
            "اجرا کن — ساختاری و محتوایی هر دو: افزودن/حذف/ادغامِ سطر و ستون، تغییرِ چیدمان، "
            "سرستون، ترازبندی، عرضِ ستون‌ها (style)، مرتب‌سازی، تفکیک/ترکیبِ جدول‌ها — با یک "
            "op=\"table_replace\" برای هر جدولِ تغییرکرده (table_index از فهرستِ بالا؛ html کاملِ "
            "جدولِ جدید). محتوای واقعیِ داده‌ها را بدونِ دستورِ صریح تغییر نده و هیچ داده‌ای را "
            "از خودت نساز.\n"
            "- اگر دستور پر کردن/تکمیلِ محتوای جدول را می‌خواهد (مثلاً «جدول را با مشخصاتِ "
            "تسهیلات پر کن»)، تنها منبعِ مجازِ داده بخشِ «حقایقِ پایگاه‌داده» است: هر قلمِ "
            "خواسته‌شده را اول در حقایق جست‌وجو کن (customer/facilities/guarantors/profile)؛ "
            "اگر یافت شد، همان مقدارِ دقیقِ پایگاه‌داده را — با همان عدد/تاریخ/واحد/املا — در "
            "خانه بگذار؛ اگر یافت نشد، خانه را «—» بگذار و در یک note جداگانه "
            "(category=tables) دقیقاً فهرست کن کدام اقلام در پایگاه‌داده موجود نبود تا کاربر "
            "بداند. هرگز عدد، تاریخ، نام یا مبلغی را حدس نزن و نساز؛ اگر «حقایقِ پایگاه‌داده» "
            "خالی است (نامهٔ عمومی/بدونِ حساب)، این را در note بگو و جدول را با داده‌ی ساختگی "
            "پر نکن.\n"
            "- اگر دستورِ کاربر بخش‌های غیرمرتبط با جدول هم دارد، آن‌ها را جداگانه با opهای "
            "معمول (text_replace/set_field/note) پوشش بده — هیچ بخشی از دستور بی‌پاسخ نماند.\n"
            "- اگر دستورِ اختصاصی خالی است یا ربطی به جدول ندارد، table_replace نده؛ همان "
            "رفتارِ پیش‌فرضِ ابزارِ جداول را انجام بده (ناهماهنگی‌ها به‌صورت note، اصلاحِ "
            "محتواییِ جزئی با text_replace)."
        )

    if instruction.strip():
        parts.append("\n### دستورِ اختصاصیِ کاربر:")
        parts.append(instruction.strip()[:2000])

    parts.append("\nحالا فهرستِ تغییراتِ پیشنهادی را دقیقاً به‌صورتِ JSON {\"changes\":[...]} برگردان.")
    return "\n".join(parts)


def parse_and_validate(raw_text: str, fields: Dict[str, Any],
                       tables_count: int = 0) -> List[Dict[str, Any]]:
    """Parse the model's JSON reply and keep ONLY changes that are safe to apply.

    The hallucination guard: a ``text_replace`` is dropped unless its ``find`` is
    actually present in the current plain text of its target field. ``set_field``
    is restricted to the scalar allow-list. ``note`` is always kept (advisory).
    Returns a clean list with stable ids; drops anything malformed."""
    data = _loose_json(raw_text)
    changes = data.get("changes") if isinstance(data, dict) else None
    if not isinstance(changes, list):
        return []

    # Pre-compute plain text per field for the find-guard.
    plain: Dict[str, str] = {}
    for key in list(SCALAR_FIELDS) + [BODY_FIELD]:
        plain[key] = html_to_text(str(fields.get(key, "") or ""))

    out: List[Dict[str, Any]] = []
    for i, ch in enumerate(changes):
        if not isinstance(ch, dict):
            continue
        if len(out) >= MAX_CHANGES:
            break
        op = str(ch.get("op") or "").strip()
        field = str(ch.get("field") or "").strip()
        category = str(ch.get("category") or "other").strip().lower()
        if category not in VALID_CATEGORIES:
            category = "other"
        severity = str(ch.get("severity") or "medium").strip().lower()
        if severity not in VALID_SEVERITY:
            severity = "medium"
        title = str(ch.get("title") or "").strip()[:300]
        detail = str(ch.get("detail") or "").strip()[:1000]

        item: Dict[str, Any] = {
            "id": f"c{i}",
            "category": category,
            "field": field,
            "op": op,
            "title": title or "(بدون عنوان)",
            "detail": detail,
            "severity": severity,
            "applicable": False,
        }

        if op == "note":
            item["applicable"] = False
            out.append(item)
            continue

        if op == "table_replace":
            # Full redesign of ONE user-selected table. Valid only when tables
            # were actually provided; the HTML must survive the whitelist
            # sanitizer (scripts/handlers/links/images never reach the letter).
            try:
                ti = int(ch.get("table_index"))
            except (TypeError, ValueError):
                continue
            if not (1 <= ti <= tables_count):
                continue
            clean = sanitize_table_html(str(ch.get("html") or ""))
            if not clean:
                continue
            item["field"] = BODY_FIELD
            item["table_index"] = ti
            item["html"] = clean
            item["before"] = f"جدول {ti} (نسخهٔ فعلی)"
            item["after"] = "نسخهٔ بازطراحی‌شده — پیش‌نمایش زیر"
            item["applicable"] = True
            out.append(item)
            continue

        if op == "set_field":
            if field not in SCALAR_FIELDS:
                continue  # body/unknown → not settable wholesale
            after = ch.get("after")
            if after is None:
                continue
            item["after"] = str(after)
            item["before"] = str(ch.get("before") if ch.get("before") is not None else plain.get(field, ""))
            item["applicable"] = True
            out.append(item)
            continue

        if op == "text_replace":
            if field not in TEXT_FIELDS:
                continue
            find = ch.get("find")
            replace = ch.get("replace")
            if not isinstance(find, str) or not find.strip() or replace is None:
                continue
            haystack = plain.get(field, "")
            # Hallucination guard: the exact snippet must exist (verbatim, or with
            # whitespace/ZWNJ normalized). If it isn't there, we cannot locate it
            # safely on the client → drop the change.
            located = find in haystack or _norm_ws(find) in _norm_ws(haystack)
            if not located:
                continue
            occ = str(ch.get("occurrence") or "first").strip()
            if occ not in ("first", "all"):
                occ = "first"
            item["find"] = find
            item["replace"] = str(replace)
            item["occurrence"] = occ
            item["before"] = find
            item["after"] = str(replace)
            item["applicable"] = True
            out.append(item)
            continue
        # unknown op → skip
    return out


MAX_DB_WRITES = 40
_KEY_RE = re.compile(r"[^a-z0-9_]+")


def _norm_key(k: str) -> str:
    """Canonicalize a proposed profile key: lower snake_case, trimmed, capped."""
    k = (k or "").strip().lower().replace(" ", "_").replace("-", "_")
    k = _KEY_RE.sub("", k)
    return k[:60]


def parse_db_writes(raw_text: str) -> List[Dict[str, Any]]:
    """Pull the model's op=="db_write" proposals — the profile facts to persist.

    Returns raw (account_no, customer_name, key, value, title, detail) dicts,
    de-duped by (account_no, key). The DB resolution + add/update/skip decision is
    done later, against the live database, by the router/service — never here."""
    data = _loose_json(raw_text)
    changes = data.get("changes") if isinstance(data, dict) else None
    if not isinstance(changes, list):
        return []
    out: List[Dict[str, Any]] = []
    seen: set = set()
    for ch in changes:
        if not isinstance(ch, dict) or str(ch.get("op") or "").strip() != "db_write":
            continue
        key = _norm_key(str(ch.get("key") or ""))
        value = str(ch.get("value") or "").strip()
        if not key or not value:
            continue
        acc = str(ch.get("account_no") or "").strip()
        name = str(ch.get("customer_name") or "").strip()
        dedup = (acc.lower(), name.lower(), key)
        if dedup in seen:
            continue
        seen.add(dedup)
        out.append({
            "account_no": acc,
            "customer_name": name,
            "key": key,
            "value": value[:300],
            "title": str(ch.get("title") or "").strip()[:300],
            "detail": str(ch.get("detail") or "").strip()[:1000],
        })
        if len(out) >= MAX_DB_WRITES:
            break
    return out


def _loose_json(text: str) -> Dict[str, Any]:
    """Tolerant JSON parse: strips code fences/prose, grabs the outermost object."""
    if not text:
        return {}
    t = text.strip()
    t = re.sub(r"^```(?:json)?", "", t).strip()
    if t.endswith("```"):
        t = t[:-3].strip()
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        t = t[i:j + 1]
    try:
        out = json.loads(t)
        return out if isinstance(out, dict) else {}
    except Exception:
        return {}
