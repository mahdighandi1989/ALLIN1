---
title: "تولید فایل واقعی توسط AI: spec سخت‌گیر + رندر سمت سرور + نشان منشأ علیه چرخهٔ داده"
tags: ["ai", "file-generation", "openpyxl", "python-docx", "data-provenance", "backend", "rtl"]
topic_canonical: "ai-generated-artifacts-spec-render-and-provenance-guard"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-07T00:00:00Z"
created_at: "2026-07-07T00:00:00Z"
updated_at: "2026-07-07T00:00:00Z"
merged_from: []
---

# AI-generated artifacts: strict spec → server render → provenance guard

## 🎯 چالش / Challenge

کاربر می‌خواهد AI برایش «فایل واقعی» بسازد (مثلاً جدول اکسل یا متن ورد از
داده‌های دیتابیس) و همان‌جا به‌عنوان پیوست ثبت شود. سه خطر:

1. اگر خودِ مدل فایل/باینری بسازد، خروجی غیرقابل‌اعتماد و غیرقابل‌ولیدیشن است.
2. مدل ممکن است دادهٔ گمشده را «اختراع» کند.
3. **چرخهٔ داده:** اگر همان سیستم یک ابزار «استخراج از پیوست‌ها → دیتابیس» هم
   داشته باشد، فایلِ ساختهٔ AI (که داده‌اش از خودِ DB آمده) دوباره وارد DB
   می‌شود — نویزِ تکراری با ظاهرِ «سند جدید».

## 💡 راه‌حل / Solution

1. **مدل فقط spec پیشنهاد می‌دهد، نه فایل:** خروجی مدل یک JSON با اسکیمای
   بسته (`kind`, `filename`, `title`, `warnings`, `sheets|paragraphs`).
2. **سرور مرجع است:** پارسر قطعی spec را ولیدیشن/کلمپ می‌کند (سقف شیت/سطر/
   ستون/طول سلول، sanitize نام فایل و نام شیت، None→خالی، مقادیر نامعتبر→
   پیش‌فرض امن، خروجی بی‌ساختار→reject) و خودش با کتابخانهٔ واقعی
   (openpyxl / python-docx) فایل را رندر می‌کند.
3. **قانون داده:** فقط از حقایقِ پاس‌داده‌شدهٔ DB + متنِ دستور؛ دادهٔ گمشده =
   سلول خالی + یک `warning` که در UI نمایش داده می‌شود — هرگز اختراع نشود.
4. **نشان منشأ (provenance):** فایل ذخیره‌شده با مارکر ثابت در metadata
   (مثلاً `notes` با پیشوند `AI_GENERATED:`) و لیستینگ API یک فلگ بولی
   (`ai_generated`) بدهد.
5. **گارد چرخه در مصرف‌کننده:** هر ابزار ingestion/استخراج، آیتم‌های
   `ai_generated` را **پیش‌فرض بی‌تیک** کند (انتخاب صریح کاربر همچنان مجاز)
   و دلیلش را همان‌جا در UI توضیح دهد.

## 🧪 نمونه کد (Anonymized)

```python
# server-side gate: model text → validated spec → real file
spec, warnings = parse_spec(model_text)      # clamps + sanitizes, raises on garbage
data, filename, mimetype = render(spec)      # openpyxl / python-docx
store(data, filename, notes=f"AI_GENERATED: {instruction[:400]}")
```

```ts
// consumer default-exclusion with explicit opt-in (tri-state via ??)
const selected = (a: Attachment) => picks[a.id] ?? !a.ai_generated
// "select all" must set every id EXPLICITLY true, otherwise {} re-excludes them
```

## ⚠️ نکات حیاتی / Pitfalls

- **`?? !flag` نه `!== false`:** اگر انتخاب پیش‌فرض با `map[id] !== false`
  پیاده شده باشد، «پیش‌فرضِ متفاوت برای گروهی از آیتم‌ها» ممکن نیست؛ به
  `map[id] ?? defaultFor(item)` مهاجرت کن و دکمهٔ «انتخاب همه» را صریح کن
  (`{}` دیگر به‌معنی «همه» نیست).
- **رندر RTL در docx:** جهتِ راست‌به‌چپ فقط در سطح پاراگراف (`w:bidi`)؛
  پرچم `rtl` روی runها یک override است و متن لاتین/عدد را آینه می‌کند.
- **sanitize نام فایل و نام شیت جدا هستند:** اکسل روی `[]:*?/\` در نام شیت
  خطا می‌دهد حتی اگر نام فایل تمیز باشد.
- **warnings را گم نکن:** تنها راهِ فهمیدن «چه چیزی در DB نبود» همین است؛
  در پاسخ endpoint و در UI پاس بده.
- مارکر منشأ را **پیشوندِ** فیلد متنی موجود کن (`startswith`)، نه substring —
  متن آزادِ کاربر می‌تواند اتفاقی شامل کلمه شود.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- [ ] هر جا AI «فایل/آرتیفکت» تولید می‌کند: مدل spec بدهد، سرور رندر کند.
- [ ] اسکیمای spec را ببند و برای هر فیلد سقف/پیش‌فرض امن تعریف کن.
- [ ] قانونِ «دادهٔ گمشده = خالی + warning» را در system prompt و در پارسر
  هر دو enforce کن.
- [ ] خروجی را با همان مسیر ذخیره‌سازیِ آرتیفکت‌های دستی ثبت کن (نه مسیر موازی).
- [ ] فلگ منشأ را در storage و در API لیستینگ اضافه کن.
- [ ] تمام مصرف‌کننده‌های ingestion را پیدا کن و default-exclusion بگذار؛
  تست بنویس که «آیتم ساختهٔ AI پیش‌فرض بی‌تیک است ولی تیک دستی کار می‌کند».

## 🔗 References

- مرتبط: [ai-edit-suggestions-review-first-with-locate-guard]
- مرتبط: [ai-extract-to-db-attribute-dedup-log]
