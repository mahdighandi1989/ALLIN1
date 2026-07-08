---
title: "طبقه‌بندی اطمینانِ de-dup باید همه‌ی ستون‌های داده را مقایسه کند، نه فهرست دستچین"
tags: ["data-integrity", "dedup", "backend", "review-first"]
topic_canonical: "conservative-dedup-compare-all-columns"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-02T00:00:00Z"
created_at: "2026-07-02T00:00:00Z"
updated_at: "2026-07-02T00:00:00Z"
merged_from: []
---

# Conservative de-dup: compare ALL data columns for confidence

## 🎯 چالش / Challenge
موتور پاکسازی duplicate دولایه بود: لایه‌ی ۱ کاندیدها را با شناسه‌ی قوی
(شماره چک/سند/سپرده) پیدا می‌کرد؛ لایه‌ی ۲ اطمینان را طبقه‌بندی می‌کرد
(«certain» → حذف خودکار، «probable» → بازبینی انسانی/AI). ولی لایه‌ی ۲ فقط
۳–۵ فیلدِ «کلیدیِ» دستچین‌شده را مقایسه می‌کرد. دو رکورد با شماره چک یکسان
(reuse یا خطای تایپ) ولی **نام ضامنِ متفاوت** — چون «نام» در آن فهرست نبود —
«certain» می‌شدند و یک ضامن واقعی خودکار حذف می‌شد. یک helper کامل مقایسه‌ی
همه‌ی ستون‌ها هم در کد بود ولی **هرگز صدا زده نمی‌شد** (dead code = نشانه‌ی نیت
پیاده‌نشده).

## 💡 راه‌حل / Solution
- «certain» فقط وقتی که **هیچ ستون داده‌ایِ پُرشده‌ای اختلاف نداشته باشد**
  (تفاوت خالی↔پُر اشکالی ندارد؛ پُر↔پُرِ متفاوت یعنی review).
- ستون‌های متادیتا (created_by, created_at, import batch, …) را از مقایسه خارج
  کن — وگرنه هر re-import همه‌چیز را probable می‌کند و ارزش auto-clean می‌میرد.
- همان قانون را در **گاردهای زمان ورود** (entry-time dedup/merge) هم اعمال کن،
  نه فقط در اسکن دوره‌ای — دو مسیر نباید دو تعریف «same record» داشته باشند.
- تست regression بنویس: جفت با شناسه‌ی قوی یکسان + یک فیلد هویتی متفاوت باید
  «probable» شود، هرگز «certain».

## 🧪 نمونه کد (Anonymized)
```python
META_COLS = {"id", "created_at", "created_by", "import_batch"}
def data_cols(model):
    return [c.name for c in model.__table__.columns if c.name not in META_COLS]

def confidence(keeper, candidate, model):
    conflicts = [c for c in data_cols(model)
                 if filled(getattr(keeper, c)) and filled(getattr(candidate, c))
                 and differs(getattr(keeper, c), getattr(candidate, c))]
    return "probable" if conflicts else "certain"
```

## ⚠️ نکات حیاتی / Pitfalls
- فهرست دستچینِ «فیلدهای مهم» با اضافه‌شدن هر ستون جدید به مدل، بی‌صدا ناقص‌تر
  می‌شود؛ مشتق‌کردن از متادیتای مدل این drift را حذف می‌کند.
- helper مرده‌ای که «کامل‌تر» از مسیر زنده است تقریباً همیشه یعنی refactor
  ناتمام — پیدا کردنش سرنخ طلایی audit است.
- مقایسه‌ی numeric-aware لازم است ("100" == "100.0") وگرنه false-probable زیاد
  می‌شود.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere
هرجا حذف/ادغام خودکارِ مبتنی بر اطمینان داری (CRM merge، cleanup، import guard):
1. سیاست را بنویس («در شک، حذف نکن») و تستش کن.
2. اطمینان را از همه‌ی ستون‌های داده مشتق کن؛ متادیتا را صریح exclude کن.
3. auto-action فقط برای بالاترین سطح اطمینان؛ بقیه صف بازبینی.

## 🔗 References
- منبع اولیه: ALLIN1 deep-audit 2026-07-02 — `services/db_cleanup.py`
- مرتبط: [form-state-reset-on-entity-switch]

## Update 2026-07-08 — کلیدِ هویتِ رکورد باید فرمت‌های ورودی را نرمال کند (نه مقایسهٔ خام)

دوپلیکیتِ ضامن که هیچ dedupـی نگرفت: **یک** نفر دو بار ثبت شده بود چون
`account = "131757"` در برابر `"2624-131757-006"` و نام `"MOHD"` در برابر
`"MOHAMED ... AL MAAZMI"`. علت‌ها: (۱) کلیدِ dedup روی **نامِ دقیق** بود؛ (۲)
شمارهٔ حساب فیلدِ متنیِ آزاد بود که در ایمپورت‌های چندساله با فرمت‌های مختلف
ذخیره شده — «core» یا «branch-core-suffix». درس:

- **کلیدِ هویت را نرمال کن، خام مقایسه نکن:** برای شمارهٔ حساب، «coreِ پایدار»
  را استخراج کن (تنها گروهِ ۶رقمی؛ اگر مبهم بود، به مقایسهٔ سخت برگرد). برای نام،
  توکن‌بندی + حذفِ honorific/fil(`MR/AL/BIN…`) + تشابهِ توکنی (subset یا ≥۲ توکنِ
  مشترک) — نه برابریِ رشته.
- **محافظه‌کار بمان و forward-only:** pass نرمال‌شده را فقط **بعد** از شکستِ
  مطابقتِ دقیق اضافه کن، با آستانهٔ سخت‌گیرانه تا افرادِ واقعاً متفاوت ادغام
  نشوند. رکوردهای موجودِ production را **خودکار ادغام نکن** (review-first)؛ فقط
  جلوی دوپلیکیتِ آینده را بگیر.
- **dedup به‌ازای هر جدول جداست:** ابزارِ پاکسازیِ «مشتری» ضامن/وثیقه را پوشش
  نمی‌دهد؛ نبودِ پوششِ یک جدول = «نگرفتنِ» گزارش‌شده. هر جدولِ آزادِ متنی کلیدِ
  هویتِ خودش را می‌خواهد.

## 🔗 References (added)
- مرتبط: [upsert-keys-must-cover-every-caller]
