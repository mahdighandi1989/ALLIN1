---
title: "SQLite در تست‌ها باگ‌های عرض ستون و precision عددی را پنهان می‌کند"
tags: ["testing", "sqlalchemy", "postgres", "sqlite", "schema"]
topic_canonical: "sqlite-tests-hide-column-width-bugs"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-02T00:00:00Z"
created_at: "2026-07-02T00:00:00Z"
updated_at: "2026-07-02T00:00:00Z"
merged_from: []
---

# SQLite tests hide column-width bugs

## 🎯 چالش / Challenge
CI کاملاً سبز بود ولی در production (Postgres) یک فیچر کامل مرده بود: یک ستون
FK با `String(8)` تعریف شده بود در حالی که مقادیر واقعی ۹+ کاراکتر بودند — هر
INSERT واقعی با `value too long` می‌مرد. همچنین `Numeric(5,4)` برای فیلد درصدی
که API تا 100 می‌پذیرفت ⇒ هر مقدار ≥ 10 در Postgres با `numeric field overflow`
می‌ترکید. هیچ تستی نمی‌گرفت چون suite روی SQLite اجرا می‌شد و **SQLite نه طول
VARCHAR را enforce می‌کند نه precision عددی را**. داده‌ی seed هم زیر آستانه بود
(نرخ‌های < 10)، پس دستی هم دیده نمی‌شد.

## 💡 راه‌حل / Solution
1. عرض/precision را روی **متادیتای مدل** assert کن — این تست روی هر DBای پاس/فیل
   یکسان دارد:
   - `fk.type.length >= pk.type.length` برای هر جفت FK↔PK.
   - `precision - scale >= digits(max_allowed_by_schema)` برای هر فیلد عددی که
     schema ورودی حدش را تعیین می‌کند.
2. اگر startup «self-heal» اسکیما دارید، فقط String را widen نکنید — precision
   عددی را هم (فقط هم‌scale و رو به بالا: `numeric(5,4) → numeric(7,4)` lossless
   است؛ تغییر scale ممنوع چون داده را گرد می‌کند).
3. برای regressionهای واقعی Postgres یک job جدا با `TEST_POSTGRES_URL` نگه دارید.

## 🧪 نمونه کد (Anonymized)
```python
def test_fk_width_matches_parent_pk():
    fk = Child.__table__.c.parent_id.type.length
    pk = Parent.__table__.c.id.type.length
    assert fk >= pk

def test_percent_columns_can_store_100():
    t = Model.__table__.c.rate.type
    assert t.precision - t.scale >= 3  # 100.0 needs 3 integer digits
```

## ⚠️ نکات حیاتی / Pitfalls
- تست API روی SQLite برای این کلاس باگ **false confidence** می‌دهد؛ pass شدنش
  هیچ‌چیز درباره‌ی Postgres نمی‌گوید.
- Truncated-UUID PK (مثل `uuid4()[:8]`) همان خانواده است: روی حجم کم جواب می‌دهد
  و در production تصادفی collide می‌کند — عرض ستون را کامل بگیر و uuid کامل بریز.
- `create_all` هرگز ستون موجود را ALTER نمی‌کند؛ تغییر مدل بدون مهاجرت/heal یعنی
  DBهای قدیمی برای همیشه عرض قدیمی را دارند.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere
- برای هر مدل ORM یک تست متادیتا بنویس: همه‌ی FKها هم‌عرض PK والد؛ همه‌ی فیلدهای
  bounded (درصد، نرخ، مبلغ) سازگار با حد schema/API.
- در review هر مدل جدید بپرس: «بزرگ‌ترین مقدار قانونی چیست و آیا ستون جا دارد؟»
- اگر self-heal دارید، مطمئن شوید هر دو خانواده (String و Numeric) را پوشش می‌دهد.

## 🔗 References
- منبع اولیه: ALLIN1 deep-audit 2026-07-02 (docs/AUDIT_LOG.md همان تاریخ)
