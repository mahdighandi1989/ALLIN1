---
title: "Upsert endpoints must have a match key for EVERY caller path"
tags: ["backend", "api-design", "data-integrity", "upsert"]
topic_canonical: "upsert-keys-must-cover-every-caller"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-03T05:30:00Z"
created_at: "2026-07-03T05:30:00Z"
updated_at: "2026-07-03T05:30:00Z"
merged_from: []
---

# Upsert endpoints must have a match key for every caller path

## 🎯 چالش / Challenge

یک endpoint «idempotent upsert» رکوردها را با یک کلید طبیعی (مثلاً شماره‌ی چک)
مطابقت می‌داد. بعداً فرم دیگری به همان endpoint وصل شد که آن کلید را ندارد
(رکوردِ بدون چک). نتیجه: هر بار «ذخیره»، یک رکورد تکراری جدید — و چون ذخیره‌ی
خودکار/مکرر بود، داده به‌سرعت کثیف می‌شد. مستند endpoint هم قول upsert می‌داد،
پس هیچ‌کس مشکل را در سمت فرم جست‌وجو نمی‌کرد.

## 💡 راه‌حل / Solution

1. برای **هر مسیر ورودی** یک زنجیره‌ی مطابقت تعریف کن، از دقیق‌ترین به عمومی‌ترین:
   `explicit id` → `natural key` (وقتی caller آن را دارد) → `fallback key`
   (مثلاً نام نرمال‌شده + شناسه‌ی ثانویه وقتی هر دو طرف دارند).
2. fallback را **محافظه‌کار** نگه دار: مطابقت فقط با برابری نرمال‌شده
   (whitespace/case)، نه fuzzy — تا دو موجودیت متمایز هرگز merge نشوند.
3. قانون «فیلد خالی، مقدار قبلی را نگه می‌دارد» را واقعاً اجرا کن: assignment
  بی‌شرطِ `x = payload.x or ""` مقدار ذخیره‌شده را با ورودیِ خالی پاک می‌کند.

## 🧪 نمونه کد (Anonymized)

```python
match = None
if payload.id:
    match = get_by_id(payload.id)
if match is None and payload.natural_key:
    match = get_by_natural_key(scope, payload.natural_key)
if match is None and not payload.natural_key:      # the NEW caller path
    match = get_by_normalized_name(scope, payload.name, payload.secondary_id)
created = match is None
...
if payload.natural_key:            # blank keeps the stored value
    match.natural_key = payload.natural_key
```

## ⚠️ نکات حیاتی / Pitfalls

- تست upsert فقط با مسیر «کلید دارد» نوشته می‌شود و مسیر بی‌کلید سال‌ها تست ندارد.
- fuzzy-match در fallback خطرناک است: دو شخص متفاوت با نام مشابه merge می‌شوند.
- پاک‌شدن field با ورودی خالی معمولاً در همان PR دیده نمی‌شود چون UI مقدار را می‌فرستد؛
  فقط caller جدیدِ minimal آن را فعال می‌کند.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- هر بار فرم/سرویس جدیدی را به endpoint موجودِ upsert وصل می‌کنی، بپرس:
  «این caller کدام کلید مطابقت را دارد؟» اگر هیچ‌کدام → قبل از اتصال، fallback بساز.
- برای هر upsert یک تست «دوبار ذخیره‌ی همان چیز = یک رکورد» به‌ازای **هر** caller بنویس.
- در review، دنبال assignmentهای بی‌شرط روی فیلدهای اختیاری بگرد.

## 🔗 References

- ALLIN1: guarantor upsert (cheque-less path از فرم Offer Letter) — AUDIT_LOG 2026-07-03
