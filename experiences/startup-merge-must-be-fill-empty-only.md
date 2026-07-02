---
title: "مرجِ داده‌ی startup باید fill-empty-only باشد وگرنه هر دیپلوی ویرایش‌های اپراتور را برمی‌گرداند"
tags: ["data-integrity", "startup", "merge", "backend"]
topic_canonical: "startup-merge-must-be-fill-empty-only"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-02T00:00:00Z"
created_at: "2026-07-02T00:00:00Z"
updated_at: "2026-07-02T00:00:00Z"
merged_from: []
---

# Startup data-merge must be fill-empty-only

## 🎯 چالش / Challenge
یک مرحله‌ی «ادغام داده‌ی legacy» در هر startup اجرا می‌شد (و از یک endpoint دستی
هم قابل‌اجرا بود). قرارداد مستندشده‌اش «فقط ستون‌های خالی را پر کن» بود، ولی برای
یک entity خاص بی‌قید می‌نوشت: `row.field = workbook_value` و حتی
`row.is_deleted = False`. نتیجه: اپراتور رکوردی را حذف یا مبلغی را اصلاح می‌کرد و
**در دیپلوی/ری‌استارت بعدی** رکورد زنده می‌شد و مقدار قدیمی برمی‌گشت — بدون هیچ
audit log و بدون اینکه کسی بفهمد چرا.

## 💡 راه‌حل / Solution
- هر write در مسیر merge باید گارد «فقط اگر خالی» داشته باشد؛ enum پیش‌فرض
  (مثل OTHER) هم «خالی» حساب می‌شود.
- رکورد soft-delete شده **کاملاً skip** شود — حذفِ اپراتور یک تصمیم است، نه یک
  خلأ داده.
- تست‌های regression: (۱) رکورد حذف‌شده حذف می‌مانَد، (۲) فیلد ویرایش‌شده دست
  نمی‌خورد، (۳) placeholder واقعی هنوز پر می‌شود، (۴) رکورد جدید ساخته می‌شود.

## 🧪 نمونه کد (Anonymized)
```python
if row.is_deleted:
    continue                      # operator decision wins, forever
if source.name and not row.name:
    row.name = source.name        # fill-empty only
if source.amount is not None and not row.amount:
    row.amount = source.amount
```

## ⚠️ نکات حیاتی / Pitfalls
- «idempotent» بودن merge کافی نیست — باید **non-destructive نسبت به ویرایش‌های
  بعدی انسان** هم باشد؛ این دو خاصیت جدا هستند.
- خطرناک‌ترین حالت وقتی است که merge در startup است: قربانی نمی‌تواند عمل خرابکار
  را به هیچ کار خودش ربط بدهد (فقط «بعد از دیپلوی خراب شد»).
- اگر واقعاً یک فیلد باید همیشه از منبع بازنویسی شود، آن را صریح، جدا و logged
  کن — نه قاطیِ مسیر fill.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere
برای هر sync/merge تکرارشونده (seed، ETL، reconcile):
1. جدول تصمیم بنویس: به‌ازای (فیلد موجود پُر/خالی/حذف‌شده × مقدار منبع) چه می‌شود؟
2. پیش‌فرض همیشه «دست نزن» باشد؛ بازنویسی نیازمند توجیه صریح.
3. تست «ویرایش اپراتور زنده می‌ماند» را جزو characterization tests کن.

## 🔗 References
- منبع اولیه: ALLIN1 deep-audit 2026-07-02 — `services/data_merge.py`
- مرتبط: [conservative-dedup-compare-all-columns]
