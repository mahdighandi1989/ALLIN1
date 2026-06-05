---
task_id: task_bd83a960a6ab
title: افزایش پایداری و اعتبارسنجی پایپلاین اکسل
type: other
priority: high
execution_priority: 2400
status: abandoned
external_status: abandoned
verification_status: partial
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:07:38.706114+00:00'
updated_at: '2026-06-05T00:41:15.381288+00:00'
archived: true
archived_at: '2026-06-05T00:41:15.381263+00:00'
tags:
- consolidated
- post_verify_merge
---

# افزایش پایداری و اعتبارسنجی پایپلاین اکسل

## Raw Idea

🧬 این یک تسک تلفیقی است — از 4 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی بهبود پایداری و قابلیت اطمینان پایپلاین پردازش داده‌ها، به ویژه برای فایل‌های اکسل، تمرکز دارند. شامل مدیریت خطاهای فایل‌های خراب/خالی، تعریف و اعتبارسنجی schema برای فایل‌های اکسل، مشخص کردن خروجی کامپوننت‌ها و افزودن پشتیبانی از فرمت‌های مختلف اکسل است.
🎯 theme: پایپلاین پردازش فایل‌های اکسل
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 4
  id: 93988a1c-6d13-40f8-b5a9-8c49c377c7c6
  عنوان اصلی: پیاده‌سازی مدیریت خطای فایل‌های خراب یا خالی
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["corrupt", "empty", "invalid format", "error handling", "try.*except", "raise"], "files_hint": ["backend/app/data_pipeline.py", "backend/app/data_processor.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "decision", "rationale"], "files_hint": ["docs/decisions/"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_data_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["why", "decision", "rationale", "reason"], "files_hint": ["PR description"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم مدیریت خطا برای فایل‌های خراب یا خالی

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

هیچ اشاره‌ای به handling حالت‌های خطا مانند فایل خراب (corrupt)، خالی (empty)، یا فرمت نادرست نشده است. اگر فایل‌های Excel باز نشوند یا داده‌ای نداشته باشند، pipeline ممکن است crash کند یا نتایج نادرست بدهد.

## 💥 پیامد (impact)
در صورت وجود فایل خراب یا خالی، pipeline متوقف می‌شود (یا داده‌های ناقص تولید می‌کند) و نیاز به مداخله دستی دارد. این باعث کاهش reliability و افزایش زمان debug می‌شود.

## 🛠 پیشنهاد رفع اولیه
یک مرحله بررسی اولیه اضافه کنید: بررسی وجود فایل، فرمت معتبر، و وجود حداقل یک شیت با داده. در صورت خطا، یک log مناسب ثبت کرده و pipeline را با خطای مشخص متوقف کنید یا از یک fallback استفاده کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا — بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا
  - اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده — اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده
  - اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel — اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel
  - اضافه کردن لاگینگ مناسب برای خطاهای مربوط به فایل در pipeline داده — اضافه کردن لاگینگ مناسب برای خطاهای فایل در pipeline داده
  - توقف pipeline با خطای مشخص در صورت بروز خطای فایل (بدون fallback) — توقف pipeline با خطای مشخص در صورت بروز خطای فایل
  - نوشتن تست‌های واحد (unit tests) برای توابع اعتبارسنجی فایل — نوشتن unit tests برای توابع اعتبارسنجی فایل
  - نوشتن تست‌های یکپارچه‌سازی (integration tests) برای pipeline داده با فایل‌های خراب/خالی — نوشتن integration tests برای pipeline داده با فایل‌های خراب/خالی
  - بررسی نهایی و مستندسازی تغییرات در مستندات پروژه — بررسی نهایی و مستندسازی تغییرات در مستندات پروژه

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 4
  id: fc686bb9-3172-4810-9b26-624303be2a32
  عنوان اصلی: تعریف و اعتبارسنجی schema فایل‌های Excel در pipeline
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["binary archive file", "schema", "Excel", "sheet", "column"], "files_hint": ["backend/app/pipeline/data.py", "backend/app/pipeline/schemas.py", "backend/app/pipeline/config.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "schema", "Excel", "binary"], "files_hint": ["backend/app/pipeline/data.py", "backend/app/pipeline/schemas.py"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_pipeline_data.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md", "docs/decisions/"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم وجود schema مشخص برای فایل‌های باینری

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

فایل‌های Excel به عنوان 'binary archive file' معرفی شده‌اند، اما هیچ schema یا ساختار داده‌ای برای محتوای داخلی آن‌ها (مثل نام شیت‌ها، ستون‌ها، نوع داده‌ها) تعریف نشده است. این باعث می‌شود که pipeline نتواند سازگاری داده‌ها را در مراحل بعدی بررسی کند.

## 💥 پیامد (impact)
در صورت تغییر ساختار فایل‌های Excel (مثلاً تغییر نام ستون‌ها یا حذف شیت‌ها)، pipeline بدون خطا اجرا می‌شود اما داده‌های نادرست یا ناقص تولید می‌کند. همچنین امکان validation خودکار وجود ندارد.

## 🛠 پیشنهاد رفع اولیه
یک schema مشخص برای هر فایل Excel تعریف کنید: نام شیت‌ها، نام ستون‌ها، نوع داده‌ها (مثلاً string, number, date) و محدوده مجاز مقادیر. سپس در pipeline یک مرحله validation برای تطبیق داده‌های ورودی با schema اضافه کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و شناسایی فایل‌های Excel موجود در pipeline data — شناسایی و مستندسازی فایل‌های Excel موجود در pipeline data
  - تعریف schema برای هر فایل Excel شامل نام شیت‌ها و ستون‌ها — تعریف schema برای هر فایل Excel شامل شیت‌ها و ستون‌ها
  - اضافه کردن مرحله validation در pipeline برای تطبیق داده‌های ورودی با schema — اضافه کردن مرحله validation در pipeline برای تطبیق با schema
  - نوشتن تست‌های unit برای validation schema — نوشتن تست‌های unit برای validation schema
  - نوشتن تست‌های integration برای pipeline با validation — نوشتن تست‌های integration برای pipeline با validation
  - مستندسازی schema و validation در مستندات پروژه — مستندسازی schema و validation در مستندات پروژه

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 4
  id: e0513e78-010b-4e28-bc31-4cc597182f0b
  عنوان اصلی: مشخص کردن خروجی کامپوننت‌های pipeline data
  اولویت اصلی: medium
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["Preserved original Excel file", "downstream", "استخراج", "CSV", "database"], "files_hint": ["backend/pipeline/data.py", "backend/pipeline/README.md", "backend/pipeline/data/*.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "output format", "target schema"], "files_hint": ["backend/pipeline/data.py", "backend/pipeline/config.py", "backend/pipeline/data/*.py"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_pipeline_data.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["چرا این تصمیم گرفته شد", "rationale", "decision", "reason"], "files_hint": ["PR description"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم تعریف خروجی مشخص برای مراحل بعدی

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

خروجی این کامپوننت‌ها فقط 'Preserved original Excel file' تعریف شده است، اما مشخص نیست که pipeline چگونه از این فایل‌ها استفاده می‌کند. آیا باید داده‌ها استخراج شوند؟ به چه فرمتی؟ آیا باید به دیتابیس یا فایل CSV تبدیل شوند؟

## 💥 پیامد (impact)
این ابهام باعث می‌شود که اتصال بین این کامپوننت‌ها و مراحل downstream نامشخص باشد. توسعه‌دهندگان ممکن است فرضیات متفاوتی داشته باشند و pipeline ناقص یا ناسازگار شود.

## 🛠 پیشنهاد رفع اولیه
خروجی مورد انتظار را به صورت دقیق تعریف کنید: مثلاً 'Extracted data as pandas DataFrame with columns: [col1, col2, ...]' یا 'Converted to CSV file at path: ...'. همچنین مشخص کنید که آیا فایل اصلی باید unchanged بماند یا تغییر کند.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - شناسایی و مستندسازی pipeline data و کامپوننت‌های آن — مستندسازی کامل فرض‌های هر دو طرف ناسازگاری
  - تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline data — تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline
  - اصلاح کامپوننت‌های pipeline data برای تولید خروجی مشخص — اصلاح کامپوننت‌ها برای تولید خروجی مشخص
  - به‌روزرسانی کامپوننت‌های downstream برای استفاده از خروجی جدید — به‌روزرسانی کامپوننت‌های downstream برای خروجی جدید
  - نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده pipeline data — نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده
  - نوشتن تست‌های integration برای pipeline data — نوشتن تست‌های integration برای pipeline data
  - به‌روزرسانی مستندات pipeline data با تغییرات اعمال‌شده — به‌روزرسانی مستندات pipeline data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 4 از 4
  id: 45d3c335-4be5-47cd-8394-997476ca53ef
  عنوان اصلی: پشتیبانی از فرمت‌های .xlsm و .xls در پایپلاین
  اولویت اصلی: low
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["xlsm", "xls", "original-excel-files"], "files_hint": ["backend/app/data_pipeline.py", "backend/app/handlers/excel_handler.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground.truth", "align", "xlsm.*xls"], "files_hint": ["backend/app/data_pipeline.py", "backend/app/handlers/excel_handler.py"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_data_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم تفکیک بین فایل‌های .xlsm و .xls

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

دو فایل با فرمت‌های مختلف (.xlsm و .xls) در یک دسته 'original-excel-files' قرار دارند، اما هیچ تمایزی در handling آن‌ها وجود ندارد. فایل .xlsm حاوی macro است و نیاز به رویکرد متفاوتی برای خواندن دارد (مثلاً اجرای macro یا صرفاً خواندن داده).

## 💥 پیامد (impact)
اگر pipeline هر دو فایل را با یک روش (مثلاً pandas.read_excel) بخواند، ممکن است macroهای فایل .xlsm اجرا نشوند یا داده‌های حاصل از macro از دست بروند. همچنین فایل .xls قدیمی‌تر است و ممکن است با کتابخانه‌های جدید compatibility مشکل داشته باشد.

## 🛠 پیشنهاد رفع اولیه
برای هر فرمت یک handler جداگانه تعریف کنید: برای .xlsm از openpyxl (با گزینه read_only یا data_only) و برای .xls از xlrd استفاده کنید. اگر macroها ضروری هستند، یک مرحله جداگانه برای اجرای macroها (با win32com یا xlwings) اضافه کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: low
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی و شناسایی فایل‌های موجود در pipeline data و نحوه handling فعلی

🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن کتابخانه‌های openpyxl و xlrd به وابستگی‌های پروژه — اضافه کردن openpyxl و xlrd به requirements.txt
  - ایجاد یک تابع handler مجزا برای فایل‌های .xlsm با استفاده از openpyxl — ایجاد تابع read_xlsm_file با openpyxl
  - ایجاد یک تابع handler مجزا برای فایل‌های .xls با استفاده از xlrd — ایجاد تابع read_xls_file با xlrd
  - اصلاح pipeline اصلی برای تشخیص خودکار فرمت فایل و استفاده از handler مناسب — تشخیص خودکار فرمت فایل و انتخاب handler مناسب
  - اضافه کردن قابلیت اجرای macro برای فایل‌های .xlsm (اختیاری، در صورت نیاز) — اضافه کردن قابلیت اجرای macro برای .xlsm
  - یکپارچه‌سازی قابلیت اجرای macro در pipeline (در صورت نیاز) — یکپارچه‌سازی اجرای macro در pipeline
  - نوشتن تست‌های واحد (unit tests) برای handlerهای جدید — نوشتن unit tests برای handlerهای جدید
  - نوشتن تست‌های یکپارچه‌سازی (integration tests) برای کل فرآیند خواندن فایل‌های Excel — نوشتن integration tests برای کل فرآیند خواندن Excel
  - بازبینی نهایی (audit) و مستندسازی تغییرات — بازبینی نهایی و مستندسازی تغییرات

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 93988a1c-6d13-40f8-b5a9-8c49c377c7c6, fc686bb9-3172-4810-9b26-624303be2a32, e0513e78-010b-4e28-bc31-4cc597182f0b, 45d3c335-4be5-47cd-8394-997476ca53ef`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Prompt

## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

📖 **خواندن کامل + اجرای مو-به-مو (بسیار مهم):**

این پرامپت — از این یادداشت تا انتها — یک سند واحد است که هر بخشش
حاوی الزام یا context منحصربه‌فرد است. خواندن سطحی یا skim کردن **ممنوع**
است.

- پرامپت را **سطر به سطر** بخوان، نه head/tail/فقط-بخش-اصلی.
- اگر بخشی به‌نظر طولانی یا تکراری آمد، **حتماً** بخوان — تفاوت‌های
  ریز ممکن است در آن جا اساسی باشند.
- هر جمله، URL، نام فایل، نام تابع، یا مقدار عددی که در پرامپت آمده،
  دقیقاً همان است که کاربر می‌خواهد — تغییرش نده، رندش نکن، خلاصه‌اش
  نکن.
- اگر پرامپت چندین درخواست/مرحله/زیرتسک دارد، **همه** را پیاده کن. حتی
  یکی را نه به‌عنوان "خارج از scope" حذف کن.

❌ ممنوعات صریح:
- خلاصه‌سازی متن کاربر در commit message یا response
- "این بخش اصلی نیست، رد می‌کنم"
- "کاربر احتمالاً منظورش این بود..." — منظورش همان است که نوشته
- "این URL/نام به نظر قدیمی است، آپدیتش کردم" — تغییر بدون درخواست ممنوع
- پیاده‌سازی فقط بخشی از پرامپت و تظاهر به کامل بودن
- "همه آیتم‌های لیست A را بررسی کردم، B و C مشابه بودند" — نه؛
  هرکدام را جداگانه

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

🔗 **وابستگی‌ها و همگام‌سازی (بسیار حیاتی — هرگز skip نکن):**

این بخش از همهٔ بخش‌های دیگرِ این یادداشت **مهم‌تر** است. اگر نقض شود،
نتیجهٔ کار ممکن است مشروع به‌نظر برسد ولی در عمل بخش‌های دیگر سیستم را عقب
بیندازد، broken reference تولید کند، یا منجر به data corruption شود.

پیش از و حین تغییر، تمام وابستگی‌ها را در **چهار جهت** به‌طور **کامل و
بدون هیچ خلاصه‌سازی** شناسایی و همگام کن:

**۱. وابستگی‌های upstream (این تسک به چه چیزهایی متکی است):**
- چه فایل‌ها، توابع، کلاس‌ها، API endpoint ها، schema های دیتابیس،
  env vars، یا config هایی که این تسک نیاز دارد؟
- آیا قرار است چیزی را ویرایش/حذف کنی که جای دیگر (signature، رفتار،
  return type، side effect) از آن انتظار خاصی می‌رود؟
- اگر dependency جدیدی اضافه می‌کنی، آیا با dependencyهای موجود تداخل
  دارد (نسخه، compat، lock file)؟

**۲. وابستگی‌های downstream (چه چیزهایی به این تسک متکی‌اند):**
- چه فایل‌ها، توابع، تست‌ها، migrations، docs، یا UI component هایی از
  کدی که داری ویرایش/اضافه/حذف می‌کنی **استفاده می‌کنند**؟
- با grep و reference search **همه‌ی** call sites، importها، subclassها،
  reference های مستقیم و غیرمستقیم را پیدا کن — نه فقط چند مورد اصلی.
- خصوصاً برای حذف یا rename: هیچ broken reference نباید باقی بماند.

**۳. وابستگی‌های cross-tier (بسیار مهم — هرگز فقط یک لایه را نبین):**

تسک شما ممکن است از backend، frontend، database، worker، یا هر tier
دیگری شروع شده باشد. ولی تغییرات تقریباً همیشه روی tier های دیگر هم
اثر می‌گذارند. **مستقل از اینکه تسک از کدام tier است**، این چک‌های دو
طرفه را همیشه انجام بده:

🔁 **اگر backend را تغییر دادی** (API، service، model، route):
  → frontend: کدام component/page/hook این endpoint یا data shape را
    مصرف می‌کند؟ type definition، state shape، error handling، loading
    state، form validation، URL routing همگی باید همگام شوند.
  → mobile/SDK/client library (اگر پروژه دارد): همان داستان frontend.
  → database: آیا migration لازم است؟ آیا rollback امن است؟
  → background workers: آیا event producer/consumer ها تحت تأثیرند؟
  → rate limit، auth، CORS، CSP: آیا رفتار جدید پشتیبانی می‌شود؟

🔁 **اگر frontend را تغییر دادی** (component، form، state، route):
  → backend: آیا endpoint جدید/تغییریافته لازم است؟ آیا data shape ای
    که ارسال می‌شود با schema سرور سازگار است؟
  → backend validation: آیا برای ورودی‌های جدید UI کافی است؟
  → permissions/RBAC: آیا feature جدید نیاز به role check جدید دارد؟
  → analytics/tracking: آیا event های جدید باید در backend log شوند؟
  → SEO/SSR: آیا تغییر route نیاز به sitemap/meta tags جدید دارد؟

🔁 **اگر database/migration را تغییر دادی**:
  → backend models (ORM، Pydantic، dataclasses) همگی به‌روزند؟
  → query های raw SQL یا ORM queries با schema جدید سازگارند؟
  → seed data، fixtures، factory functions تست‌ها به‌روزند؟
  → frontend: آیا data shape جدید در UI به‌درستی render می‌شود؟
  → rollback migration نوشته شده و امن است؟

🔁 **اگر API contract یا event schema را تغییر دادی** (REST، GraphQL،
   WebSocket، gRPC، Kafka، …):
  → OpenAPI/GraphQL schema/proto file آپدیت شد؟
  → همه‌ی consumer ها (client، subscriber، webhook، external API
    user) با version جدید سازگارند؟
  → backward compatibility حفظ شده یا migration path روشن است؟
  → versioning header/path اگر breaking change است؟

🔁 **اگر infrastructure یا config را تغییر دادی** (Dockerfile، CI، Render
   config، env، secrets):
  → README setup/installation section به‌روزه؟
  → `.env.example` با env vars جدید آپدیت شد؟
  → deploy script یا CI workflow هم تغییر کرد؟
  → docs/architecture یا diagram های infrastructure به‌روزند؟

⚠️ **هرگز فقط یک tier را تغییر نده و فرض کنی بقیه خودکار همگام می‌شوند.**
   حتی برای تغییرات به‌ظاهر «کوچک»، چک کن.

**۴. وابستگی‌های جانبی (artifacts که همیشه چک شوند):**

تغییرات کد همیشه روی این artifact ها اثر دارند. **همه را** بررسی و
به‌روز کن — مستندات اولویت **بالا** دارد چون فراموش‌شدنی‌ترین است.

  📝 **مستندات** (همیشه چک کن — حتی برای تغییر کوچک کد):
    - README.md (شرح، setup، نمونه‌های استفاده، badge ها)
    - CHANGELOG.md / RELEASE_NOTES.md
    - docs/ folder (architecture، API reference، user guides، runbooks)
    - inline docstrings/کامنت‌های توابع و کلاس‌های تغییریافته
    - OpenAPI/Swagger annotations، JSDoc/TSDoc
    - architecture diagrams (اگر component اضافه/حذف شد)
    - migration guides (اگر breaking change است)

  🌍 **مستندات کاربر**:
    - i18n files و translation keys
    - UI labels، tooltip ها، help text، error messages
    - in-app onboarding (اگر flow جدید است)

  🧪 **تست‌ها**:
    - unit tests (همه‌ی فایل‌های مرتبط — حتی اگر «بی‌ربط» به‌نظر می‌رسد)
    - integration tests
    - e2e tests (Playwright/Cypress/Selenium)
    - snapshot tests (اگر UI تغییر کرد)
    - contract tests (Pact یا مشابه)
    - performance benchmarks (اگر behavior performance-sensitive تغییر کرد)

  🧬 **type definitions و contracts**:
    - .d.ts files
    - Pydantic models، dataclasses
    - Protobuf/Avro/Thrift schemas
    - GraphQL schema definitions
    - JSON Schemas

  🏗 **infrastructure و config**:
    - Dockerfile، docker-compose.yml
    - Kubernetes manifests
    - Render/Vercel/Netlify config
    - GitHub Actions / GitLab CI workflows
    - environment templates (.env.example، .env.sample)
    - feature flags (LaunchDarkly، GrowthBook، config)

  📊 **monitoring و observability**:
    - logging keys (اگر اضافه/حذف شد، log parser ها هم به‌روز شوند)
    - metric names (Prometheus، Datadog)
    - tracing spans
    - alert rules و dashboards
    - error tracking (Sentry rules، groupings)

  🔐 **security**:
    - auth rules (rate limit، CORS، CSP، HSTS)
    - permissions/RBAC config
    - secrets rotation policies
    - audit log events (اگر action جدید اضافه شد)

  💾 **caches و serialization**:
    - cache keys و TTL (اگر data shape یا lifecycle تغییر کرد)
    - serializer formats (Redis، session storage)
    - browser storage (localStorage، IndexedDB schemas)

**قانون مطلق همگام‌سازی:**
- هر چیزی که در (۱)، (۲)، (۳)، یا (۴) شناسایی شد، در **همان workflow
  این تسک** همگام و به‌روز شود. هرگز برای بعد رها نکن.
- اگر یک فایل/تست/docs نسبت به تغییر شما عقب بماند، در بهترین حالت bug،
  در بدترین حالت مشکل امنیتی یا data corruption تولید می‌کند.
- تغییرات همگام‌سازی می‌توانند در commit جداگانه باشند (در همان task)،
  ولی نباید skip شوند یا به «refactor آینده» سپرده شوند.

**هرگز این جمله‌ها قابل قبول نیست:**
- ❌ «بعداً پیداش می‌کنم»
- ❌ «احتمالاً جای دیگه‌ای استفاده نمی‌شه»
- ❌ «این یه refactor جداگانه‌ست — out of scope»
- ❌ «فقط فایل‌های اصلی رو بررسی کردم»
- ❌ «حدس می‌زنم چیزی بهش وابسته نیست»
- ❌ «دامنه‌ی وابستگی‌ها رو خلاصه کردم» — هرگز خلاصه نکن
- ❌ «این task فقط backend است؛ frontend مشکل خودش» — هرگز
- ❌ «این task فقط frontend است؛ backend از قبل کار می‌کند» — هرگز ثابت نکرده
- ❌ «مستندات بعداً به‌روز می‌شن» — همیشه same-task همگام شوند
- ❌ «testها رو نگاه نکردم چون فقط یه تغییر کوچیک بود»

**در commit message یا PR description**، دامنهٔ وابستگی‌های شناسایی‌شده و
همگام‌شده را به‌طور explicit و **per-tier** بنویس. مثال:
```
Dependencies synced:
- upstream: User model schema, auth middleware
- downstream: 3 API endpoints, 5 frontend components, 12 tests
- cross-tier (backend → frontend): UserProfile.tsx, useUser.ts hook,
  api-types.ts (TS definitions)
- cross-tier (backend → infra): .env.example added NEW_AUTH_SCOPES
- side artifacts: OpenAPI spec, README API section, i18n keys for
  new errors, Sentry alert rule for new error code
```
اگر هیچ وابستگی پیدا نکردی در هر کدام از چهار جهت، صریحاً بنویس:
«بررسی شد — هیچ وابستگی upstream / downstream / cross-tier (backend↔
frontend↔db↔infra) / side شناسایی نشد» تا مشخص باشد بررسی **انجام شده**
نه اینکه فراموش شده.

📋 **مدیریت TO-DO برای اقدامات دستی کاربر (همیشه چک کن):**

⚠️ **هشدار بحرانی — قاعدهٔ ضد-فرار:** TO-DO فقط برای کارهایی است که
**واقعاً غیرممکن** برای agent است (نیاز به انسان مطلق)، نه برای کارهایی
که «بزرگ‌اند»، «وقت می‌برند»، یا «نیازمند fixture/setup» هستند. اگر یک
agent در یک سشن بیش از **۲۰٪ از تسک‌ها** را با TO-DO ببندد، یعنی از کار
فرار می‌کند — این الگو در سشن‌های قبلی **مشاهده** شده و الان ممنوع است.

✅ **فقط برای این موارد TO-DO بساز** (لیست بسته — هرچه خارج این لیست
ممنوع است):

  ۱. **Credential/secret که فقط کاربر دارد**:
     - تنظیم API key واقعی در پنل ادمین خارجی (Render، AWS، Stripe، …)
     - تأیید OAuth client روی console آن سرویس
     - paste کردن webhook secret که فقط بعد از ساخت در dashboard ظاهر می‌شود

  ۲. **Account/billing روی سرویس خارجی که کاربر باید عضو شود**:
     - ساخت account جدید روی Stripe/SendGrid/Twilio/Google Cloud
     - تأیید verification شماره یا ID
     - فعال‌سازی subscription پولی

  ۳. **داده/asset خصوصی که فقط کاربر دارد**:
     - آپلود لوگو/تصویر/فونت برند
     - paste کردن داده‌ای که در محل کار کاربر است
     - import داده‌ای که فقط روی device کاربر است

  ۴. **تصمیم سلیقه‌ای/حقوقی/کسب‌وکار**:
     - انتخاب رنگ‌بندی نهایی یا تم
     - متن دقیق Terms of Service / Privacy Policy
     - تعرفهٔ قیمت‌گذاری
     - نام نهایی برند یا دامنه

⛔ **هرگز TO-DO نکن برای** (لیست سیاه — هر چیزی که در این لیست است
**قابل اجرا** توسط agent است، حتی اگر بزرگ یا چندبخشی باشد):

  ❌ UI component / page / dashboard (هر فریم‌ورک: React, Vue, Angular,
     Svelte، حتی اگر معماری بزرگ دارد) — می‌توانی stub اولیه + state
     management + layout + استایل بسازی
  ❌ "نیازمند Google Drive / Stripe / Twilio API" — می‌توانی **client
     stub** با abstraction layer بسازی که با env var واقعی plug-in شود؛
     کد integration یعنی پیاده‌سازی، نه TO-DO
  ❌ "feature بزرگ، چند روز کار می‌برد" — اندازه دلیل defer نیست؛ کوچک
     شروع کن، iterate کن، در همین سشن کامل کن
  ❌ Celery / background worker / scheduler — یک task ساده + register
     می‌توانی بسازی
  ❌ Migration / model / schema — حتی اگر فیلد جدید نیاز دارد، اضافه کن
  ❌ REST endpoint / GraphQL resolver / WebSocket route — هرگز TO-DO
  ❌ test (unit/integration/e2e) — همیشه قابل نوشتن
  ❌ Documentation / README / API docs — همیشه قابل نوشتن
  ❌ Config file / .env.example / Dockerfile / CI workflow — همیشه قابل
     نوشتن
  ❌ "می‌توانستی .tsx ولی repo .jsx است" — از .jsx استفاده کن، TO-DO نکن
  ❌ "نیازمند فیلد X در مدل دیگر" — اضافه کن فیلد را، TO-DO نکن
  ❌ "تصمیم admin-vs-user-scoped" — پرامپت اولیه scope را معلوم کرده،
     یا با محتاطانه‌ترین تفسیر پیش برو
  ❌ "credential در production هنوز ست نیست" — این TO-DO ساده برای
     تنظیم env var است (مورد ۱ بالا)، نه دلیل برای defer کردن کد
  ❌ "نیازمند verification از کاربر" — اگر اقدام واقعی غیرممکن نیست،
     پیش برو
  ❌ هر چیزی که در یک کامنت `# TODO` معمولی نوشته می‌شد — این فایل
     TO-DO نیست، کامنت inline است

🔬 **قاعدهٔ «حداقل تلاش» قبل از TO-DO**: قبل از TO-DO کردن یک AC، **اثبات
کن** که قابل انجام نیست:

  ۱. آیا می‌توانم یک stub/placeholder بسازم که با env واقعی plug-in شود؟
     → اگر بله، بساز و TO-DO نکن
  ۲. آیا می‌توانم برای این بخش یک test (حتی mock-based) بنویسم؟
     → اگر بله، بنویس و TO-DO نکن
  ۳. آیا می‌توانم abstraction/interface را تعریف کنم، حتی اگر backend
     واقعی نیست؟ → اگر بله، تعریف کن و TO-DO نکن
  ۴. آیا فقط یک حالت سلیقه‌ای/decision کاربر در میان است؟
     → فقط آن یک decision را TO-DO کن، نه کل feature را

اگر یکی از این چهار راه‌حل ممکن بود ولی به TO-DO رفتی، **اعتبار شما از
بین می‌رود**.

📊 **آستانهٔ TO-DO per session**: در یک حلقهٔ اجرای N تسک، اگر بیشتر از
**۲۰٪** تسک‌ها فایل TO-DO ساختی، خودت در گزارش پایانی صریحاً اعلام کن:

  "⚠️ نسبت TO-DO من {K}/{N} = {%} است که از آستانهٔ ۲۰٪ بالاتر است.
   احتمالاً برخی از این TO-DO ها قابل اجرا بودند ولی من فرار کردم.
   لیست TO-DO ها را کاربر باید بازبینی کند که آیا واقعاً Manual-required
   بودند یا agent ضعیف کار کرده."

**یادآوری همیشگی:** اگر در آینده قابلیت‌های شما گسترش پیدا کرد و توانستید
یکی از موارد لیست سفید را خودکار انجام دهید (مثلاً managed credential
injection، یا integration پولی automate شود)، انجام دهید و TO-DO نسازید.
لیست سفید بسته است ولی **بسته از پایین** (می‌تواند کوچک‌تر شود اگر
قابلیت‌ها رشد کنند، ولی هرگز بزرگ‌تر نشود برای فرار).

**اگر هیچ بخش Manual-required نبود (تمام تسک Auto-capable است)**:
  → فایل TO-DO **نساز**. فولدر TO-DO/ باید پاک و معنادار بماند.
  → اگر برای این task از قبل `TO-DO/todo-task-{task_id_first_8}.md` بود
     (یعنی در run قبلی نیاز به دخالت کاربر بود ولی الان نه): فایل قدیمی
     را پاک کن و entry را از `TO-DO/_index.json` حذف کن.

**اگر بخش Manual-required دارد** (همه‌جانبه یا hybrid):
  1. فولدر TO-DO/ را در ریشه ریپو ایجاد کن اگر نیست
  2. فایل `TO-DO/todo-task-{task_id_first_8}.md` بساز با front-matter
     شامل: task_id, task_title, execution_priority, created_at,
     updated_at, status: "pending"
     و در بدنه: «چرا این فایل ساخته شد»، «وضعیت بخش‌های خودکار»
     (commit ها reference)، «کارهایی که باید انجام دهی» با اولویت
     بالا/متوسط/پایین به ترتیب، «وقتی این کارها را تمام کردی»
  3. `TO-DO/_index.json` را با **merge** آپدیت کن (نه overwrite):
     - فایل موجود را بخوان
     - entry های orphan (فایلشان پاک شده) را حذف کن
     - entry این task را اضافه/replace کن
     - بر اساس execution_priority صعودی مرتب کن
     - ساختار: `{"version":1, "generated_at": ISO, "total": N, "items": [...]}`
  4. این تغییرات TO-DO را در **همان commit کد** شامل کن (نه commit جداگانه)

⛔ **ممنوعات مطلق TO-DO**:
  ❌ ساختن TO-DO برای کاری که می‌توانستی خودت انجام دهی (شلوغی فولدر)
  ❌ overwrite کردن `TO-DO/_index.json` بدون merge (data loss)
  ❌ نگه‌داشتن entry هایی که فایل‌شان پاک شده (broken reference)
  ❌ فراموش کردن نوشتن «خروجی مورد انتظار» در هر آیتم TO-DO

این بخش الزامی است. حتی اگر فکر می‌کنی "این تسک کاملاً auto است و نیازی
به TO-DO نیست"، صریحاً در commit message یا report بنویس:
"بررسی شد — این تسک هیچ بخش Manual-required ندارد، TO-DO ساخته نشد."

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

🔁 **Commit + Push فوری per-task (بسیار مهم برای جریان کار صحیح):**

پس از اتمام پیاده‌سازی این تسک، **بلافاصله** commit کن و **همان موقع**
به default branch (main/master) push کن. سپس به تسک بعدی برو.

✓ چرا این قانون حیاتی است:
  - تسک‌های بعدی ممکن است به فایل‌ها/تغییراتی که این تسک ایجاد کرده
    نیاز داشته باشند. اگر push نکنی، `git pull` بعدی آن‌ها را نمی‌بیند.
  - جمع‌کردن تغییرات چند تسک منجر به conflict های بزرگ می‌شود.
  - اگر در میانه fail کنی، task های push شده ضایع نمی‌شوند.

⛔ ممنوع: "همه task ها را تمام می‌کنم بعد یک‌جا push می‌زنم"
⛔ ممنوع: branch جدا برای task — مستقیم به default branch
⛔ ممنوع: task بعدی بدون push کامل task قبلی

---

🧬 این یک تسک تلفیقی است — از 4 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی بهبود پایداری و قابلیت اطمینان پایپلاین پردازش داده‌ها، به ویژه برای فایل‌های اکسل، تمرکز دارند. شامل مدیریت خطاهای فایل‌های خراب/خالی، تعریف و اعتبارسنجی schema برای فایل‌های اکسل، مشخص کردن خروجی کامپوننت‌ها و افزودن پشتیبانی از فرمت‌های مختلف اکسل است.
🎯 theme: پایپلاین پردازش فایل‌های اکسل
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 4
  id: 93988a1c-6d13-40f8-b5a9-8c49c377c7c6
  عنوان اصلی: پیاده‌سازی مدیریت خطای فایل‌های خراب یا خالی
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["corrupt", "empty", "invalid format", "error handling", "try.*except", "raise"], "files_hint": ["backend/app/data_pipeline.py", "backend/app/data_processor.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "decision", "rationale"], "files_hint": ["docs/decisions/"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_data_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["why", "decision", "rationale", "reason"], "files_hint": ["PR description"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم مدیریت خطا برای فایل‌های خراب یا خالی

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

هیچ اشاره‌ای به handling حالت‌های خطا مانند فایل خراب (corrupt)، خالی (empty)، یا فرمت نادرست نشده است. اگر فایل‌های Excel باز نشوند یا داده‌ای نداشته باشند، pipeline ممکن است crash کند یا نتایج نادرست بدهد.

## 💥 پیامد (impact)
در صورت وجود فایل خراب یا خالی، pipeline متوقف می‌شود (یا داده‌های ناقص تولید می‌کند) و نیاز به مداخله دستی دارد. این باعث کاهش reliability و افزایش زمان debug می‌شود.

## 🛠 پیشنهاد رفع اولیه
یک مرحله بررسی اولیه اضافه کنید: بررسی وجود فایل، فرمت معتبر، و وجود حداقل یک شیت با داده. در صورت خطا، یک log مناسب ثبت کرده و pipeline را با خطای مشخص متوقف کنید یا از یک fallback استفاده کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا — بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا
  - اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده — اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده
  - اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel — اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel
  - اضافه کردن لاگینگ مناسب برای خطاهای مربوط به فایل در pipeline داده — اضافه کردن لاگینگ مناسب برای خطاهای فایل در pipeline داده
  - توقف pipeline با خطای مشخص در صورت بروز خطای فایل (بدون fallback) — توقف pipeline با خطای مشخص در صورت بروز خطای فایل
  - نوشتن تست‌های واحد (unit tests) برای توابع اعتبارسنجی فایل — نوشتن unit tests برای توابع اعتبارسنجی فایل
  - نوشتن تست‌های یکپارچه‌سازی (integration tests) برای pipeline داده با فایل‌های خراب/خالی — نوشتن integration tests برای pipeline داده با فایل‌های خراب/خالی
  - بررسی نهایی و مستندسازی تغییرات در مستندات پروژه — بررسی نهایی و مستندسازی تغییرات در مستندات پروژه

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 4
  id: fc686bb9-3172-4810-9b26-624303be2a32
  عنوان اصلی: تعریف و اعتبارسنجی schema فایل‌های Excel در pipeline
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["binary archive file", "schema", "Excel", "sheet", "column"], "files_hint": ["backend/app/pipeline/data.py", "backend/app/pipeline/schemas.py", "backend/app/pipeline/config.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "schema", "Excel", "binary"], "files_hint": ["backend/app/pipeline/data.py", "backend/app/pipeline/schemas.py"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_pipeline_data.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md", "docs/decisions/"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم وجود schema مشخص برای فایل‌های باینری

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

فایل‌های Excel به عنوان 'binary archive file' معرفی شده‌اند، اما هیچ schema یا ساختار داده‌ای برای محتوای داخلی آن‌ها (مثل نام شیت‌ها، ستون‌ها، نوع داده‌ها) تعریف نشده است. این باعث می‌شود که pipeline نتواند سازگاری داده‌ها را در مراحل بعدی بررسی کند.

## 💥 پیامد (impact)
در صورت تغییر ساختار فایل‌های Excel (مثلاً تغییر نام ستون‌ها یا حذف شیت‌ها)، pipeline بدون خطا اجرا می‌شود اما داده‌های نادرست یا ناقص تولید می‌کند. همچنین امکان validation خودکار وجود ندارد.

## 🛠 پیشنهاد رفع اولیه
یک schema مشخص برای هر فایل Excel تعریف کنید: نام شیت‌ها، نام ستون‌ها، نوع داده‌ها (مثلاً string, number, date) و محدوده مجاز مقادیر. سپس در pipeline یک مرحله validation برای تطبیق داده‌های ورودی با schema اضافه کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و شناسایی فایل‌های Excel موجود در pipeline data — شناسایی و مستندسازی فایل‌های Excel موجود در pipeline data
  - تعریف schema برای هر فایل Excel شامل نام شیت‌ها و ستون‌ها — تعریف schema برای هر فایل Excel شامل شیت‌ها و ستون‌ها
  - اضافه کردن مرحله validation در pipeline برای تطبیق داده‌های ورودی با schema — اضافه کردن مرحله validation در pipeline برای تطبیق با schema
  - نوشتن تست‌های unit برای validation schema — نوشتن تست‌های unit برای validation schema
  - نوشتن تست‌های integration برای pipeline با validation — نوشتن تست‌های integration برای pipeline با validation
  - مستندسازی schema و validation در مستندات پروژه — مستندسازی schema و validation در مستندات پروژه

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 4
  id: e0513e78-010b-4e28-bc31-4cc597182f0b
  عنوان اصلی: مشخص کردن خروجی کامپوننت‌های pipeline data
  اولویت اصلی: medium
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["Preserved original Excel file", "downstream", "استخراج", "CSV", "database"], "files_hint": ["backend/pipeline/data.py", "backend/pipeline/README.md", "backend/pipeline/data/*.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "output format", "target schema"], "files_hint": ["backend/pipeline/data.py", "backend/pipeline/config.py", "backend/pipeline/data/*.py"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_pipeline_data.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["چرا این تصمیم گرفته شد", "rationale", "decision", "reason"], "files_hint": ["PR description"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم تعریف خروجی مشخص برای مراحل بعدی

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

خروجی این کامپوننت‌ها فقط 'Preserved original Excel file' تعریف شده است، اما مشخص نیست که pipeline چگونه از این فایل‌ها استفاده می‌کند. آیا باید داده‌ها استخراج شوند؟ به چه فرمتی؟ آیا باید به دیتابیس یا فایل CSV تبدیل شوند؟

## 💥 پیامد (impact)
این ابهام باعث می‌شود که اتصال بین این کامپوننت‌ها و مراحل downstream نامشخص باشد. توسعه‌دهندگان ممکن است فرضیات متفاوتی داشته باشند و pipeline ناقص یا ناسازگار شود.

## 🛠 پیشنهاد رفع اولیه
خروجی مورد انتظار را به صورت دقیق تعریف کنید: مثلاً 'Extracted data as pandas DataFrame with columns: [col1, col2, ...]' یا 'Converted to CSV file at path: ...'. همچنین مشخص کنید که آیا فایل اصلی باید unchanged بماند یا تغییر کند.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - شناسایی و مستندسازی pipeline data و کامپوننت‌های آن — مستندسازی کامل فرض‌های هر دو طرف ناسازگاری
  - تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline data — تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline
  - اصلاح کامپوننت‌های pipeline data برای تولید خروجی مشخص — اصلاح کامپوننت‌ها برای تولید خروجی مشخص
  - به‌روزرسانی کامپوننت‌های downstream برای استفاده از خروجی جدید — به‌روزرسانی کامپوننت‌های downstream برای خروجی جدید
  - نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده pipeline data — نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده
  - نوشتن تست‌های integration برای pipeline data — نوشتن تست‌های integration برای pipeline data
  - به‌روزرسانی مستندات pipeline data با تغییرات اعمال‌شده — به‌روزرسانی مستندات pipeline data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 4 از 4
  id: 45d3c335-4be5-47cd-8394-997476ca53ef
  عنوان اصلی: پشتیبانی از فرمت‌های .xlsm و .xls در پایپلاین
  اولویت اصلی: low
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["xlsm", "xls", "original-excel-files"], "files_hint": ["backend/app/data_pipeline.py", "backend/app/handlers/excel_handler.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground.truth", "align", "xlsm.*xls"], "files_hint": ["backend/app/data_pipeline.py", "backend/app/handlers/excel_handler.py"]}]
  - integration test برای pipeline `data` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_data_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم تفکیک بین فایل‌های .xlsm و .xls

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline data است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `data` یک ناسازگاری منطقی پیدا شد:

دو فایل با فرمت‌های مختلف (.xlsm و .xls) در یک دسته 'original-excel-files' قرار دارند، اما هیچ تمایزی در handling آن‌ها وجود ندارد. فایل .xlsm حاوی macro است و نیاز به رویکرد متفاوتی برای خواندن دارد (مثلاً اجرای macro یا صرفاً خواندن داده).

## 💥 پیامد (impact)
اگر pipeline هر دو فایل را با یک روش (مثلاً pandas.read_excel) بخواند، ممکن است macroهای فایل .xlsm اجرا نشوند یا داده‌های حاصل از macro از دست بروند. همچنین فایل .xls قدیمی‌تر است و ممکن است با کتابخانه‌های جدید compatibility مشکل داشته باشد.

## 🛠 پیشنهاد رفع اولیه
برای هر فرمت یک handler جداگانه تعریف کنید: برای .xlsm از openpyxl (با گزینه read_only یا data_only) و برای .xls از xlrd استفاده کنید. اگر macroها ضروری هستند، یک مرحله جداگانه برای اجرای macroها (با win32com یا xlwings) اضافه کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `data` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: low
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی و شناسایی فایل‌های موجود در pipeline data و نحوه handling فعلی

🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن کتابخانه‌های openpyxl و xlrd به وابستگی‌های پروژه — اضافه کردن openpyxl و xlrd به requirements.txt
  - ایجاد یک تابع handler مجزا برای فایل‌های .xlsm با استفاده از openpyxl — ایجاد تابع read_xlsm_file با openpyxl
  - ایجاد یک تابع handler مجزا برای فایل‌های .xls با استفاده از xlrd — ایجاد تابع read_xls_file با xlrd
  - اصلاح pipeline اصلی برای تشخیص خودکار فرمت فایل و استفاده از handler مناسب — تشخیص خودکار فرمت فایل و انتخاب handler مناسب
  - اضافه کردن قابلیت اجرای macro برای فایل‌های .xlsm (اختیاری، در صورت نیاز) — اضافه کردن قابلیت اجرای macro برای .xlsm
  - یکپارچه‌سازی قابلیت اجرای macro در pipeline (در صورت نیاز) — یکپارچه‌سازی اجرای macro در pipeline
  - نوشتن تست‌های واحد (unit tests) برای handlerهای جدید — نوشتن unit tests برای handlerهای جدید
  - نوشتن تست‌های یکپارچه‌سازی (integration tests) برای کل فرآیند خواندن فایل‌های Excel — نوشتن integration tests برای کل فرآیند خواندن Excel
  - بازبینی نهایی (audit) و مستندسازی تغییرات — بازبینی نهایی و مستندسازی تغییرات

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 93988a1c-6d13-40f8-b5a9-8c49c377c7c6, fc686bb9-3172-4810-9b26-624303be2a32, e0513e78-010b-4e28-bc31-4cc597182f0b, 45d3c335-4be5-47cd-8394-997476ca53ef`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد _(verify: static)_
2. ground truth تعیین شد و طرف دیگر align شد _(verify: static)_
3. integration test برای pipeline `data` بدون شکست عبور می‌کند _(verify: backend_test)_
4. PR description توضیح می‌دهد چرا این تصمیم گرفته شد _(verify: static)_

## Task Steps

### Step 1: بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی کامل فایل‌های موجود در pipeline داده برای شناسایی وضعیت فعلی مدیریت خطا برای فایل‌های خراب یا خالی است. باید فایل‌های backend/app/data_pipeline.py و backend/app/data_processor.py و هر فایل مرتبط دیگر بررسی شوند. خارج از این مرحله: ایجاد تغییرات در کد یا نوشتن تست. نکته حیاتی: قبل از هر تغییری باید وضعیت فعلی به دقت مستند شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا — بررسی و شناسایی فایل‌های مرتبط با pipeline داده و وضعیت فعلی مدیریت خطا
```

### Step 2: اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده
**Status:** `done` (100%)
**Scope:** این مرحله شامل اضافه کردن یک تابع جدید برای بررسی وجود فایل و اعتبارسنجی فرمت آن در ابتدای pipeline داده است. تابع باید در backend/app/data_pipeline.py یا فایل مناسب دیگر اضافه شود. خارج از این مرحله: بررسی محتوای فایل یا داده‌های داخل آن. نکته حیاتی: تابع باید قبل از هر پردازش دیگری فراخوانی شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده — اضافه کردن تابع بررسی وجود فایل و فرمت معتبر در ابتدای pipeline داده
```

### Step 3: اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel
**Status:** `done` (100%)
**Scope:** این مرحله شامل اضافه کردن منطق بررسی وجود حداقل یک شیت با داده در فایل Excel است. باید پس از تأیید وجود فایل و فرمت معتبر، بررسی کند که فایل حداقل یک شیت غیرخالی داشته باشد. خارج از این مرحله: بررسی محتوای ستون‌ها یا نوع داده‌ها. نکته حیاتی: فایل‌های خالی (بدون داده) باید به عنوان خطا شناسایی شوند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel — اضافه کردن بررسی وجود حداقل یک شیت با داده در فایل Excel
```

### Step 4: اضافه کردن لاگینگ مناسب برای خطاهای مربوط به فایل در pipeline داده
**Status:** `done` (100%)
**Scope:** این مرحله شامل اضافه کردن لاگینگ مناسب برای تمام خطاهای مربوط به فایل (فایل خراب، خالی، فرمت نامعتبر) در pipeline داده است. لاگ‌ها باید شامل جزئیات خطا، نام فایل و زمان وقوع باشند. خارج از این مرحله: لاگینگ خطاهای دیگر pipeline. نکته حیاتی: لاگ‌ها باید در سطح ERROR ثبت شوند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن لاگینگ مناسب برای خطاهای مربوط به فایل در pipeline داده — اضافه کردن لاگینگ مناسب برای خطاهای فایل در pipeline داده
```

### Step 5: توقف pipeline با خطای مشخص در صورت بروز خطای فایل
**Status:** `done` (100%)
**Scope:** این مرحله شامل اصلاح pipeline به گونه‌ای است که در صورت بروز هرگونه خطای فایل (خراب، خالی، فرمت نامعتبر)، pipeline با یک خطای مشخص و قابل فهم متوقف شود. خارج از این مرحله: استفاده از fallback یا ادامه پردازش با داده‌های پیش‌فرض. نکته حیاتی: خطا باید به صورت واضح به caller گزارش شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - توقف pipeline با خطای مشخص در صورت بروز خطای فایل (بدون fallback) — توقف pipeline با خطای مشخص در صورت بروز خطای فایل
```

### Step 6: نوشتن تست‌های واحد (unit tests) برای توابع اعتبارسنجی فایل
**Status:** `done` (100%)
**Scope:** این مرحله شامل نوشتن تست‌های واحد برای توابع جدید اعتبارسنجی فایل (بررسی وجود فایل، فرمت معتبر، وجود شیت با داده) است. تست‌ها باید در tests/test_data_pipeline.py اضافه شوند. خارج از این مرحله: تست‌های یکپارچه‌سازی. نکته حیاتی: هر تابع باید حداقل یک تست مثبت و یک تست منفی داشته باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های واحد (unit tests) برای توابع اعتبارسنجی فایل — نوشتن unit tests برای توابع اعتبارسنجی فایل
```

### Step 7: نوشتن تست‌های یکپارچه‌سازی (integration tests) برای pipeline داده با فایل‌های خراب/خالی
**Status:** `done` (100%)
**Scope:** این مرحله شامل نوشتن تست‌های یکپارچه‌سازی برای pipeline داده با استفاده از فایل‌های خراب و خالی است. تست‌ها باید در tests/test_data_pipeline.py اضافه شوند و رفتار pipeline را در سناریوهای خطا بررسی کنند. خارج از این مرحله: تست‌های واحد. نکته حیاتی: تست‌ها باید شامل فایل‌های خراب، خالی و با فرمت نامعتبر باشند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های یکپارچه‌سازی (integration tests) برای pipeline داده با فایل‌های خراب/خالی — نوشتن integration tests برای pipeline داده با فایل‌های خراب/خالی
```

### Step 8: بررسی نهایی و مستندسازی تغییرات در مستندات پروژه
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی نهایی تمام تغییرات اعمال‌شده در تسک 1 و مستندسازی آن‌ها در مستندات پروژه است. باید تغییرات در فایل README یا docs/ مرتبط ثبت شوند. خارج از این مرحله: ایجاد تغییرات جدید در کد. نکته حیاتی: مستندات باید شامل نحوه عملکرد مدیریت خطا و خطاهای قابل برگشت باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی نهایی و مستندسازی تغییرات در مستندات پروژه — بررسی نهایی و مستندسازی تغییرات در مستندات پروژه
```

### Step 9: بررسی و شناسایی فایل‌های Excel موجود در pipeline data
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی کامل فایل‌های Excel موجود در pipeline data و مستندسازی ساختار فعلی آن‌ها است. باید فایل‌های backend/app/pipeline/data.py و backend/app/pipeline/schemas.py و backend/app/pipeline/config.py بررسی شوند. خارج از این مرحله: ایجاد تغییرات در کد. نکته حیاتی: باید نام شیت‌ها و ستون‌های موجود شناسایی شوند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و شناسایی فایل‌های Excel موجود در pipeline data — شناسایی و مستندسازی فایل‌های Excel موجود در pipeline data
```

### Step 10: تعریف schema برای هر فایل Excel شامل نام شیت‌ها و ستون‌ها
**Status:** `done` (100%)
**Scope:** این مرحله شامل تعریف یک schema مشخص برای هر فایل Excel در pipeline data است. schema باید شامل نام شیت‌ها، نام ستون‌ها، نوع داده‌ها و محدوده مجاز مقادیر باشد. schema باید در backend/app/pipeline/schemas.py تعریف شود. خارج از این مرحله: پیاده‌سازی validation. نکته حیاتی: schema باید به صورت dataclass یا کلاس مشابه تعریف شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - تعریف schema برای هر فایل Excel شامل نام شیت‌ها و ستون‌ها — تعریف schema برای هر فایل Excel شامل شیت‌ها و ستون‌ها
```

### Step 11: اضافه کردن مرحله validation در pipeline برای تطبیق داده‌های ورودی با schema
**Status:** `done` (100%)
**Scope:** این مرحله شامل اضافه کردن یک مرحله validation در pipeline data است که داده‌های ورودی را با schema تعریف‌شده تطبیق می‌دهد. validation باید در backend/app/pipeline/data.py اضافه شود. خارج از این مرحله: تعریف schema. نکته حیاتی: در صورت عدم تطابق، pipeline باید با خطای مشخص متوقف شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن مرحله validation در pipeline برای تطبیق داده‌های ورودی با schema — اضافه کردن مرحله validation در pipeline برای تطبیق با schema
```

### Step 12: نوشتن تست‌های unit برای validation schema
**Status:** `partial` (50%)
**Scope:** این مرحله شامل نوشتن تست‌های واحد برای توابع validation schema است. تست‌ها باید در tests/test_pipeline_data.py اضافه شوند و تطبیق داده‌ها با schema را در سناریوهای مختلف بررسی کنند. خارج از این مرحله: تست‌های یکپارچه‌سازی. نکته حیاتی: تست‌ها باید شامل موارد مثبت و منفی باشند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های unit برای validation schema — نوشتن تست‌های unit برای validation schema
```

### Step 13: نوشتن تست‌های integration برای pipeline با validation
**Status:** `done` (100%)
**Scope:** این مرحله شامل نوشتن تست‌های یکپارچه‌سازی برای pipeline data با فعال بودن validation schema است. تست‌ها باید در tests/test_pipeline_data.py اضافه شوند و رفتار pipeline را با فایل‌های سازگار و ناسازگار با schema بررسی کنند. خارج از این مرحله: تست‌های واحد. نکته حیاتی: تست‌ها باید شامل سناریوهای مختلف عدم تطابق باشند.
— [merged] این مرحله شامل نوشتن تست‌های یکپارچه‌سازی برای کل pipeline data است. تست‌ها باید در tests/test_pipeline_data.py اضافه شوند و جریان کامل داده را از ورودی تا خروجی بررسی کنند. خارج از این مرحله: تست‌های واحد. نکته حیاتی: تست‌ها باید شامل سناریوهای مختلف ورودی باشند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های integration برای pipeline با validation — نوشتن تست‌های integration برای pipeline با validation
```

### Step 14: مستندسازی schema و validation در مستندات پروژه
**Status:** `done` (100%)
**Scope:** این مرحله شامل مستندسازی schema تعریف‌شده و فرآیند validation در مستندات پروژه است. باید توضیحات مربوط به schema و نحوه عملکرد validation در فایل README یا docs/ مرتبط اضافه شود. خارج از این مرحله: تغییر کد. نکته حیاتی: مستندات باید شامل مثال‌هایی از schema و خطاهای validation باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - مستندسازی schema و validation در مستندات پروژه — مستندسازی schema و validation در مستندات پروژه
```

### Step 15: شناسایی و مستندسازی pipeline data و کامپوننت‌های آن
**Status:** `done` (100%)
**Scope:** این مرحله شامل شناسایی کامل کامپوننت‌های pipeline data و مستندسازی فرض‌های هر دو طرف ناسازگاری است. باید فایل‌های backend/app/pipeline/data.py و backend/pipeline/README.md و backend/pipeline/data/*.py بررسی شوند. خارج از این مرحله: ایجاد تغییرات در کد. نکته حیاتی: فرض‌های هر کامپوننت باید به دقت مستند شوند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - شناسایی و مستندسازی pipeline data و کامپوننت‌های آن — مستندسازی کامل فرض‌های هر دو طرف ناسازگاری
```

### Step 16: تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline data
**Status:** `done` (100%)
**Scope:** این مرحله شامل تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline data است. باید مشخص شود که خروجی هر کامپوننت چیست (مثلاً pandas DataFrame با ستون‌های مشخص، فایل CSV در مسیر مشخص). خارج از این مرحله: اصلاح کد کامپوننت‌ها. نکته حیاتی: خروجی باید به صورت دقیق و قابل اندازه‌گیری تعریف شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline data — تعریف دقیق خروجی مورد انتظار برای هر کامپوننت pipeline
```

### Step 17: اصلاح کامپوننت‌های pipeline data برای تولید خروجی مشخص
**Status:** `done` (100%)
**Scope:** این مرحله شامل اصلاح کامپوننت‌های pipeline data به گونه‌ای است که خروجی مشخص و تعریف‌شده را تولید کنند. باید فایل‌های backend/app/pipeline/data.py و backend/pipeline/data/*.py اصلاح شوند. خارج از این مرحله: به‌روزرسانی کامپوننت‌های downstream. نکته حیاتی: خروجی باید با تعریف مرحله قبل مطابقت داشته باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اصلاح کامپوننت‌های pipeline data برای تولید خروجی مشخص — اصلاح کامپوننت‌ها برای تولید خروجی مشخص
```

### Step 18: به‌روزرسانی کامپوننت‌های downstream برای استفاده از خروجی جدید
**Status:** `done` (100%)
**Scope:** این مرحله شامل به‌روزرسانی کامپوننت‌های downstream برای استفاده از خروجی جدید کامپوننت‌های pipeline data است. باید تمام caller های کامپوننت‌های اصلاح‌شده بررسی و به‌روزرسانی شوند. خارج از این مرحله: اصلاح خود کامپوننت‌های pipeline. نکته حیاتی: باید از سازگاری backward اطمینان حاصل شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - به‌روزرسانی کامپوننت‌های downstream برای استفاده از خروجی جدید — به‌روزرسانی کامپوننت‌های downstream برای خروجی جدید
```

### Step 19: نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده pipeline data
**Status:** `partial` (50%)
**Scope:** این مرحله شامل نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده pipeline data است. تست‌ها باید در tests/test_pipeline_data.py اضافه شوند و خروجی هر کامپوننت را بررسی کنند. خارج از این مرحله: تست‌های یکپارچه‌سازی. نکته حیاتی: هر کامپوننت باید حداقل یک تست مثبت داشته باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده pipeline data — نوشتن تست‌های واحد برای کامپوننت‌های اصلاح‌شده
```

### Step 20: به‌روزرسانی مستندات pipeline data با تغییرات اعمال‌شده
**Status:** `done` (100%)
**Scope:** این مرحله شامل به‌روزرسانی مستندات pipeline data با تغییرات اعمال‌شده در خروجی کامپوننت‌ها است. باید فایل backend/pipeline/README.md و هر فایل مستندات دیگر به‌روزرسانی شود. خارج از این مرحله: تغییر کد. نکته حیاتی: مستندات باید شامل توضیحات دقیق خروجی هر کامپوننت باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - به‌روزرسانی مستندات pipeline data با تغییرات اعمال‌شده — به‌روزرسانی مستندات pipeline data
```

### Step 21: اضافه کردن کتابخانه‌های openpyxl و xlrd به وابستگی‌های پروژه
**Status:** `not_done` (0%)
**Scope:** این مرحله شامل اضافه کردن کتابخانه‌های openpyxl و xlrd به فایل requirements.txt یا pyproject.toml پروژه است. این کتابخانه‌ها برای خواندن فایل‌های .xlsm و .xls استفاده خواهند شد. خارج از این مرحله: پیاده‌سازی handlerها. نکته حیاتی: باید از آخرین نسخه پایدار کتابخانه‌ها استفاده شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن کتابخانه‌های openpyxl و xlrd به وابستگی‌های پروژه — اضافه کردن openpyxl و xlrd به requirements.txt
```

### Step 22: ایجاد تابع read_xlsm_file با استفاده از openpyxl
**Status:** `done` (100%)
**Scope:** این مرحله شامل ایجاد یک تابع handler مجزا برای خواندن فایل‌های .xlsm با استفاده از کتابخانه openpyxl است. تابع باید در backend/app/handlers/excel_handler.py ایجاد شود و قابلیت خواندن داده‌ها با گزینه‌های read_only و data_only را داشته باشد. خارج از این مرحله: اجرای macroها. نکته حیاتی: تابع باید داده‌ها را به صورت pandas DataFrame برگرداند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - ایجاد یک تابع handler مجزا برای فایل‌های .xlsm با استفاده از openpyxl — ایجاد تابع read_xlsm_file با openpyxl
```

### Step 23: ایجاد تابع read_xls_file با استفاده از xlrd
**Status:** `done` (100%)
**Scope:** این مرحله شامل ایجاد یک تابع handler مجزا برای خواندن فایل‌های .xls با استفاده از کتابخانه xlrd است. تابع باید در backend/app/handlers/excel_handler.py ایجاد شود. خارج از این مرحله: خواندن فایل‌های .xlsm. نکته حیاتی: تابع باید داده‌ها را به صورت pandas DataFrame برگرداند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - ایجاد یک تابع handler مجزا برای فایل‌های .xls با استفاده از xlrd — ایجاد تابع read_xls_file با xlrd
```

### Step 24: تشخیص خودکار فرمت فایل و انتخاب handler مناسب در pipeline اصلی
**Status:** `done` (100%)
**Scope:** این مرحله شامل اصلاح pipeline اصلی برای تشخیص خودکار فرمت فایل (بر اساس پسوند) و استفاده از handler مناسب (read_xlsm_file یا read_xls_file) است. باید در backend/app/data_pipeline.py یا backend/app/handlers/excel_handler.py پیاده‌سازی شود. خارج از این مرحله: پیاده‌سازی handlerها. نکته حیاتی: برای فایل‌های .xlsx باید از روش پیش‌فرض استفاده شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اصلاح pipeline اصلی برای تشخیص خودکار فرمت فایل و استفاده از handler مناسب — تشخیص خودکار فرمت فایل و انتخاب handler مناسب
```

### Step 25: اضافه کردن قابلیت اجرای macro برای فایل‌های .xlsm (اختیاری)
**Status:** `not_done` (0%)
**Scope:** این مرحله شامل اضافه کردن قابلیت اجرای macro برای فایل‌های .xlsm است. این قابلیت باید به صورت اختیاری و با استفاده از کتابخانه‌های win32com یا xlwings پیاده‌سازی شود. خارج از این مرحله: یکپارچه‌سازی در pipeline. نکته حیاتی: این قابلیت فقط در صورت نیاز و در محیط‌های دارای Excel فعال می‌شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - اضافه کردن قابلیت اجرای macro برای فایل‌های .xlsm (اختیاری، در صورت نیاز) — اضافه کردن قابلیت اجرای macro برای .xlsm
```

### Step 26: یکپارچه‌سازی قابلیت اجرای macro در pipeline (در صورت نیاز)
**Status:** `not_done` (0%)
**Scope:** این مرحله شامل یکپارچه‌سازی قابلیت اجرای macro در pipeline اصلی است. اگر مرحله قبل (اجرای macro) پیاده‌سازی شده باشد، این مرحله آن را در pipeline ادغام می‌کند. خارج از این مرحله: پیاده‌سازی خود قابلیت اجرای macro. نکته حیاتی: اجرای macro باید به صورت اختیاری و قابل تنظیم باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - یکپارچه‌سازی قابلیت اجرای macro در pipeline (در صورت نیاز) — یکپارچه‌سازی اجرای macro در pipeline
```

### Step 27: نوشتن تست‌های واحد (unit tests) برای handlerهای جدید
**Status:** `not_done` (0%)
**Scope:** این مرحله شامل نوشتن تست‌های واحد برای handlerهای جدید (read_xlsm_file و read_xls_file) است. تست‌ها باید در tests/test_data_pipeline.py یا فایل تست جدید اضافه شوند. خارج از این مرحله: تست‌های یکپارچه‌سازی. نکته حیاتی: هر handler باید حداقل یک تست مثبت و یک تست منفی داشته باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های واحد (unit tests) برای handlerهای جدید — نوشتن unit tests برای handlerهای جدید
```

### Step 28: نوشتن تست‌های یکپارچه‌سازی (integration tests) برای کل فرآیند خواندن فایل‌های Excel
**Status:** `done` (100%)
**Scope:** این مرحله شامل نوشتن تست‌های یکپارچه‌سازی برای کل فرآیند خواندن فایل‌های Excel با فرمت‌های مختلف (.xlsx, .xlsm, .xls) است. تست‌ها باید در tests/test_data_pipeline.py اضافه شوند. خارج از این مرحله: تست‌های واحد. نکته حیاتی: تست‌ها باید شامل تشخیص خودکار فرمت و استفاده از handler مناسب باشند.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - نوشتن تست‌های یکپارچه‌سازی (integration tests) برای کل فرآیند خواندن فایل‌های Excel — نوشتن integration tests برای کل فرآیند خواندن Excel
```

### Step 29: بازبینی نهایی (audit) و مستندسازی تغییرات
**Status:** `done` (100%)
**Scope:** این مرحله شامل بازبینی نهایی تمام تغییرات اعمال‌شده در تسک 4 و مستندسازی آن‌ها در مستندات پروژه است. باید تغییرات در فایل README یا docs/ مرتبط ثبت شوند. خارج از این مرحله: ایجاد تغییرات جدید در کد. نکته حیاتی: مستندات باید شامل نحوه عملکرد handlerهای جدید و تشخیص خودکار فرمت باشد.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - بازبینی نهایی (audit) و مستندسازی تغییرات — بازبینی نهایی و مستندسازی تغییرات
```

### Step 30: گام ۲: تصمیم‌گیری درباره ground truth برای تسک 1 (مدیریت خطا)
**Status:** `done` (100%)
**Scope:** این مرحله شامل تصمیم‌گیری درباره اینکه کدام طرف ناسازگاری در تسک 1 (مدیریت خطا) ground truth است و مستندسازی این تصمیم است. باید فرض‌های هر دو طرف بررسی و مشخص شود کدام یک منطق کسب‌وکار را بهتر پشتیبانی می‌کند. خارج از این مرحله: پیاده‌سازی تغییرات. نکته حیاتی: تصمیم باید در docs/decisions/ مستند شود.
**Excerpt:**
```
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
```

### Step 31: گام ۳: align کردن طرف دیگر با ground truth برای تسک 1 (مدیریت خطا)
**Status:** `done` (100%)
**Scope:** این مرحله شامل align کردن طرف دیگر ناسازگاری با ground truth انتخاب‌شده در مرحله قبل است. باید کد طرف دیگر اصلاح شود تا با ground truth مطابقت داشته باشد. خارج از این مرحله: نوشتن تست. نکته حیاتی: تغییرات باید minimal باشند و فقط برای align کردن انجام شوند.
**Excerpt:**
```
گام ۳: طرف دیگر را با ground truth align کن.
```
