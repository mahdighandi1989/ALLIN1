---
title: "فرم‌های load-by-id باید هنگام تعویض موجودیت به state تمیز reset شوند"
tags: ["react", "frontend", "forms", "data-integrity"]
topic_canonical: "form-state-reset-on-entity-switch"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-02T00:00:00Z"
created_at: "2026-07-02T00:00:00Z"
updated_at: "2026-07-02T00:00:00Z"
merged_from: []
---

# Form state must reset when the loaded entity changes

## 🎯 چالش / Challenge
چند فرم «شماره/شناسه را وارد کن → بارگیری → ویرایش → ذخیره» داشتیم. الگوی پر
کردن فرم این بود:

```ts
setForm((s) => ({ ...s, field: saved.field || fetched.field || s.field }))
if (Array.isArray(saved.rows)) setRows(saved.rows)   // فقط وقتی داده هست!
setRows((rows) => rows.map(...bind to new data...))   // مپ روی ردیف‌های قبلی!
```

سه مکانیزم جدا ولی هم‌ریشه: (۱) fallback به `s.X` یعنی مقدار موجودیت قبلی، (۲)
جایگزینی «مشروط» آرایه‌ها یعنی وقتی موجودیت جدید داده ندارد آرایه‌ی قبلی می‌ماند،
(۳) مپ روی state قبلی یعنی IDهای بایندشده به موجودیت قبلی زنده می‌مانند. نتیجه در
یک سیستم بانکی: بارگیری مشتری B بعد از A و زدن «ذخیره» ⇒ وثایق/ضامن‌های A روی
پروفایل B نوشته شد و حتی رکوردهای A آپدیت شدند — خرابی داده‌ی cross-entity کاملاً
بی‌صدا.

## 💡 راه‌حل / Solution
قانون: **در ابتدای هر load، همه‌ی stateهای فرم از ثابتِ INITIAL/base ساخته شوند**؛
هیچ setter ای نباید به state قبلی مپ شود یا fallback کند:

```ts
const s = { ...INITIAL }
setForm(() => ({ ...s, field: saved.field || fetched.field || s.field }))
setRows(Array.isArray(saved.rows) ? saved.rows : baseRows())  // بدون شرطِ نگه‌داشتن
setBoundRows(() => bindToFetched(baseRows(), fetched))        // نه مپ روی قبلی
```

`|| s.X` فقط وقتی مجاز است که `s` از INITIAL آمده باشد (یعنی «پیش‌فرض فرم»، نه
«مقدار موجودیت قبلی»).

## ⚠️ نکات حیاتی / Pitfalls
- خطر فقط «نمایش غلط» نیست؛ اگر فرم دکمه‌ی ذخیره دارد، carryover یعنی **نوشتن
  داده‌ی یک موجودیت روی دیگری**.
- جایگزینی مشروط (`if (data.length) setRows(data)`) رایج‌ترین شکل باگ است چون در
  تستِ «موجودیت دارای داده» درست کار می‌کند و فقط برای موجودیتِ خالی خراب می‌شود.
- ردیف‌هایی که id دیتابیس حمل می‌کنند (facilityId, dbId) خطرناک‌ترند — ذخیره،
  آپدیتِ موجودیتِ قبلی را صدا می‌زند.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere
چک‌لیست review برای هر فرم load-by-id:
1. آیا هر state فرم در مسیر load از یک ثابت base ساخته می‌شود؟
2. آیا هیچ `setX((prev) => ...)` ای در مسیر load به prev وابسته نیست؟
3. آیا fallbackهای `||` به پیش‌فرض اشاره می‌کنند نه به state جاری؟
4. تست دستی: موجودیت پُر → موجودیت خالی → ذخیره؛ سپس دیتای موجودیت اول را چک کن.

## 🔗 References
- منبع اولیه: ALLIN1 deep-audit 2026-07-02 — فرم‌های credit-file/sanction/offer-letter
