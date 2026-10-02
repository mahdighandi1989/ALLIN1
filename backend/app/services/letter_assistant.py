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

# v171 — «نوار دستورِ سریع» + دسترسیِ کاملِ دستیار به ظاهرِ فرم.
# The letter's look (sizes, positions, letterhead boxes, fonts, captions) lives in
# the page's `layout`/`labels`, NOT in the text fields — so the assistant could
# never change it. Two more review-first ops now reach it, validated by whitelist
# and clamped to sane ranges, so a model cannot push a box off the sheet:
#   set_layout — one layout box (logo/name/footer/body/…): x,y,w,h,size,…
#   set_label  — one printed caption («شماره :», «موضوع :» …)
LAYOUT_KEYS: Dict[str, str] = {
    "logo": "لوگو (سربرگ)", "name": "نامِ بانک (سربرگ)", "footer": "فوتر (پاورقیِ سربرگ)",
    "besmele": "بسمه تعالی", "shomareh": "شماره", "tarikh": "تاریخ", "peyvast": "پیوست",
    "recName": "نامِ گیرنده", "recTitle": "سمت/ادارهٔ گیرنده", "classification": "طبقه‌بندی",
    "subject": "موضوع", "separator": "خطِ جداکننده", "body": "متنِ نامه", "sender": "امضاکننده",
    "copyto": "رونوشت", "action": "اقدام‌کننده", "pagenum": "شمارهٔ صفحه",
}
LABEL_KEYS: Dict[str, str] = {
    "besmele": "بسمه تعالی", "shomareh": "شماره", "tarikh": "تاریخ", "peyvast": "پیوست",
    "classification": "طبقه‌بندی", "subject": "موضوع", "copyto": "رونوشت",
    "action": "اقدام‌کننده", "actionExt": "داخلیِ اقدام‌کننده",
}
# prop → (kind, lo, hi). Positions/sizes are CSS px on the A4 sheet (1mm ≈ 3.78px;
# the sheet is ~794×1123px).
LAYOUT_PROPS: Dict[str, tuple] = {
    "x": ("num", -50, 900), "y": ("num", -50, 1250),
    "w": ("num", 8, 900), "h": ("num", 1, 1250),
    "size": ("num", 5, 60), "ls": ("num", 0, 12), "lh": ("num", 1.0, 3.5),
    "indent": ("num", 0, 8), "contY": ("num", 0, 1250),
    "bold": ("bool",), "underline": ("bool",), "justify": ("bool",), "hidden": ("bool",),
    "align": ("enum", ("right", "center", "left")), "dir": ("enum", ("rtl", "ltr")),
}
MAX_LAYOUT_TOUCH = 30


def clean_layout_props(props: Any) -> Dict[str, Any]:
    """Whitelist + clamp a model-proposed layout patch. Unknown props/values are
    dropped, numbers are clamped into their range — never trusted as-is."""
    out: Dict[str, Any] = {}
    if not isinstance(props, dict):
        return out
    for k, v in props.items():
        spec = LAYOUT_PROPS.get(k)
        if not spec:
            continue
        if spec[0] == "num":
            if isinstance(v, bool) or not isinstance(v, (int, float, str)):
                continue
            try:
                n = float(v)
            except (TypeError, ValueError):
                continue
            if n != n or n in (float("inf"), float("-inf")):
                continue
            n = max(spec[1], min(spec[2], n))
            out[k] = round(n, 2) if k in ("ls", "lh", "indent") else int(round(n))
        elif spec[0] == "bool":
            if isinstance(v, bool):
                out[k] = v
        elif spec[0] == "enum":
            if isinstance(v, str) and v in spec[1]:
                out[k] = v
    return out

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
        "guide": (
            "چینش را «کل‌نگر» بررسی کن، نه جمله‌به‌جمله و جزیره‌ای — کلِ متن را از اول تا آخر بخوان و این سه را حتماً بگیر: "
            "(۱) ادامهٔ یک موضوع که به‌اشتباه در پاراگراف/خطِ جدا آمده یا جمله‌های پراکندهٔ یک موضوع در چند جای متن — این‌ها را با op=paragraph_merge به هم بدوز: "
            "parts = خودِ تکه‌های عیناً-موجود (هر تکه داخلِ یک پاراگراف؛ text_replace از مرزِ پاراگراف رد نمی‌شود)، replace = متنِ یکپارچه و روانِ نهایی؛ تکه‌های بعدی خودکار از جای قبلی حذف می‌شوند. "
            "(۲) اصلاح/بازچینشِ داخلِ یک پاراگراف با text_replace (نسخهٔ مرتبِ همان محتوا). "
            "(۳) جملهٔ ابتر/ناتمام (بی‌فعل، بریده، معلق‌مانده) را حتماً شناسایی کن: اگر ادامه‌اش جای دیگری در متن است با paragraph_merge وصلش کن؛ اگر از زمینه کامل‌شدنی است کاملش کن؛ وگرنه با یک note دقیق بگو کدام جمله ناقص است و چه اطلاعی کم است. "
            "چیزی از محتوای واقعی حذف یا اضافه نکن؛ فقط پیوند، چینش و کامل‌سازی (category=paragraphs)."
        ),
    },
    "tables": {
        "label": "بررسی و اصلاح جداول (ساخت/پر کردن/بازطراحی با دستور)",
        "guide": "ناهماهنگی محتوای جدول‌ها (سرستون‌ها، واحدها، ردیف‌های خالی) را گزارش کن؛ اصلاح محتوایی با text_replace. تغییرِ ساختاری: اگر همان جدول در «جدول‌های انتخاب‌شده» هست با op=table_replace کاملش را بازطراحی کن، وگرنه صرفاً note (category=tables). اگر دستورِ کاربر جدولِ «جدید» می‌خواهد با op=table_insert بساز. برای پر کردنِ محتوای جدول فقط از «حقایقِ پایگاه‌داده»، «محتوای پیوست‌های نامه» (اگر در پیام هست) یا خودِ دستورِ کاربر استفاده کن — قلمِ ناموجود را «—» بگذار و در note اعلام کن؛ هیچ داده‌ای نساز.",
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
            "کامل بده — معنا، اعداد و تعهدها را عوض نکن. در تعدادِ پیشنهادها محافظه‌کار نباش: "
            "همهٔ پاراگراف‌ها را یکی‌یکی ارزیابی کن و هر پاراگرافی که می‌تواند بهتر خوانده شود، "
            "بازنویسیِ کاملِ خودش را بگیرد؛ یک نامهٔ کوتاهِ اداری معمولاً چند پیشنهادِ بازنویسیِ "
            "جمله/پاراگراف می‌خواهد، نه فقط یکی. "
            "سنجهٔ کیفیت، متنِ نهاییِ سرهم‌شده است نه تک‌جمله‌ها: قبل از دادنِ پیشنهادها، نسخهٔ "
            "نهایی را ذهنی یک بار پیوسته بخوان — اگر واژه یا قالبی (جهت، اقدام، نسبت به، مقتضی است، "
            "نامِ یک سند/اداره…) در جمله‌های مجاور یا در پاراگراف‌های پشتِ‌سرِهم تکرار می‌شود، در "
            "همان پیشنهادها با مترادفِ اداری، ضمیر و اشاره (آن، مذکور، یادشده، موصوف) یا بازچینیِ "
            "جمله رفعش کن؛ تکرارِ بین‌پاراگرافی هم عیب است، نه فقط درونِ یک جمله. "
            "آهنگِ نثر را دلنشین کن: طولِ جمله‌ها را متنوع، شروعِ پاراگراف‌ها را غیرتکراری و "
            "پایان‌بندی را گرم و محترمانه — متن باید مثل نوشتهٔ یک نامه‌نگارِ باسابقهٔ بانکی خوانده "
            "شود، نه قالب‌های خشکِ پشتِ‌سرِهم (category=professional)."
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
            "جمله‌هایی از متن که «متنِ نامه» نیستند بلکه دستور یا خواستهٔ نویسنده‌اند را تشخیص بده — "
            "چه صریح («اینجا یه پاراگراف دربارهٔ وضعیت وثایق بنویس»، «این قسمت رو با ارقامِ تسهیلات "
            "پر کن»، «میخوام اینجا اشاره بشه که ...») و چه غیرصریح: هر جا نویسنده «دربارهٔ» چیزی که "
            "نامه باید بگوید حرف می‌زند به‌جای اینکه خودِ آن را بگوید — اول‌شخص و محاوره‌ای مثل "
            "«میخوام از اداره X که یه جوری به Y بگه که ...»، «باید یه جوری گفته بشه که ...»، "
            "«کاش اشاره بشه ...». این‌ها متنِ خام نیستند؛ نیتِ نویسنده‌اند و باید به متنِ رسمیِ نهاییِ "
            "خطاب‌شده به مخاطبِ درست تبدیل شوند و هیچ ردی از زبانِ نیت («میخوام...»، «یه جوری بگه») "
            "در نامه نماند. برای هر دستور یک text_replace "
            "بده که خودِ جملهٔ دستور را با متنِ خواسته‌شده جایگزین کند: رسمی، بانکی، هم‌لحنِ بقیهٔ "
            "نامه، و دقیقاً همان چیزی که دستور خواسته. اگر دستور به داده نیاز دارد، تنها منبعِ مجاز "
            "«حقایقِ پایگاه‌داده» است — قلمِ ناموجود را «________» بگذار و در detail بگو چه چیزی در "
            "پایگاه‌داده نبود؛ هیچ عدد/تاریخ/نامی نساز. اگر دستور می‌گوید داده‌ای در پرونده/پایگاه‌داده "
            "«ثبت شود»، علاوه بر متن، برای هر واقعیت یک op=\"db_write\" هم بده (همان قواعدِ ابزارِ "
            "استخراج: account_no/customer_name/key/value). اگر دستورِ داخلِ متن دربارهٔ «جدول» است "
            "(ساختن، پر کردن، تغییرِ سرستون/ساختار)، همان opهای جدول را بده — table_replace برای "
            "جدولِ انتخاب‌شده، table_insert برای جدولِ نو — با همان منابعِ مجازِ دادهٔ جدول‌ها "
            "(حقایقِ پایگاه‌داده، «محتوای پیوست‌های نامه» اگر در پیام هست، خودِ دستور) و جملهٔ "
            "دستور را با یک text_replace جداگانه از متن حذف کن. دستورهای مربوط به جاگیری در صفحه "
            "(«همه در یک صفحه بیفتد»، «اقدام‌کننده هم‌صفحه باشد») قابلِ اجرای تو نیستند — "
            "صفحه‌بندی و جایگاهِ بلوکِ پایانی خودکار است؛ فقط جملهٔ دستور را حذف کن و در یک note "
            "کوتاه بگو صفحه‌بندی خودکار انجام می‌شود. جملهٔ دستور نباید در متنِ نهایی بماند "
            "(category=inline_prompts)."
        ),
    },
    "validation": {
        "label": "اعتبارسنجی موردِ انتخاب‌شده با پایگاه‌داده",
        "guide": "موردِ انتخاب‌شده را در برابر «حقایق پایگاه‌داده» راستی‌آزمایی کن؛ اگر درست است note با severity=low و اگر غلط است اصلاحِ text_replace/set_field پیشنهاد بده (category=validation).",
    },
    "db_extract": {
        "label": "استخراج و ثبتِ داده‌های مفید در پروفایلِ مشتری(ها) و پایگاه دانش",
        "guide": (
            "داده‌های مفیدِ پروفایلی را از متنِ نامه استخراج کن و برای هرکدام یک تغییر با "
            "op=\"db_write\" بده. **با نهایت دقت**: یک نامه ممکن است چند مشتری را نام ببرد؛ هر "
            "واقعیت را فقط به مشتریِ درستش نسبت بده. برای هر db_write این کلیدها را بده: "
            "account_no (اگر شماره‌حسابِ آن مشتری در متن آمده؛ وگرنه خالی)، customer_name (نامِ "
            "همان مشتری)، key (نامِ فیلدِ کوتاهِ snake_case از این فهرست یا مشابهش: "
            + ", ".join(CANONICAL_KEYS) + ")، value (مقدارِ استخراج‌شده). "
            "فقط واقعیت‌های صریحِ متن؛ چیزی از خودت نساز. اگر واقعیتی به مشتریِ اصلیِ نامه ربط "
            "ندارد، account_no/customer_name همان مشتریِ دیگر را بگذار. (category=db_extract)\n"
            "  پایگاه دانش: جدا از واقعیت‌های پروفایلی، اگر در نامه یا پیوست‌ها محتوایی با "
            "ارزشِ عمومی/آموزشی هست (قاعده، رویه، بخشنامه، ضابطهٔ محاسبه، درسِ عملیاتی — نه "
            "دادهٔ خصوصیِ یک مشتری)، برای هر موضوع یک تغییر با op=\"kb_write\" بده با کلیدهای: "
            "topic (عنوانِ عام و ماندگارِ موضوع — محتوای مشابه باید ذیلِ یک عنوان جمع شود، نه "
            "هر جمله یک ردیف)، category (دسته: رویه/بخشنامه/محاسبات/وثایق/…)، content (متنِ "
            "منظم و کاملِ آموزشی — بازنویسیِ تمیزِ همان محتوا، بدونِ نامِ مشتری و دادهٔ خصوصی)، "
            "source_note (ارجاعِ دقیق: کدام نامه/پیوست و کدام بخش). فقط وقتی ارزشِ عمومیِ "
            "واقعی دارد؛ برای محتوای صرفاً موردی kb_write نده. (category=db_extract)"
        ),
    },
    "full_check": {
        "label": "بررسیِ کاملِ نامه و پیوست‌ها با پایگاه‌داده",
        "guide": (
            "بازرسِ مغایرت باش — همهٔ فیلدهای نامه، متنِ کاملِ نامه، جدول‌های پیوستِ داخلِ "
            "نامه و «محتوای پیوست‌ها» (اگر داده شده) را جزءبه‌جزء با «حقایقِ پایگاه‌داده» و با "
            "همدیگر مقایسه کن: مبالغ، نرخ‌ها، شماره‌حساب‌ها، نام‌ها، تاریخ‌ها، شماره‌نامه‌ها و "
            "ارجاع‌ها. هر مغایرت یک تغییرِ جدا: اگر اصلاح در متنِ نامه ممکن است text_replace "
            "با مقدارِ درست؛ اگر مغایرت در پیوست یا پایگاه‌داده است (متنِ نامه درست است یا "
            "منبعِ حقیقت نامشخص است) note با شرحِ دقیقِ دو مقدار و محلِ هرکدام — کاربر خودش "
            "تصمیم می‌گیرد کدام درست است. "
            "انطباقِ نامه با پیوست‌ها را هم بسنج: وقتی نامه بازتاب/انعکاسِ نامهٔ دیگری است، "
            "شماره و تاریخِ نامهٔ ارجاع‌شده، نامِ فرستنده/گیرندهٔ آن، مبالغ و خواسته‌ها باید "
            "عیناً با آنچه در پیوست آمده بخواند و توضیحِ نامه باید مفهومِ پیوست را کامل و "
            "درست منتقل کند — هر ناسازگاری (شمارهٔ نامهٔ غلط، تاریخِ ناهم‌خوان، خلاصهٔ "
            "ناقص/گمراه‌کننده) را با ذکرِ هر دو مقدار گزارش کن. اگر پیوستی داده نشده، فقط "
            "نامه را با پایگاه‌داده بسنج و در یک note کوتاه بگو پیوست‌ها در دسترس نبودند. "
            "(category=consistency)"
        ),
    },
}

# Internal tool: NOT listed in the assistant's tool picker (`TOOLS` feeds that);
# it is what the Quick-Command bar runs. Same ops, same validators, same reviewer —
# the bar is the assistant with a narrower, faster brief, so the two cannot disagree.
QUICK_TOOL = "quick"
QUICK_GUIDE = (
    "حالت «دستورِ سریع»: کاربر یک خواستهٔ کوتاه و موردی نوشته (و ممکن است یک یا چند کادر روی "
    "قسمت‌هایی از فرم کشیده باشد). فقط همان خواسته را اجرا کن، کامل و دقیق، و به چیزِ دیگری دست نزن: "
    "بازبینیِ کلیِ نامه، بازنویسی‌های سلیقه‌ای و اصلاحاتِ نامرتبط ممنوع است. "
    "هر خواسته را به opِ مناسب ترجمه کن: تغییرِ متن ⇒ text_replace/set_field/paragraph_merge؛ "
    "تغییرِ اندازه/جا/فونت/ترازبندی/سربرگ (لوگو، نامِ بانک، فوتر) ⇒ set_layout؛ تغییرِ عنوانِ چاپی "
    "(«شماره :» …) ⇒ set_label؛ جدول ⇒ table_replace/table_insert. "
    "«کادرهای انتخاب‌شده» را به‌عنوانِ محلِ خواسته بگیر: اگر خواسته درباره‌ی «اینجا/این/همین» است، "
    "همان کلیدهای layout و متنِ زیرِ کادر هدف‌اند. اگر کادری نکشیده یا مبهم است، از خودِ دستور و "
    "فهرستِ فیلدها/layout حدس بزن که کجا مقصود است و در title بنویس کدام را هدف گرفتی. "
    "برای «بزرگ‌تر/کوچک‌تر/بالاتر/پایین‌تر» مقدارِ فعلیِ layout را مبنا بگیر و مقدارِ مطلقِ نهایی بده. "
    "حذفِ جدول (داخلِ متن یا صفحهٔ پیوست) ⇒ table_delete؛ انتقالِ جدول بینِ متن و پیوست ⇒ "
    "table_delete روی جدولِ فعلی + table_insert با همان html و placementِ مقصد؛ تغییرِ «پیوست: "
    "دارد/ندارد» ⇒ set_field روی attachment. "
    "اگر بخشِ «دستورهای قبلیِ همین نامه» در پیام هست، دستورِ تازه را ادامهٔ همان گفت‌وگو بخوان: "
    "«دوباره/درستش کن/نه منظورم … بود/همان را/بله انجام بده» به همان موضوعِ قبلی برمی‌گردد؛ "
    "اگر قبلاً چیزی را پرسیده یا رد کرده بودی و کاربر حالا تأیید یا تکرار کرده، این‌بار اجرا کن. "
    "هر واحد را که با هیچ‌کدام از opهای بالا شدنی نیست، در یک note با دلیلِ فنیِ مشخص بگو "
    "(نه پرسشِ «در صورتِ تمایل»)."
)

# v178 — «دستورِ سریع … نمی‌فهمه و تمکین نمی‌کنه … بهونه میاره». The bar ran under
# SYSTEM_PROMPT, whose identity is «a conservative editor who never applies anything,
# only proposes; in doubt, give a note». A quick command IS the user's decision and
# is applied at once with a full undo — so under that identity the model kept
# answering an order with a polite advisory («در صورتِ تمایل اعلام فرمایید»). This
# preface takes precedence in quick mode only; the anti-hallucination rules stay.
QUICK_SYSTEM_PREFIX = (
    "### حالتِ «دستورِ سریع» — این بخش بر همهٔ قواعدِ پایین مقدم است\n"
    "در این حالت تو «مجری» هستی، نه پیشنهاددهنده: هر change که بدهی فوراً روی فرم اعمال "
    "می‌شود و کاربر با یک دکمه («برگشتِ دستور») همه را برمی‌گرداند. دستورِ کاربر خودش "
    "تأییدِ اوست. پس:\n"
    "- اجازه نگیر، نپرس «در صورتِ تمایل اعلام فرمایید»، تأییدِ دوباره نخواه، گزینه پیشنهاد "
    "نده — همان کاری را که خواسته شده کامل انجام بده.\n"
    "- عبارت‌های «تو هرگز چیزی را مستقیم اعمال نمی‌کنی»، «محافظه‌کار» و «در شک، note بده» در "
    "قواعدِ پایین در این حالت لغو است؛ قواعدِ سلیقه‌ایِ بازبینیِ کلی (۸ تا ۱۳ و ۱۶) فقط وقتی "
    "به کار می‌آیند که خودِ دستور بازنویسی/اصلاحِ متن بخواهد. هر مقداری را که کاربر صریحاً "
    "خواسته (امضاکننده، شعبه، عنوان، عدد، جمله) عیناً همان را بگذار، حتی اگر با پیش‌فرض‌های "
    "قاعدهٔ ۱۳ نخواند.\n"
    "- فقط دو چیز پابرجاست: find عیناً از متنِ فعلی کپی شود، و هیچ دادهٔ مالی/عددی از خودت "
    "نساز. note فقط برای بخشی که با هیچ opی شدنی نیست، با دلیلِ فنیِ مشخص.\n"
    "- حذفِ متن = text_replace با replace خالی؛ حذفِ جدول = table_delete؛ افزودنِ جمله کنارِ "
    "عبارتی موجود = text_replace که find همان عبارت و replace «عبارت + متنِ تازه» است.\n\n"
)


def _tool_guide(t: str) -> Optional[str]:
    if t == QUICK_TOOL:
        return QUICK_GUIDE
    return TOOLS[t]["guide"] if t in TOOLS else None


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

# v123 — ATTACHMENT BUDGETS. The owner's report: a letter with 12 attachments
# had its table filled from only 10 of them. Root cause: this module dropped
# attachments past a hard `[:10]` and trimmed each text at 20k chars, ALL
# SILENTLY — neither the model nor the user was told anything was missing, so
# an incomplete answer looked like a complete one.
#
# Rules now (mirroring the generator's proven v114 `fit_sources`):
#   * NO fixed count cap while a fair share of the budget still fits — with N
#     attachments each gets TOTAL//N, so 12 of 12 are present. Being trimmed is
#     far better than being absent: the user's table has one row PER attachment.
#   * Whatever is still cut is announced LOUDLY — inside the prompt (so the
#     model reports it instead of quietly summarising) and back to the caller
#     as warnings the UI shows as review rows.
ATT_TOTAL_CAP = 360_000      # same total prompt budget the generator proved
ATT_FILE_CAP = 60_000        # no single attachment may eat the whole budget
ATT_MIN_CHARS = 4_000        # below this a "share" is useless — cap the count instead
ATT_TBL_CAP = 15_000         # per in-flow attachment table


def fit_attachments(attachments_text, attachment_tables):
    """Fit EVERY attachment into the prompt budget, applied ONCE.

    Returns ``([(name, fitted_text)], [table_html], warnings)`` — build_user_prompt
    renders exactly this and the endpoint surfaces the same warnings, so the
    prompt and the API reply can never disagree about what the model saw."""
    atts = [a for a in (attachments_text or [])
            if isinstance(a, dict) and (a.get("text") or "").strip()]
    warns: List[str] = []
    n = len(atts)
    used = atts
    if n:
        share = ATT_TOTAL_CAP // n
        if share < ATT_MIN_CHARS:
            # Too many to give each a usable share: only NOW is a count cap
            # justified — and it is reported, never silent.
            keep = max(1, ATT_TOTAL_CAP // ATT_MIN_CHARS)
            warns.append(
                f"تعدادِ پیوست‌ها ({n}) از ظرفیتِ یک درخواست بیشتر است — فقط {keep} پیوستِ نخست به مدل رسید. "
                "برای پوششِ کامل، پیوست‌ها را در دو یا چند نوبت تحلیل کن."
            )
            used = atts[:keep]
            share = ATT_MIN_CHARS
        per = min(ATT_FILE_CAP, share)
        out = []
        for a in used:
            nm = str(a.get("name") or "پیوست")[:120]
            txt = str(a.get("text") or "")
            cut = txt[:per]
            if len(txt) > len(cut):
                warns.append(
                    f"متنِ پیوست «{nm}» کامل به مدل نرسید ({len(cut):,} از {len(txt):,} نویسه) — "
                    "اگر ردیف‌های این پیوست ناقص پر شد، همین علت است."
                )
            out.append((nm, cut))
    else:
        out = []
    tbls_in = [t for t in (attachment_tables or []) if (t or "").strip()]
    tbls = [t[:ATT_TBL_CAP] for t in tbls_in]
    if any(len(a) > ATT_TBL_CAP for a in tbls_in):
        warns.append("یک یا چند جدولِ پیوستِ داخلِ نامه بسیار بزرگ بود و بریده شد.")
    return out, tbls, warns


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


def _fold_heh(s: str) -> str:
    """Match-only fold: the editor stores the precomposed «ۀ» (U+06C0 —
    B Nazanin cannot anchor the combining U+0654) while models often emit
    ه+U+0654. NEVER used for display — only so both forms locate the same
    text in the hallucination guards."""
    return (s or "").replace("\u0654", "").replace("\u06c0", "\u0647")


def _norm_ws(s: str) -> str:
    # whitespace/ZWNJ collapse + Arabic-vs-Persian yeh/kaf canonicalization —
    # the model often emits ي/ك or plain spaces where the letter has ی/ک/ZWNJ
    s = (s or "").replace("‌", " ").replace("\u00a0", " ")
    s = s.replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")
    return _WS_RE.sub(" ", s).strip()


def _row_facts(row: Any, skip: tuple = ("id", "account_no", "customer_name", "created_by",
                                        "date_added", "is_deleted", "created_at",
                                        "content_norm", "title_norm")) -> Dict[str, Any]:
    """Generic, schema-driven view of an ORM row for the facts JSON: every
    non-empty column except housekeeping. A column added to the model later is
    AUTOMATICALLY available to the model — no facts-builder edit needed."""
    out: Dict[str, Any] = {}
    for col in row.__table__.columns:
        if col.name in skip:
            continue
        v = getattr(row, col.name, None)
        if v in (None, ""):
            continue
        try:
            from decimal import Decimal
            if isinstance(v, Decimal):
                v = f"{float(v):,.2f}"
        except Exception:
            pass
        out[col.name] = str(v)
    return out


def build_facts(customer: Any, profile_data: Dict[str, Any], facilities: List[Any],
                guarantors: List[Any], properties: Optional[List[Any]] = None,
                property_events: Optional[List[Any]] = None,
                fixed_deposits: Optional[List[Any]] = None,
                partners: Optional[List[Any]] = None,
                audit_logs: Optional[List[Any]] = None,
                journal_entries: Optional[List[Any]] = None) -> Dict[str, Any]:
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
    # Mortgaged properties — EVERY column generically (schema-driven, so new
    # columns like postal_code/owner_national_id and any future ones flow in
    # automatically) + the full dated EVENT TIMELINE per property (several
    # valuations, mortgage/re-mortgage/release/insurance…).
    if properties:
        ev_by_prop: Dict[str, List[Dict[str, Any]]] = {}
        for e in (property_events or []):
            ev_by_prop.setdefault(e.property_id, []).append({
                "event_type": e.event_type, "date": e.event_date or "",
                **({"amount": f"{float(e.amount):,.2f}"} if e.amount is not None else {}),
                **({"currency": e.currency} if e.currency else {}),
                **({"remarks": e.remarks} if e.remarks else {}),
            })
        pl = []
        for p in properties[:20]:
            d = _row_facts(p)
            evs = ev_by_prop.get(p.id) or []
            if evs:
                d["history"] = evs[:30]
            pl.append(d)
        if pl:
            facts["properties"] = pl
    if fixed_deposits:
        facts["fixed_deposits"] = [_row_facts(fd) for fd in fixed_deposits[:20]]
    if partners:
        facts["partners"] = [_row_facts(pt) for pt in partners[:20]]
    # The account's ACTIVITY LOGS — so a request like «آخرین کارهای انجام‌شده
    # روی این حساب را فهرست کن» can be answered from the DB, not invented.
    # account_activity_log = audit trail rows (who did what, newest first);
    # journal_log = per-customer workflow/daily-log lines routed to the account.
    if audit_logs:
        facts["account_activity_log"] = [
            {
                "when": str(getattr(a, "created_at", "") or ""),
                "user": getattr(a, "username", "") or "",
                "action": getattr(a, "action", "") or "",
                "entity": getattr(a, "entity_type", "") or "",
                "detail": _norm_ws(str(getattr(a, "detail", "") or ""))[:300],
            }
            for a in audit_logs[:40]
        ]
    if journal_entries:
        facts["journal_log"] = [_row_facts(j) for j in journal_entries[:40]]
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
    "تأکیدِ ساده، بدون script/link/img)) و \"table_delete\" (حذفِ کاملِ یکی از همان جدول‌ها — "
    "داخلِ متن یا صفحهٔ پیوست — فقط وقتی دستورِ کاربر حذفش را خواسته: کلیدِ table_index)؛ "
    "و — فقط وقتی «دستورِ اختصاصیِ کاربر» ساختِ جدولِ "
    "«جدید» را می‌خواهد — \"table_insert\" (ساختِ یک جدولِ نو: کلیدهای html (HTML کاملِ جدول، "
    "همان محدودیت‌های table_replace)، table_title (عنوانِ اختیاریِ بالای جدول) و placement: "
    "\"body\" یعنی داخلِ متنِ نامه (جدولِ کوچک/مرتبط با متن) یا \"attachment\" یعنی صفحهٔ "
    "پیوستِ جداگانه بعد از صفحهٔ آخر (جدولِ پهن/پرردیف یا وقتی کاربر گفته پیوست). دادهٔ "
    "خانه‌ها همان قواعدِ پر کردنِ جدول را دارد: فقط از «حقایقِ پایگاه‌داده»، «محتوای "
    "پیوست‌های نامه» (اگر در پیام هست) یا خودِ دستورِ کاربر — قلمِ ناموجود «—» + note؛ "
    "ظاهر مرتب: سرستونِ روشن، ترازبندی و عرضِ ستون‌ها با style)؛ و \"paragraph_merge\" "
    "(دوختنِ تکه‌های پراکندهٔ «یک» موضوع که به‌اشتباه در پاراگراف‌ها/خط‌های جدا افتاده‌اند: "
    "کلیدهای parts (آرایهٔ ۲ تا ۶ عبارتِ «عیناً موجود» در متن — هر عبارت کاملاً داخلِ یک "
    "پاراگرافِ واحد، بدونِ گذر از مرزِ پاراگراف) و replace (متنِ یکپارچه، مرتب و روانِ نهایی "
    "که به‌جای تکهٔ اول می‌نشیند؛ تکه‌های بعدی خودکار از جای قبلی‌شان حذف می‌شوند). این تنها "
    "راهِ جابه‌جایی/ادغامِ بینِ پاراگراف‌هاست — text_replace نمی‌تواند از مرزِ پاراگراف بگذرد).\n"
    "4) برای op=text_replace، مقدارِ find باید «عیناً» از متنِ فعلیِ همان فیلد کپی شود (کاراکتر‌به‌کاراکتر) "
    "تا قابلِ یافتن باشد؛ کوتاه و یکتا نگه‌اش دار. اگر مطمئن نیستی عبارت دقیقاً وجود دارد، به‌جای آن note بده.\n"
    "5) op=set_field فقط برای فیلدهای کوتاه مجاز است، نه برای body.\n"
    "6) هیچ ادعای مالی/عددی جدیدی از خودت نساز؛ برای اعتبارسنجی فقط به «حقایق پایگاه‌داده» استناد کن. "
    "در شک، به‌جای اصلاح، note بده. title و detail فارسی و کوتاه باشند.\n"
    "7) فقط تغییراتِ واقعی و ارزشمند پیشنهاد بده؛ اگر چیزی برای اصلاح نیست، changes را خالی بگذار.\n"
    "8) اصلِ نتیجهٔ نهایی: وقتی متن آشفته است (محاوره، جمله‌های پراکنده، دستورهای نویسنده وسطِ متن، "
    "نقل‌قول‌های درهم)، پیشنهادهایت را طوری طراحی کن که اگر کاربر همه را تیک بزند، حاصل یک نامهٔ اداریِ "
    "کامل، منسجم و آماده‌ی امضا باشد — نه مجموعه‌ای از وصله‌های جدا. متن را ذهنی پاراگراف‌به‌پاراگراف "
    "بازسازی کن و هر پاراگرافِ نهایی را با یک text_replace روی معادلِ فعلی‌اش بده؛ اگر تکه‌های یک "
    "موضوع در چند پاراگرافِ جدا افتاده‌اند با paragraph_merge به هم بدوزشان؛ ترتیبِ منطقی "
    "(مقدمه/استناد، اصلِ درخواست، اقدامِ خواسته‌شده، پایان‌بندی) را رعایت کن. در پایان، متنِ "
    "سرهم‌شده را یک بار ذهنی از اول تا آخر بخوان: هیچ جملهٔ ناتمام/ابتر، ادامهٔ جامانده در "
    "پاراگرافِ اشتباه، یا ترتیبِ نامنطقی نباید باقی بماند. معنا، مبالغ، تاریخ‌ها و "
    "تعهدها را تغییر نده و چیزی از خودت نساز.\n"
    "9) سلسله‌مراتبِ مخاطب: از فیلدهای گیرنده (نام، سمت، اداره) و بافتِ نامه جایگاهِ مخاطب نسبت به "
    "امضاکننده را تشخیص بده و صیغهٔ درخواست را با آن هماهنگ کن. خطاب به مقام/ادارهٔ بالادستی فقط "
    "زبانِ گزارش و استدعاست: «به استحضار می‌رساند»، «خواهشمند است دستور فرمایید»، «در صورت صلاحدید»، "
    "«موجب امتنان خواهد بود» — هرگز صیغهٔ دستوری/تکلیفی مانند «مقتضی است آن اداره…»، «لازم است»، "
    "«اقدام نمایید» به بالادستی نگو؛ کاری هم که باید توسط شخصِ ثالث انجام شود، از بالادستی «صدورِ "
    "دستور» به آن مرجع را درخواست کن، نه انجامِ مستقیم را. خطاب به هم‌تراز «خواهشمند است دستور "
    "اقدام فرمایید» و فقط خطاب به زیرمجموعه «مقتضی است / دستور داده می‌شود» بگو. اگر متنِ فعلی این "
    "را رعایت نکرده، اصلاحش پیشنهاد بده.\n"
    "10) تنوعِ واژگانی در نتیجهٔ نهایی: متنِ سرهم‌شده (با فرضِ تیکِ همهٔ پیشنهادها) نباید یک واژه یا "
    "قالبِ اداری را در جمله‌ها/پاراگراف‌های مجاور تکرار کند؛ با مترادف، ضمیر و اشاره (آن، مذکور، "
    "یادشده) یا بازچینی، تنوع بده — بدونِ تغییرِ معنا.\n"
    "11) هنرِ درخواستِ اداری — چهار قانونِ سختِ جمله‌سازی برای هر جملهٔ درخواست:\n"
    "  الف) یک نامه یک هستهٔ درخواست دارد: همهٔ خواسته‌هایی که مقصدشان یکی است را در «یک» جملهٔ "
    "درخواستِ منسجم بچین (با «ضمن»، «و»، «همچنین»)؛ «خواهشمند است» در کلِ نامه حداکثر یک بار بیاید "
    "مگر مقصدها واقعاً جدا باشند.\n"
    "  ب) زنجیرهٔ مجهولِ تودرتو ممنوع: «اعلام گردد که ... اقدام نمایند» و امثالش کودکانه است. "
    "به‌جایش ساختِ روشن: «مراتب/جدولِ پیوست به [مرجع] ابلاغ/ارسال گردد تا [کارِ مشخص] را انجام و "
    "نتیجه را به [این اداره] اعلام نماید».\n"
    "  پ) عبارتِ توخالی ممنوع: «جهت انجام اقدامات لازم»، «اقدامات مقتضی معمول گردد» و مانندش را "
    "با خودِ کارِ مشخصِ خواسته‌شده جایگزین کن (از متن/بافتِ نامه بگیر: تمدید، صدور، ارسال، بررسی…).\n"
    "  ت) هر جملهٔ درخواست باید بدونِ ابهام بگوید: چه‌کسی، چه کاری، با چه هدفی، و نتیجه به کجا "
    "گزارش شود.\n"
    "  نمونهٔ بد ⇒ خوب (الگوی ساخت، نه متنِ آماده — با محتوای همان نامه پرش کن):\n"
    "  • بد: «خواهشمند است دستور فرمایید به شرکت X اعلام گردد که نسبت به اخذ مجوز اقدام نمایند.» "
    "خوب: «خواهشمند است دستور فرمایید مراتب به شرکت X ابلاغ گردد تا ضمن بررسی، مجوزهای لازم را "
    "اخذ و نتیجه را به این اداره اعلام نماید.»\n"
    "  • بد: «جدول یادشده به شرکت X جهت انجام اقدامات لازم ارسال گردد.» "
    "خوب: «جدول پیوست برای تمدید/صدور بیمه‌نامه‌های موضوعِ نامه به شرکت X ارسال گردد.»\n"
    "  • بد: دو جملهٔ پشتِ‌سرِهم که هر دو با «خواهشمند است دستور فرمایید» شروع می‌شوند. "
    "خوب: یک جمله: «خواهشمند است دستور فرمایید جدول پیوست به شرکت X ارسال و به آن شرکت ابلاغ "
    "گردد تا ضمن تمدید پوشش‌های پیشین، امکان [خواستهٔ دوم] را نیز بررسی و نتیجه را به این "
    "سرپرستی اعلام نماید.»\n"
    "12) نقطه‌گذاری، جملهٔ بسته و پاراگراف — نثرِ اداری با علائم نفس می‌کشد:\n"
    "  الف) هر جمله «یک» گزاره دارد و با نقطه بسته می‌شود؛ جملهٔ کش‌داری که چند خواسته را بدونِ "
    "مکث به هم می‌دوزد («... صورت پذیرد همچنین شایان ذکر است ...») ممنوع — قبل از «همچنین/ضمناً/"
    "شایان ذکر است» جملهٔ قبلی را با نقطه ببند یا با «؛» جدا کن.\n"
    "  ب) ویرگولِ فارسی («،») را بگذار: بعد از قید/عبارتِ آغازین («در این خصوص،»، «با عنایت به "
    "شرایط موجود،»)، دو طرفِ عبارتِ معترضه، و بین جمله‌واره‌ها؛ نبودِ ویرگول همان‌قدر عیب است که "
    "زیادی‌اش.\n"
    "  پ) حشوِ انباشته ممنوع: دو واژهٔ هم‌معنا پشتِ هم («اقدامات لازم مقتضی»، «جهت ... به منظور ...» "
    "در یک جمله) یکی‌اش حذف شود.\n"
    "  ت) پاراگراف‌بندی را حفظ کن: هر پاراگراف یک کار (استناد/زمینه، ایفادِ پیوست، درخواست، "
    "پایان‌بندی). find و replace هر پیشنهاد باید داخلِ مرزِ همان پاراگراف بماند — هرگز چند "
    "پاراگراف را در یک replace ادغام نکن و متنِ پاراگراف‌های مجاور را در یک جملهٔ واحد نچسبان.\n"
    "13) درستیِ امضاکننده (sender): این نامه‌ها از «بانک صادرات — سرپرستی منطقه خلیج فارس» و "
    "شعب/دوایرِ زیرمجموعه‌اش صادر می‌شوند و فیلد sender فقط دو مقدارِ مجاز دارد. قاعدهٔ کلی: "
    "اگر گیرنده بیرون از این مجموعه است (ادارهٔ کل/سازمان/شرکت/بانکِ دیگر، نهادِ دولتی، "
    "بیمه، مشتری…) امضاکنندهٔ درست «سرپرستی منطقه خلیج فارس» است؛ اگر مکاتبهٔ داخلیِ خودِ "
    "مجموعه است (بین شعب و دوایرِ همین سرپرستی) امضاکنندهٔ درست «دایره تسهیلات اعطایی» است. "
    "اگر sender فعلی با این قاعده نمی‌خواند، یک پیشنهادِ op=set_field برای field=sender با "
    "مقدارِ درست بده (category=consistency, severity=high) و در detail دلیل را بنویس؛ چون "
    "استثنا ممکن است، این فقط پیشنهاد است و کاربر تصمیم می‌گیرد. اگر جایگاهِ گیرنده مبهم بود، "
    "به‌جای set_field یک note بده.\n"
    "14) op=\"kb_write\" فقط وقتی ابزارِ استخراج فعال است مجاز است: ثبتِ محتوای عمومی/آموزشی "
    "در پایگاه دانش با کلیدهای topic/category/content/source_note (شرحِ کامل در راهنمای همان "
    "ابزار). دادهٔ خصوصیِ مشتری هرگز در kb_write نمی‌آید.\n"
    "15) جستجوی کاملِ لاگ‌ها (need_logs): کلیدهای account_activity_log/journal_log در «حقایقِ "
    "پایگاه‌داده» فقط برشِ اخیرند. اگر دستورِ کاربر به لاگ‌ها/کارهای انجام‌شده اشاره دارد و این برش "
    "کافی نیست (قدیمی‌تر، کاربر/بازهٔ خاص، حسابِ دیگر یا کلِ سیستم)، به‌جای خروجیِ معمول فقط این JSON "
    "را برگردان تا سرور روی «کلِ» لاگ‌ها جستجو کند و نتیجه را بدهد:\n"
    "{\"need_logs\": {\"scope\": \"audit\"|\"journal\"|\"both\", \"account_no\": \"\", \"text\": \"\", "
    "\"user\": \"\", \"action\": \"\", \"date_from\": \"YYYY-MM-DD\", \"date_to\": \"YYYY-MM-DD\"}}\n"
    "همهٔ فیلترها اختیاری‌اند (خالی = همه). این فرصت فقط یک بار است: در نوبتِ بعد «نتایجِ جستجوی "
    "لاگ‌ها» را می‌گیری و باید خروجیِ نهایی را بدهی؛ اگر شمارِ یافته‌ها از سقفِ ارسال بیشتر بود در "
    "warnings همان پیام آمده — فیلتر را در همان نوبتِ اول درست انتخاب کن. هرگز به‌جای need_logs "
    "دادهٔ لاگ نساز.\n"
    "16) لحنِ بازنویسی از آرشیوِ خودِ اداره: اگر بخشِ «نمونه‌نامه‌های آرشیو» در پیام هست، هر "
    "جمله‌ای که پیشنهاد می‌دهی باید هم‌جنسِ همان نامه‌ها باشد — همان فاصلهٔ رسمی، همان قالب‌های "
    "آغاز/استناد/درخواست/پایان‌بندی، همان آهنگ و پختگیِ جمله. پیش از نوشتنِ هر replace، جمله‌ات "
    "را ذهنی کنارِ نمونه‌ها بگذار؛ اگر در آن نامه‌ها چنین جمله‌ای نمی‌نشیند (خام، محاوره‌ای، "
    "شتاب‌زده)، بازنویسی‌اش کن تا بنشیند. از نمونه‌ها فقط «سبک» را بردار: هیچ نام/عدد/تاریخ/"
    "تعهد/موضوعی از آن‌ها به این نامه نیاور و محتوایشان را واقعیت تلقی نکن."
)


def parse_need_logs(raw_text: str) -> Optional[Dict[str, str]]:
    """Detect a need_logs request in the model's reply (rule 15) — None when
    the reply is a normal changes payload. The returned query is sanitized."""
    data = _loose_json(raw_text or "")
    need = data.get("need_logs") if isinstance(data, dict) else None
    if not isinstance(need, dict):
        return None
    from app.services.log_search import sanitize_query
    return sanitize_query(need)

MAX_CHANGES = 60


MAX_SELECTIONS = 12


MAX_STYLE_SAMPLES = 3
MAX_STYLE_CHARS = 1500



LAYOUT_ADDENDUM = (
    "\n12) opهای ظاهرِ فرم (فقط وقتی بخشِ «ظاهرِ فعلیِ فرم» در پیام هست و دستورِ اختصاصیِ کاربر "
    "صریحاً تغییرِ ظاهر می‌خواهد): \"set_layout\" (field = یکی از کلیدهای layout، props = شیءِ "
    "مقدارهای مطلقِ جدید مثل {\"size\":14} یا {\"w\":300,\"h\":90}؛ برای هر جعبه فقط یک change) و "
    "\"set_label\" (field = کلیدِ عنوانِ چاپی، after = متنِ جدید). سربرگ = کلیدهای logo/name/footer: "
    "تغییرِ اندازه‌شان با w/h و جایشان با x/y. مقدار را از عددهای فعلیِ همان بخش بساز و از محدودهٔ برگه "
    "بیرون نزن. تغییرِ ظاهر را با تغییرِ متن قاطی نکن — هرکدام change جدا. برای این opها "
    "find/replace لازم نیست.\n"
)


def _layout_section(layout: Dict[str, Any], labels: Dict[str, Any]) -> str:
    """The form's CURRENT look, so set_layout/set_label can be expressed as absolute
    values. Only whitelisted keys/props are echoed (the client is not trusted)."""
    lines = [
        "\n### ظاهرِ فعلیِ فرم (layout — واحدها px روی برگهٔ A4 با عرض≈۷۹۴ و ارتفاع≈۱۱۲۳؛ "
        "هر میلی‌متر≈۳٫۷۸px). دسترسی به این بخش فقط وقتی مجاز است که «دستورِ اختصاصیِ کاربر» "
        "صریحاً تغییرِ اندازه/جا/فونت/سربرگ/عنوانِ چاپی می‌خواهد — خودسرانه ظاهر را تغییر نده:",
        "op=\"set_layout\": کلیدهای field (یکی از کلیدهای زیر) و props (شیءِ مقدارهای مطلقِ جدید — "
        "فقط از x,y,w,h,size(پوینت),ls,lh,indent,contY,bold,underline,justify,hidden,align,dir)؛ "
        "فقط ویژگی‌هایی که باید عوض شوند را بده. op=\"set_label\": field (کلیدِ عنوانِ چاپی) و after.",
    ]
    n = 0
    for k, fa_name in LAYOUT_KEYS.items():
        box = layout.get(k)
        if not isinstance(box, dict):
            continue
        cur = {pk: box[pk] for pk in LAYOUT_PROPS if pk in box and box[pk] is not None}
        lines.append(f"- {k} ({fa_name}): {json.dumps(cur, ensure_ascii=False)}")
        n += 1
        if n >= 40:
            break
    lab = {k: str(labels[k])[:60] for k in LABEL_KEYS if k in labels}
    if lab:
        lines.append("عنوان‌های چاپیِ فعلی (set_label): " + json.dumps(lab, ensure_ascii=False))
    return "\n".join(lines)


def _spots_section(spots: List[Dict[str, Any]], hints: Dict[str, Any]) -> str:
    """The boxes the owner drew (and what the page knows they were looking at)."""
    lines = ["\n### کادرهای انتخاب‌شده توسطِ کاربر روی فرم (محلِ خواسته؛ مختصات نسبت به برگه):"]
    if not spots:
        lines.append("هیچ کادری کشیده نشده — محلِ خواسته را از دستور و فهرستِ فیلدها/layout حدس بزن.")
    for i, sp in enumerate(spots[:8], 1):
        if not isinstance(sp, dict):
            continue
        keys = [k for k in (sp.get("layout_keys") or []) if k in LAYOUT_KEYS][:6]
        rect = sp.get("rect") if isinstance(sp.get("rect"), dict) else {}
        r = {k: rect.get(k) for k in ("x", "y", "w", "h") if isinstance(rect.get(k), (int, float))}
        txt = str(sp.get("covered_text") or "").strip()[:400]
        tix = [int(t) for t in (sp.get("table_indexes") or [])
               if isinstance(t, (int, float)) and not isinstance(t, bool) and 1 <= int(t) <= MAX_TABLES][:4]
        lines.append(
            f"{i}. صفحهٔ {sp.get('page') or '؟'} — کلیدهای layoutِ زیرِ کادر (بیشترین هم‌پوشانی اول): "
            f"{', '.join(keys) or 'هیچ (خارج از برگه/نوارِ ابزار)'} — مختصاتِ کادر روی برگه (px): "
            f"{json.dumps(r)} — بخشِ صفحه: {str(sp.get('section') or '')[:60] or '—'}"
            + (f" — متنِ زیرِ کادر: «{txt}»" if txt else "")
            + (f" — ⟵ این کادر روی جدولِ شمارهٔ {', '.join(str(t) for t in tix)} از فهرستِ «جدول‌های فرم» است "
               "(اگر دستور دربارهٔ «این/همین» است، هدف همین جدول است)" if tix else ""))
    sel = str(hints.get("selected_text") or "").strip()[:600]
    if sel:
        lines.append(f"متنی که کاربر همین حالا در نامه انتخاب کرده (اگر دستور «این» می‌گوید مقصود همین است): «{sel}»")
    sk = str(hints.get("selected_layout_key") or "")
    if sk in LAYOUT_KEYS:
        lines.append(f"فیلدی که کاربر در حالتِ چیدمان انتخاب کرده: {sk} ({LAYOUT_KEYS[sk]})")
    return "\n".join(lines)


MAX_HISTORY = 4


def _history_section(history: List[Dict[str, Any]]) -> str:
    """v178 — the quick bar's previous turns on THIS letter. Without them every
    request was a stranger: «دوباره»، «نه، منظورم جدولِ دوم بود»، «بله انجام بده»
    pointed at nothing, and the model answered the second request blind."""
    lines = ["\n### دستورهای قبلیِ همین نامه (قدیمی‌تر اول؛ آنچه «اعمال شد» الان در متن/فرمِ فعلی هست — "
             "دستورِ تازه را ادامهٔ همین گفت‌وگو بخوان):"]
    for i, h in enumerate([x for x in history if isinstance(x, dict)][-MAX_HISTORY:], 1):
        ins = str(h.get("instruction") or "").strip()[:400]
        if not ins:
            continue
        app_ = [str(a).strip()[:160] for a in (h.get("applied") or []) if str(a).strip()][:8]
        notes = [str(n).strip()[:300] for n in (h.get("notes") or []) if str(n).strip()][:4]
        lines.append(f"{i}. کاربر: «{ins}»")
        lines.append("   اعمال شد: " + ("؛ ".join(app_) if app_ else "هیچ"))
        if notes:
            lines.append("   پاسخِ تو: " + " | ".join(notes))
    return "\n".join(lines)


def build_user_prompt(fields: Dict[str, Any], facts: Dict[str, Any], tools: List[str],
                      instruction: str = "", selection: str = "",
                      selections: Optional[List[str]] = None,
                      tables: Optional[List[str]] = None,
                      attachments_text: Optional[List[Dict[str, str]]] = None,
                      attachment_tables: Optional[List[str]] = None,
                      style_samples: Optional[List[Dict[str, str]]] = None,
                      warnings_out: Optional[List[str]] = None,
                      layout: Optional[Dict[str, Any]] = None,
                      labels: Optional[Dict[str, Any]] = None,
                      spots: Optional[List[Dict[str, Any]]] = None,
                      hints: Optional[Dict[str, Any]] = None,
                      table_labels: Optional[List[str]] = None,
                      history: Optional[List[Dict[str, Any]]] = None) -> str:
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

    # v88 — few-shot لحن: نامه‌های واقعیِ قبلاً ذخیره‌شدهٔ همین اداره، فقط
    # به‌عنوانِ الگوی نگارش (قاعدهٔ ۱۶). محتوایشان هرگز منبعِ واقعیت نیست.
    if style_samples:
        parts.append("\n### نمونه‌نامه‌های آرشیو (فقط الگوی لحن و نگارش — قاعدهٔ ۱۶):")
        parts.append(
            "این‌ها نامه‌های رسمیِ قبلاً ذخیره‌شدهٔ همین اداره‌اند. لحن، قالبِ جمله‌ها و "
            "آغاز/استناد/درخواست/پایان‌بندی را از این‌ها الگو بگیر تا پیشنهادهایت هم‌صدا با "
            "مکاتباتِ واقعیِ این اداره باشد. فقط «سبک» را بردار: هیچ نام/عدد/تاریخ/موضوعی از "
            "نمونه‌ها به نامهٔ فعلی منتقل نشود و محتوایشان واقعیت تلقی نشود.")
        for i, smp in enumerate((style_samples or [])[:MAX_STYLE_SAMPLES], 1):
            subj = str(smp.get("subject") or "").strip()
            head = f"— نمونهٔ {i}" + (f" (موضوع: {subj})" if subj else "")
            parts.append(head + ":\n" + str(smp.get("body") or "").strip()[:MAX_STYLE_CHARS])

    if layout:
        parts.append(_layout_section(layout, labels or {}))
    if history:
        parts.append(_history_section(history))
    if spots or hints:
        parts.append(_spots_section(spots or [], hints or {}))

    parts.append("\n### حقایقِ پایگاه‌داده (منبعِ حقیقت برای اعتبارسنجی؛ کلیدهای "
                 "account_activity_log/journal_log = لاگِ کارهای همین حساب — جدیدترین اول؛ "
                 "اگر دستورِ کاربر به «لاگ‌ها/کارهای انجام‌شده» اشاره دارد از همین‌ها استخراج کن و "
                 "اگر این برشِ اخیر کافی نیست، با need_logs (قاعدهٔ ۱۵) کلِ لاگ‌ها را جستجو کن):")
    parts.append(json.dumps(facts, ensure_ascii=False, indent=1) if facts else "(بدون رکورد مرتبط)")

    parts.append("\n### ابزارهای درخواستی (فقط روی این‌ها تمرکز کن):")
    guides = [f"- {g}" for g in (_tool_guide(t) for t in tools) if g]
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
    # Attachment CONTENT (for the full_check tool): in-flow attachment tables +
    # extracted text of attached files — the material the letter must agree with.
    atts, att_tbls, _att_warns = fit_attachments(attachments_text, attachment_tables)
    if warnings_out is not None:
        warnings_out.extend(_att_warns)
    if atts or att_tbls:
        n_att = len(atts) + len(att_tbls)
        parts.append(
            "\n### محتوای پیوست‌های نامه (برای بررسیِ مغایرت با پایگاه‌داده و انطباق با متنِ نامه — "
            "این‌ها قابلِ text_replace نیستند؛ مغایرت‌شان را با note/اصلاحِ متنِ نامه گزارش کن. "
            "اما محتوایشان «منبعِ مجازِ داده» برای پر کردن/ساختنِ جدول‌هاست: اگر دستورِ کاربر "
            "پر کردنِ جدولی را می‌خواهد که داده‌اش این‌جاست، همان مقدارهای دقیق را بردار و در "
            "note بگو از کدام پیوست آمده):"
        )
        # v123 — COMPLETENESS CONTRACT. The failure the owner keeps hitting is a
        # silently PARTIAL answer (10 of 12 rows). State the exact count, forbid
        # summarising, and require an explicit note when something is missing —
        # a reported gap is recoverable, a silent one is not.
        parts.append(
            f"⚠️ تعدادِ دقیقِ منابعِ پیوستِ زیر: {n_att} مورد "
            f"({len(atts)} فایلِ پیوست + {len(att_tbls)} جدولِ پیوستِ داخلِ نامه). "
            "قاعدهٔ الزامی: اگر دستورِ کاربر به پیوست‌ها مربوط است، باید **هر "
            f"{n_att} مورد** را پردازش کنی — یکی‌یکی و کامل. هرگز خلاصه نکن، "
            "«و غیره/سایر موارد» ننویس، و هیچ موردی را جا نینداز. اگر جدولی را پر "
            "می‌کنی، به‌ازای هر منبع ردیف(های) خودش باید ساخته شود. اگر برای موردی "
            "داده‌ای پیدا نکردی، آن را حذف نکن: ردیفش را با مقدارِ خالی بیاور و در یک "
            "note بنویس کدام مورد و چرا. پیش از پایان، شمارشِ خودت را چک کن: تعدادِ "
            f"موردهای پوشش‌داده‌شده باید {n_att} باشد؛ اگر کمتر است، ادامه بده."
        )
        for i, t in enumerate(att_tbls, 1):
            parts.append(f"[جدولِ پیوست {i} — صفحهٔ پیوستِ داخلِ خودِ نامه]\n{t}")
        for i, (nm, txt) in enumerate(atts, 1):
            parts.append(f"[فایلِ پیوست {i} از {len(atts)}: {nm}]\n{txt}")
        if _att_warns:
            # The model must not present a trimmed input as a complete answer.
            parts.append(
                "توجه: بخشی از محتوای پیوست‌ها به‌خاطرِ محدودیتِ اندازه به تو نرسید — "
                + " | ".join(_att_warns)
                + " . در چنین حالتی نتیجه را «کامل» جا نزن؛ در یک note دقیقاً بگو کدام "
                "پیوست ناقص بود."
            )

    tbls = [t for t in (tables or []) if (t or "").strip()][:MAX_TABLES]
    if tbls:
        parts.append(
            "\n### جدول‌های انتخاب‌شده توسطِ کاربر (HTML فعلی — شماره‌ها برای table_index):"
            if not table_labels else
            "\n### جدول‌های فرم (HTML فعلی — شماره‌ها برای table_index در table_replace/table_delete؛ "
            "جای هر جدول کنارِ شماره‌اش آمده):"
        )
        labs = [str(x or "").strip()[:120] for x in (table_labels or [])]
        for i, t in enumerate(tbls, 1):
            where = labs[i - 1] if i - 1 < len(labs) and labs[i - 1] else ""
            parts.append(f"[جدول {i}{' — ' + where if where else ''}]\n{t[:20000]}")
        parts.append(
            "قواعدِ کار با جدول‌های انتخاب‌شده:\n"
            "- اگر «دستورِ اختصاصیِ کاربر» خواسته‌ای دربارهٔ جدول(ها) دارد، آن را کامل و همه‌جانبه "
            "اجرا کن — ساختاری و محتوایی هر دو: افزودن/حذف/ادغامِ سطر و ستون، تغییرِ چیدمان، "
            "سرستون، ترازبندی، عرضِ ستون‌ها (style)، مرتب‌سازی، تفکیک/ترکیبِ جدول‌ها — با یک "
            "op=\"table_replace\" برای هر جدولِ تغییرکرده (table_index از فهرستِ بالا؛ html کاملِ "
            "جدولِ جدید). محتوای واقعیِ داده‌ها را بدونِ دستورِ صریح تغییر نده و هیچ داده‌ای را "
            "از خودت نساز.\n"
            "- اگر دستور پر کردن/تکمیلِ محتوای جدول را می‌خواهد (مثلاً «جدول را با مشخصاتِ "
            "تسهیلات پر کن»)، منابعِ مجازِ داده فقط این‌هاست: بخشِ «حقایقِ پایگاه‌داده»، بخشِ "
            "«محتوای پیوست‌های نامه» (اگر در همین پیام هست) و خودِ دستورِ کاربر. هر قلمِ "
            "خواسته‌شده را اول در حقایق جست‌وجو کن (customer/facilities/guarantors/profile/"
            "properties/…) و بعد در محتوای پیوست‌ها؛ اگر یافت شد، همان مقدارِ دقیق را — با همان "
            "عدد/تاریخ/واحد/املا — در خانه بگذار (و اگر از پیوست آمده، در note منبعش را بگو)؛ "
            "اگر هیچ‌جا یافت نشد، خانه را «—» بگذار و در یک note جداگانه "
            "(category=tables) دقیقاً فهرست کن کدام اقلام موجود نبود تا کاربر "
            "بداند. هرگز عدد، تاریخ، نام یا مبلغی را حدس نزن و نساز؛ اگر «حقایقِ پایگاه‌داده» "
            "خالی است (نامهٔ عمومی/بدونِ حساب) و پیوستی هم نیست، این را در note بگو و جدول را "
            "با داده‌ی ساختگی پر نکن.\n"
            "- جمع/تجمیع فقط به‌درخواستِ صریحِ کاربر («جمعِ همهٔ شعب»، «مجموعِ هر سال»، «بدونِ "
            "تفکیک»): محاسبه از روی ردیف‌های همان منابعِ مجاز آزاد است، به سه شرط: (۱) محاسبه را "
            "دو بار مستقل انجام بده و فقط اگر هر دو یکی شد بنویس؛ (۲) در یک note جداگانه دقیقاً "
            "بگو چه ردیف‌هایی را از کدام منبع جمع زدی (مثلاً «جمعِ ستونِ مبلغِ ۱۲ ردیفِ شعبِ "
            "پیوستِ X برای سالِ ۲۰۲۴») تا قابلِ راستی‌آزمایی باشد؛ (۳) اگر ردیف‌های منبع ناقص/"
            "بریده به نظر می‌رسند (متنِ پیوست سقف‌خورده)، جمع نزن — در note بگو منبع کامل نیست.\n"
            "- اگر دستورِ کاربر بخش‌های غیرمرتبط با جدول هم دارد، آن‌ها را جداگانه با opهای "
            "معمول (text_replace/set_field/note) پوشش بده — هیچ بخشی از دستور بی‌پاسخ نماند.\n"
            "- اگر دستورِ اختصاصی خالی است یا ربطی به جدول ندارد، table_replace نده؛ همان "
            "رفتارِ پیش‌فرضِ ابزارِ جداول را انجام بده (ناهماهنگی‌ها به‌صورت note، اصلاحِ "
            "محتواییِ جزئی با text_replace)."
        )

    if instruction.strip():
        parts.append(
            "\n### ساختِ جدولِ جدید (وقتی دستورِ زیر جدولِ نو می‌خواهد):\n"
            "- اگر دستورِ اختصاصیِ کاربر ایجادِ جدولِ تازه‌ای را می‌خواهد (در متنِ نامه یا "
            "به‌صورتِ صفحهٔ پیوست)، لازم نیست جدولی از قبل وجود داشته یا انتخاب شده باشد — "
            "با یک op=\"table_insert\" برای هر جدولِ جدید انجامش بده: html = HTML کاملِ جدول "
            "(همان تگ‌های مجازِ table_replace)؛ table_title = عنوانِ کوتاهِ اختیاری؛ placement "
            "= \"body\" برای جدولِ کوچکِ داخلِ متن یا \"attachment\" برای صفحهٔ پیوستِ جداگانه "
            "بعد از صفحهٔ آخرِ نامه (جدولِ پهن/پرردیف، یا وقتی کاربر خودش گفته پیوست؛ صفحهٔ "
            "پیوست خودش عریض‌شدن/کوچک‌شدنِ فونت را مدیریت می‌کند).\n"
            "- دادهٔ خانه‌ها همان قواعدِ پر کردنِ جدول: فقط از «حقایقِ پایگاه‌داده»، «محتوای "
            "پیوست‌های نامه» (اگر هست) یا خودِ دستور؛ قلمِ ناموجود «—» + note؛ هیچ داده‌ای نساز.\n"
            "- ظاهر: ردیفِ اولِ سرستون با <th> یا bold، ترازبندی و عرضِ ستون‌ها با style "
            "(text-align/width)، بدونِ ستون/ردیفِ بی‌استفاده — جدول باید مرتب و درخورِ نامهٔ "
            "رسمی باشد.\n"
            "- اگر دستور جدولِ جدید نمی‌خواهد، table_insert نده."
        )
        parts.append("\n### دستورِ اختصاصیِ کاربر:")
        parts.append(instruction.strip()[:2000])

    parts.append("\nحالا فهرستِ تغییراتِ پیشنهادی را دقیقاً به‌صورتِ JSON {\"changes\":[...]} برگردان.")
    return "\n".join(parts)


def _reject(rejected: Optional[List[Dict[str, str]]], op: str, title: str, reason: str) -> None:
    """Record WHY a proposal was dropped. Silently dropping was what made the
    quick bar answer an order with «تغییری اعمال نشد» and no reason (v178)."""
    if rejected is not None:
        rejected.append({"op": op, "title": (title or op)[:200], "reason": reason[:300]})


def parse_and_validate(raw_text: str, fields: Dict[str, Any],
                       tables_count: int = 0,
                       layout: Optional[Dict[str, Any]] = None,
                       rejected: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
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

        if op == "set_layout":
            # Only when the caller supplied a layout (i.e. the page can apply it).
            if not layout or field not in LAYOUT_KEYS:
                _reject(rejected, op, title, f"کلیدِ ظاهرِ «{field}» شناخته نیست")
                continue
            props = clean_layout_props(ch.get("props"))
            if not props or len(props) > MAX_LAYOUT_TOUCH:
                _reject(rejected, op, title, "props خالی/نامعتبر است (فقط x,y,w,h,size,… با مقدارِ عددیِ مطلق)")
                continue
            cur = layout.get(field) if isinstance(layout.get(field), dict) else {}
            item["props"] = props
            item["before"] = json.dumps({k: cur.get(k) for k in props if k in cur}, ensure_ascii=False)
            item["after"] = json.dumps(props, ensure_ascii=False)
            item["title"] = item["title"] if title else f"تغییرِ ظاهرِ «{LAYOUT_KEYS[field]}»"
            item["applicable"] = True
            out.append(item)
            continue

        if op == "set_label":
            if not layout or field not in LABEL_KEYS:
                _reject(rejected, op, title, f"عنوانِ چاپیِ «{field}» شناخته نیست")
                continue
            after = ch.get("after")
            if not isinstance(after, str) or len(after) > 60:
                _reject(rejected, op, title, "after باید متنِ کوتاه (حداکثر ۶۰ نویسه) باشد")
                continue
            item["after"] = after
            item["before"] = str(ch.get("before") or "")
            item["applicable"] = True
            out.append(item)
            continue

        if op == "table_replace":
            # Full redesign of ONE user-selected table. Valid only when tables
            # were actually provided; the HTML must survive the whitelist
            # sanitizer (scripts/handlers/links/images never reach the letter).
            try:
                ti = int(ch.get("table_index"))
            except (TypeError, ValueError):
                _reject(rejected, op, title, "شمارهٔ جدول (table_index) نیامده یا عدد نیست")
                continue
            if not (1 <= ti <= tables_count):
                _reject(rejected, op, title,
                        f"جدولِ شمارهٔ {ti} وجود ندارد (فقط {tables_count} جدول فرستاده شده)")
                continue
            clean = sanitize_table_html(str(ch.get("html") or ""))
            if not clean:
                _reject(rejected, op, title, "html جدول خالی/نامعتبر است")
                continue
            item["field"] = BODY_FIELD
            item["table_index"] = ti
            item["html"] = clean
            item["before"] = f"جدول {ti} (نسخهٔ فعلی)"
            item["after"] = "نسخهٔ بازطراحی‌شده — پیش‌نمایش زیر"
            item["applicable"] = True
            out.append(item)
            continue

        if op == "table_delete":
            # Remove ONE of the tables that were sent (body or attachment page).
            # Same index contract as table_replace; the client deletes by uid.
            try:
                ti = int(ch.get("table_index"))
            except (TypeError, ValueError):
                _reject(rejected, op, title, "شمارهٔ جدول (table_index) نیامده یا عدد نیست")
                continue
            if not (1 <= ti <= tables_count):
                _reject(rejected, op, title,
                        f"جدولِ شمارهٔ {ti} وجود ندارد (فقط {tables_count} جدول فرستاده شده)")
                continue
            item["field"] = BODY_FIELD
            item["table_index"] = ti
            item["before"] = f"جدول {ti}"
            item["after"] = "حذف"
            item["title"] = item["title"] if title else f"حذفِ جدولِ {ti}"
            item["applicable"] = True
            out.append(item)
            continue

        if op == "table_insert":
            # A brand-NEW table authored by the model (needs no pre-existing or
            # selected table). Same whitelist sanitizer as table_replace — this
            # is the only path model HTML takes into the letter.
            clean = sanitize_table_html(str(ch.get("html") or ""))
            if not clean:
                _reject(rejected, op, title, "html جدول خالی/نامعتبر است")
                continue
            placement = str(ch.get("placement") or "body").strip().lower()
            if placement not in ("body", "attachment"):
                placement = "body"
            item["field"] = BODY_FIELD
            item["html"] = clean
            item["placement"] = placement
            item["table_title"] = str(ch.get("table_title") or "").strip()[:120]
            item["before"] = "—"
            item["after"] = ("جدولِ جدید — صفحهٔ پیوستِ نامه" if placement == "attachment"
                             else "جدولِ جدید — داخلِ متنِ نامه") + " — پیش‌نمایش زیر"
            item["applicable"] = True
            out.append(item)
            continue

        if op == "paragraph_merge":
            # Stitch SCATTERED pieces of one topic across paragraph boundaries:
            # every part must exist verbatim (or ws/yeh-kaf-normalized) in the
            # target field — same hallucination guard as text_replace. The
            # client replaces part 1 with `replace` and deletes the rest.
            fld = field if field in TEXT_FIELDS else BODY_FIELD
            haystack = plain.get(fld, "")
            raw_parts = ch.get("parts")
            replace = ch.get("replace")
            if not isinstance(raw_parts, list) or not isinstance(replace, str) or not replace.strip():
                _reject(rejected, op, title, "parts/replace نیامده")
                continue
            parts_txt = [str(p).strip() for p in raw_parts if isinstance(p, str) and str(p).strip()][:6]
            if len(parts_txt) < 2:
                _reject(rejected, op, title, "دست‌کم دو تکه (parts) لازم است")
                continue
            missing = [p for p in parts_txt
                       if not (p in haystack or _norm_ws(_fold_heh(p)) in _norm_ws(_fold_heh(haystack)))]
            if missing:
                _reject(rejected, op, title, f"این تکه عیناً در متن نیست: «{missing[0][:80]}»")
                continue
            item["field"] = fld
            item["parts"] = parts_txt
            item["replace"] = replace
            item["before"] = " ⤶ ".join(p[:80] for p in parts_txt)
            item["after"] = replace
            item["applicable"] = True
            out.append(item)
            continue

        if op == "set_field":
            if field not in SCALAR_FIELDS:
                # body/unknown → not settable wholesale
                _reject(rejected, op, title,
                        "set_field برای body مجاز نیست — متنِ نامه را با text_replace/paragraph_merge تغییر بده"
                        if field == BODY_FIELD else f"فیلدِ «{field}» شناخته نیست")
                continue
            after = ch.get("after")
            if after is None:
                _reject(rejected, op, title, "after نیامده")
                continue
            item["after"] = str(after)
            item["before"] = str(ch.get("before") if ch.get("before") is not None else plain.get(field, ""))
            item["applicable"] = True
            out.append(item)
            continue

        if op == "text_replace":
            if field not in TEXT_FIELDS:
                _reject(rejected, op, title,
                        f"فیلدِ «{field}» متنِ آزاد نیست — برای فیلدهای کوتاه set_field بده"
                        if field in SCALAR_FIELDS else f"فیلدِ «{field}» شناخته نیست")
                continue
            find = ch.get("find")
            replace = ch.get("replace")
            if not isinstance(find, str) or not find.strip() or replace is None:
                _reject(rejected, op, title, "find/replace نیامده")
                continue
            haystack = plain.get(field, "")
            # Hallucination guard: the exact snippet must exist (verbatim, or with
            # whitespace/ZWNJ normalized). If it isn't there, we cannot locate it
            # safely on the client → drop the change.
            located = find in haystack or _norm_ws(_fold_heh(find)) in _norm_ws(_fold_heh(haystack))
            if not located:
                _reject(rejected, op, title, f"این عبارت عیناً در «{field}» نیست: «{find.strip()[:80]}»")
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
        if op not in ("db_write", "kb_write", "link", "entity_write"):   # staged elsewhere
            _reject(rejected, op, title, f"op «{op}» شناخته نیست")
        # unknown op → skip
    return out


MAX_DB_WRITES = 40
_KEY_RE = re.compile(r"[^a-z0-9_]+")


def _norm_key(k: str) -> str:
    """Canonicalize a proposed profile key: lower snake_case, trimmed, capped."""
    k = (k or "").strip().lower().replace(" ", "_").replace("-", "_")
    k = _KEY_RE.sub("", k)
    return k[:60]


def parse_kb_writes(raw_text: str) -> List[Dict[str, Any]]:
    """Pull the model's op=="kb_write" proposals — general/educational content
    for the Knowledge Base. Raw dicts (topic/category/content/source_note),
    de-duped by (topic, content); persistence/grouping happens in kb_store."""
    data = _loose_json(raw_text)
    changes = data.get("changes") if isinstance(data, dict) else None
    if not isinstance(changes, list):
        return []
    out: List[Dict[str, Any]] = []
    seen: set = set()
    for ch in changes:
        if not isinstance(ch, dict) or str(ch.get("op") or "").strip() != "kb_write":
            continue
        topic = str(ch.get("topic") or "").strip()
        content = str(ch.get("content") or "").strip()
        if len(topic) < 2 or len(content) < 10:
            continue
        dedup = (topic.casefold(), content[:120].casefold())
        if dedup in seen:
            continue
        seen.add(dedup)
        out.append({
            "topic": topic[:300],
            "category": str(ch.get("category") or "").strip()[:120],
            "content": content[:8000],
            "source_note": str(ch.get("source_note") or "").strip()[:400],
            "title": str(ch.get("title") or "").strip() or f"پایگاه دانش: {topic[:60]}",
            "detail": str(ch.get("detail") or "").strip(),
        })
    return out[:20]


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
