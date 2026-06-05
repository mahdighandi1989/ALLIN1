---
task_id: task_02dfbac2d524
title: پیاده‌سازی مانیتورینگ خطاها و عملکرد سیستم
type: other
priority: high
execution_priority: 2100
status: pending
external_status: done
verification_status: applied_externally_pending_verify
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:15:14.835242+00:00'
updated_at: '2026-06-05T01:00:26.755759+00:00'
tags:
- consolidated
- post_verify_merge
---

# پیاده‌سازی مانیتورینگ خطاها و عملکرد سیستم

## Raw Idea

🧬 این یک تسک تلفیقی است — از 2 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی افزایش قابلیت مشاهده (observability) سیستم از طریق پیاده‌سازی مانیتورینگ جامع خطاها و افزودن معیارهای عملکردی کلیدی تمرکز دارند. این اقدامات به تشخیص سریع مشکلات و ارزیابی سلامت و کارایی سیستم کمک می‌کنند.
🎯 theme: بهبود مانیتورینگ و جمع‌آوری معیارهای عملکردی
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 2
  id: 7eb31c02-841d-4090-aa7f-29b8f60bc27f
  عنوان اصلی: پیاده‌سازی مانیتورینگ جامع خطاهای واقعی
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["app.add_exception_handler", "structlog.get_logger", "logger.exception"], "files_hint": ["backend/app/main.py"]}]
  - test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/e2e/test_global_exception_handling.py::test_unhandled_exception_logs_correctly", "timeout_seconds": 60}]
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/simulate-unhandled-error", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["error_id", "message"], "json_contains": {"message": "Interna]

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
[Effectiveness] عدم وجود لاگ‌های خطا در ۳۰ روز اخیر نشان‌دهنده پوشش ناقص مانیتورینگ است

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 🎯 هدف مطلوب (outcome target)
پس از پیاده‌سازی لاگ‌گیری جامع، نرخ شناسایی خطاهای واقعی باید به ۱۰۰٪ برسد و error_rate واقعی سیستم شفاف شود

## 📊 وضعیت فعلی
error_rate_30d = 0.0 با وجود ۲ هش (warn) و ۹۸ اطلاعیه (info) که احتمالاً خطاهای خاموش یا نادیده گرفته شده وجود دارد

## 🛠 اقدام پیشنهادی
افزودن exception handlers سراسری در main.py و لاگ‌گیری تمام استثناهای مدیریت‌نشده با structured logging (مانند structlog) و ارسال به سرویس مانیتورینگ

## ⚙️ ماهیت این finding
این یک effectiveness issue است — کد ممکن است syntactically کار کند ولی **outcome مطلوب** (مثل: «فرم باید ایمیل ارسال کند») حاصل نمی‌شود. verify باید outcome را اندازه بگیرد، نه فقط وجود فایل/خط.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] outcome target به‌صورت measurable بازنویسی شد
- [ ] کد تغییر کرد تا outcome target محقق شود
- [ ] test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: outcome target را به‌صورت قابل اندازه‌گیری بازنویسی کن (مثلاً: «email send rate > 95% در ۱۰۰ تلاش»).
گام ۲: کد را تغییر بده تا outcome محقق شود.
گام ۳: یک end-to-end test که outcome را اندازه می‌گیرد بنویس.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest -k 'outcome or e2e'`

## ⚠️ ریسک‌ها و موارد احتیاط
بهبود outcome ممکن است latency یا cost را افزایش دهد — قبل/بعد metric ها را compare کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بازنویسی هدف مطلوب به صورت measurable و اضافه کردن متریک error_rate واقعی — بازنویسی هدف مطلوب به صورت measurable و اضافه کردن متریک error_rate_real
  - افزودن exception handlers سراسری در main.py برای لاگ‌گیری تمام استثناهای مدیریت‌نشده — افزودن exception handlers سراسری در main.py با structured logging
  - ارسال لاگ‌های خطا به سرویس مانیتورینگ (مثلاً Sentry, Datadog, یا custom service) — ارسال لاگ‌های خطا به سرویس مانیتورینگ خارجی
  - اضافه کردن متریک error_rate_real برای اندازه‌گیری نرخ خطاهای واقعی — اضافه کردن متریک error_rate_real برای اندازه‌گیری نرخ خطاهای واقعی
  - نوشتن تست E2E که outcome target (نرخ شناسایی خطاهای واقعی) را اندازه‌گیری می‌کند — نوشتن تست E2E که outcome target را اندازه‌گیری می‌کند
  - اطمینان از عبور تمام تست‌های موجود (pytest/npm run test) بدون fail و بدون warning linter — اطمینان از عبور تمام تست‌های موجود بدون fail و warning linter
  - بررسی و اصلاح type-checking (type-c) برای اطمینان از عبور بدون error — بررسی و اصلاح type-checking برای عبور بدون error

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 2
  id: d0185ac2-49b4-4058-bcee-2088ff932e94
  عنوان اصلی: افزودن معیارهای عملکردی به outcome data
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["prometheus_client", "Histogram", "middleware"], "files_hint": ["backend/app/middleware.py", "backend/app/main.py"]}]
  - test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/e2e/test_performance.py::test_api_latency_within_threshold", "timeout_seconds": 120}]
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/metrics", "headers": null, "json_body": null, "expected_status": 200, "required_fields": null, "json_contains": ["http_request_duration_seconds_bucket", "http_request_durat]

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
[Effectiveness] عدم نمایش معیارهای عملکردی (performance metrics) در outcome data

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 🎯 هدف مطلوب (outcome target)
پس از افزودن metrics، زمان پاسخگویی API باید زیر ۲۰۰ms برای ۹۵٪ درخواست‌ها باقی بماند

## 📊 وضعیت فعلی
outcome data فقط error/warn/info را نشان می‌دهد و هیچ metricی برای latency, throughput, یا database connection pool usage وجود ندارد

## 🛠 اقدام پیشنهادی
افزودن middleware برای ثبت metrics درخواست‌ها (با استفاده از Prometheus client) و نمایش latency percentiles در outcome data

## ⚙️ ماهیت این finding
این یک effectiveness issue است — کد ممکن است syntactically کار کند ولی **outcome مطلوب** (مثل: «فرم باید ایمیل ارسال کند») حاصل نمی‌شود. verify باید outcome را اندازه بگیرد، نه فقط وجود فایل/خط.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] outcome target به‌صورت measurable بازنویسی شد
- [ ] کد تغییر کرد تا outcome target محقق شود
- [ ] test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: outcome target را به‌صورت قابل اندازه‌گیری بازنویسی کن (مثلاً: «email send rate > 95% در ۱۰۰ تلاش»).
گام ۲: کد را تغییر بده تا outcome محقق شود.
گام ۳: یک end-to-end test که outcome را اندازه می‌گیرد بنویس.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest -k 'outcome or e2e'`

## ⚠️ ریسک‌ها و موارد احتیاط
بهبود outcome ممکن است latency یا cost را افزایش دهد — قبل/بعد metric ها را compare کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - افزودن middleware ثبت metrics درخواست‌ها با Prometheus client — ایجاد middleware FastAPI با prometheus_client برای ثبت latency، throughput و database connection pool usage
  - افزودن latency percentiles به outcome data — افزودن latency percentiles (p50, p95, p99) به outcome data
  - بازنویسی outcome target به صورت measurable — بازنویسی outcome target به صورت measurable با threshold عددی
  - تغییر کد برای محقق شدن outcome target — تغییر کد برای کاهش latency یا افزایش throughput به threshold مشخص
  - نوشتن تست E2E برای اندازه‌گیری outcome — نوشتن تست E2E که latency 95% درخواست‌ها زیر 200ms را بررسی کند
  - افزودن metric/log برای تشخیص outcome rate در production — افزودن metric/log aggregated برای نمایش outcome rate در production
  - اجرای تست‌های موجود و linter/type-check برای اطمینان از عدم شکست — اجرای pytest و linter/type-check برای اطمینان از عدم شکست

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 7eb31c02-841d-4090-aa7f-29b8f60bc27f, d0185ac2-49b4-4058-bcee-2088ff932e94`
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

🧬 این یک تسک تلفیقی است — از 2 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی افزایش قابلیت مشاهده (observability) سیستم از طریق پیاده‌سازی مانیتورینگ جامع خطاها و افزودن معیارهای عملکردی کلیدی تمرکز دارند. این اقدامات به تشخیص سریع مشکلات و ارزیابی سلامت و کارایی سیستم کمک می‌کنند.
🎯 theme: بهبود مانیتورینگ و جمع‌آوری معیارهای عملکردی
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 2
  id: 7eb31c02-841d-4090-aa7f-29b8f60bc27f
  عنوان اصلی: پیاده‌سازی مانیتورینگ جامع خطاهای واقعی
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["app.add_exception_handler", "structlog.get_logger", "logger.exception"], "files_hint": ["backend/app/main.py"]}]
  - test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/e2e/test_global_exception_handling.py::test_unhandled_exception_logs_correctly", "timeout_seconds": 60}]
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/simulate-unhandled-error", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["error_id", "message"], "json_contains": {"message": "Interna]

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
[Effectiveness] عدم وجود لاگ‌های خطا در ۳۰ روز اخیر نشان‌دهنده پوشش ناقص مانیتورینگ است

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 🎯 هدف مطلوب (outcome target)
پس از پیاده‌سازی لاگ‌گیری جامع، نرخ شناسایی خطاهای واقعی باید به ۱۰۰٪ برسد و error_rate واقعی سیستم شفاف شود

## 📊 وضعیت فعلی
error_rate_30d = 0.0 با وجود ۲ هش (warn) و ۹۸ اطلاعیه (info) که احتمالاً خطاهای خاموش یا نادیده گرفته شده وجود دارد

## 🛠 اقدام پیشنهادی
افزودن exception handlers سراسری در main.py و لاگ‌گیری تمام استثناهای مدیریت‌نشده با structured logging (مانند structlog) و ارسال به سرویس مانیتورینگ

## ⚙️ ماهیت این finding
این یک effectiveness issue است — کد ممکن است syntactically کار کند ولی **outcome مطلوب** (مثل: «فرم باید ایمیل ارسال کند») حاصل نمی‌شود. verify باید outcome را اندازه بگیرد، نه فقط وجود فایل/خط.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] outcome target به‌صورت measurable بازنویسی شد
- [ ] کد تغییر کرد تا outcome target محقق شود
- [ ] test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: outcome target را به‌صورت قابل اندازه‌گیری بازنویسی کن (مثلاً: «email send rate > 95% در ۱۰۰ تلاش»).
گام ۲: کد را تغییر بده تا outcome محقق شود.
گام ۳: یک end-to-end test که outcome را اندازه می‌گیرد بنویس.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest -k 'outcome or e2e'`

## ⚠️ ریسک‌ها و موارد احتیاط
بهبود outcome ممکن است latency یا cost را افزایش دهد — قبل/بعد metric ها را compare کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بازنویسی هدف مطلوب به صورت measurable و اضافه کردن متریک error_rate واقعی — بازنویسی هدف مطلوب به صورت measurable و اضافه کردن متریک error_rate_real
  - افزودن exception handlers سراسری در main.py برای لاگ‌گیری تمام استثناهای مدیریت‌نشده — افزودن exception handlers سراسری در main.py با structured logging
  - ارسال لاگ‌های خطا به سرویس مانیتورینگ (مثلاً Sentry, Datadog, یا custom service) — ارسال لاگ‌های خطا به سرویس مانیتورینگ خارجی
  - اضافه کردن متریک error_rate_real برای اندازه‌گیری نرخ خطاهای واقعی — اضافه کردن متریک error_rate_real برای اندازه‌گیری نرخ خطاهای واقعی
  - نوشتن تست E2E که outcome target (نرخ شناسایی خطاهای واقعی) را اندازه‌گیری می‌کند — نوشتن تست E2E که outcome target را اندازه‌گیری می‌کند
  - اطمینان از عبور تمام تست‌های موجود (pytest/npm run test) بدون fail و بدون warning linter — اطمینان از عبور تمام تست‌های موجود بدون fail و warning linter
  - بررسی و اصلاح type-checking (type-c) برای اطمینان از عبور بدون error — بررسی و اصلاح type-checking برای عبور بدون error

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 2
  id: d0185ac2-49b4-4058-bcee-2088ff932e94
  عنوان اصلی: افزودن معیارهای عملکردی به outcome data
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["prometheus_client", "Histogram", "middleware"], "files_hint": ["backend/app/middleware.py", "backend/app/main.py"]}]
  - test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/e2e/test_performance.py::test_api_latency_within_threshold", "timeout_seconds": 120}]
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/metrics", "headers": null, "json_body": null, "expected_status": 200, "required_fields": null, "json_contains": ["http_request_duration_seconds_bucket", "http_request_durat]

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
[Effectiveness] عدم نمایش معیارهای عملکردی (performance metrics) در outcome data

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 🎯 هدف مطلوب (outcome target)
پس از افزودن metrics، زمان پاسخگویی API باید زیر ۲۰۰ms برای ۹۵٪ درخواست‌ها باقی بماند

## 📊 وضعیت فعلی
outcome data فقط error/warn/info را نشان می‌دهد و هیچ metricی برای latency, throughput, یا database connection pool usage وجود ندارد

## 🛠 اقدام پیشنهادی
افزودن middleware برای ثبت metrics درخواست‌ها (با استفاده از Prometheus client) و نمایش latency percentiles در outcome data

## ⚙️ ماهیت این finding
این یک effectiveness issue است — کد ممکن است syntactically کار کند ولی **outcome مطلوب** (مثل: «فرم باید ایمیل ارسال کند») حاصل نمی‌شود. verify باید outcome را اندازه بگیرد، نه فقط وجود فایل/خط.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] outcome target به‌صورت measurable بازنویسی شد
- [ ] کد تغییر کرد تا outcome target محقق شود
- [ ] test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: outcome target را به‌صورت قابل اندازه‌گیری بازنویسی کن (مثلاً: «email send rate > 95% در ۱۰۰ تلاش»).
گام ۲: کد را تغییر بده تا outcome محقق شود.
گام ۳: یک end-to-end test که outcome را اندازه می‌گیرد بنویس.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest -k 'outcome or e2e'`

## ⚠️ ریسک‌ها و موارد احتیاط
بهبود outcome ممکن است latency یا cost را افزایش دهد — قبل/بعد metric ها را compare کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - افزودن middleware ثبت metrics درخواست‌ها با Prometheus client — ایجاد middleware FastAPI با prometheus_client برای ثبت latency، throughput و database connection pool usage
  - افزودن latency percentiles به outcome data — افزودن latency percentiles (p50, p95, p99) به outcome data
  - بازنویسی outcome target به صورت measurable — بازنویسی outcome target به صورت measurable با threshold عددی
  - تغییر کد برای محقق شدن outcome target — تغییر کد برای کاهش latency یا افزایش throughput به threshold مشخص
  - نوشتن تست E2E برای اندازه‌گیری outcome — نوشتن تست E2E که latency 95% درخواست‌ها زیر 200ms را بررسی کند
  - افزودن metric/log برای تشخیص outcome rate در production — افزودن metric/log aggregated برای نمایش outcome rate در production
  - اجرای تست‌های موجود و linter/type-check برای اطمینان از عدم شکست — اجرای pytest و linter/type-check برای اطمینان از عدم شکست

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 7eb31c02-841d-4090-aa7f-29b8f60bc27f, d0185ac2-49b4-4058-bcee-2088ff932e94`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. outcome target به‌صورت measurable بازنویسی شد _(verify: manual_only)_
2. کد تغییر کرد تا outcome target محقق شود _(verify: static)_
3. test E2E که outcome را اندازه می‌گیرد عبور می‌کند _(verify: backend_test)_
4. metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد _(verify: api_response)_

## Task Steps

### Step 1: بازنویسی outcome target برای تسک 1 به صورت measurable
**Status:** `not_done` (0%)
**Scope:** این مرحله شامل بازنویسی هدف مطلوب (outcome target) برای تسک 1 (پیاده‌سازی مانیتورینگ جامع خطاهای واقعی) به صورت قابل اندازه‌گیری است. هدف باید به یک معیار عددی مشخص تبدیل شود، مانند 'نرخ شناسایی خطاهای واقعی باید به 100% برسد' یا 'error_rate_real باید کمتر از 0.1% باشد'. این مرحله فقط شامل بازنویسی متن هدف است و هیچ تغییری در کد ایجاد نمی‌کند. خروجی این مرحله یک متن بازنویسی شده از outcome target است که در مستندات یا فایل مربوطه ثبت می‌شود.
— [merged] این مرحله شامل بازنویسی هدف مطلوب (outcome target) برای تسک 2 (افزودن معیارهای عملکردی) به صورت قابل اندازه‌گیری است. هدف باید به یک معیار عددی مشخص تبدیل شود، مانند 'زمان پاسخگویی API باید زیر 200ms برای 95% درخواست‌ها باشد'. این مرحله فقط شامل بازنویسی متن هدف است و هیچ تغییری در کد ایجاد نمی‌کند.
**Excerpt:**
```
## 🎯 هدف مطلوب (outcome target)
پس از پیاده‌سازی لاگ‌گیری جامع، نرخ شناسایی خطاهای واقعی باید به ۱۰۰٪ برسد و error_rate واقعی سیستم شفاف شود

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
```

### Step 2: تغییر کد برای محقق شدن outcome target تسک 1
**Status:** `done` (100%)
**Scope:** این مرحله شامل تغییر کد در فایل backend/app/main.py برای افزودن exception handlers سراسری است. باید از structlog.get_logger برای لاگ‌گیری ساختاریافته استفاده شود و تمام استثناهای مدیریت‌نشده با logger.exception لاگ شوند. این مرحله فقط بر روی backend/app/main.py تمرکز دارد و شامل middleware یا فایل‌های دیگر نمی‌شود. نکته حیاتی: از app.add_exception_handler برای ثبت handler استفاده شود.
— [merged] این مرحله شامل تغییر کد برای کاهش latency یا افزایش throughput به threshold مشخص (زیر 200ms برای 95% درخواست‌ها) است. ممکن است شامل بهینه‌سازی queryها، اضافه کردن caching، یا بهبود معماری باشد. این مرحله بر روی فایل‌های backend تمرکز دارد و شامل frontend نمی‌شود.
**Excerpt:**
```
- کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["app.add_exception_handler", "structlog.get_logger", "logger.exception"], "files_hint": ["backend/app/main.py"]}]

## 🛠 اقدام پیشنهادی
افزودن exception handlers سراسری در main.py و لاگ‌گیری تمام استثناهای مدیریت‌نشده با structured logging (مانند structlog) و ارسال به سرویس مانیتورینگ
```

### Step 3: نوشتن تست E2E برای اندازه‌گیری outcome target تسک 1
**Status:** `not_done` (0%)
**Scope:** این مرحله شامل نوشتن یک تست end-to-end در فایل tests/e2e/test_global_exception_handling.py است. تست باید یک خطای مدیریت‌نشده را شبیه‌سازی کند (مثلاً با فراخوانی endpoint /api/simulate-unhandled-error) و بررسی کند که خطا به درستی لاگ شده است. نام تست باید test_unhandled_exception_logs_correctly باشد. این تست باید با pytest اجرا شود و timeout آن 60 ثانیه است.
— [merged] این مرحله شامل نوشتن یک تست end-to-end در فایل tests/e2e/test_performance.py است. تست باید بررسی کند که latency 95% درخواست‌ها زیر 200ms است. نام تست باید test_api_latency_within_threshold باشد. این تست باید با pytest اجرا شود و timeout آن 120 ثانیه است.
**Excerpt:**
```
- test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/e2e/test_global_exception_handling.py::test_unhandled_exception_logs_correctly", "timeout_seconds": 60}]

## 🪜 مراحل اجرایی پیشنهادی
گام ۳: یک end-to-end test که outcome را اندازه می‌گیرد بنویس.
```

### Step 4: اضافه کردن metric/log برای تشخیص outcome rate در production برای تسک 1
**Status:** `partial` (70%)
**Scope:** این مرحله شامل اضافه کردن یک metric یا log است که در production قابل تشخیص باشد. باید یک endpoint مانند /api/simulate-unhandled-error ایجاد شود که یک خطای مدیریت‌نشده را شبیه‌سازی کند و در پاسخ خود فیلدهای error_id و message را برگرداند. پاسخ باید status 500 داشته باشد و شامل json_contains با message: 'Internal Server Error' باشد. این مرحله فقط بر روی backend/app/main.py تمرکز دارد.
— [merged] این مرحله شامل اضافه کردن یک metric/log aggregated است که در production outcome rate را نمایش دهد. باید یک endpoint /metrics ایجاد شود که metrics مربوط به latency و throughput را در قالب Prometheus exposition format برگرداند. پاسخ باید status 200 داشته باشد و شامل http_request_duration_seconds_bucket و http_request_duration_seconds_sum باشد.
**Excerpt:**
```
- metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/simulate-unhandled-error", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["error_id", "message"], "json_contains": {"message": "Interna
```

### Step 5: اطمینان از عبور تمام تست‌های موجود بدون fail و بدون warning linter برای تسک 1
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای تمام تست‌های موجود (pytest) و linter (مانند flake8 یا pylint) برای اطمینان از عدم وجود fail یا warning است. هیچ تغییری در کد ایجاد نمی‌شود، فقط اجرا و بررسی می‌شود. اگر تست یا linter fail شود، باید خطاها گزارش شوند اما در این مرحله رفع نمی‌شوند.
— [merged] این مرحله شامل اجرای تمام تست‌های موجود (pytest) و linter (مانند flake8 یا pylint) برای اطمینان از عدم وجود fail یا warning است. هیچ تغییری در کد ایجاد نمی‌شود، فقط اجرا و بررسی می‌شود. اگر تست یا linter fail شود، باید خطاها گزارش شوند اما در این مرحله رفع نمی‌شوند.
**Excerpt:**
```
- هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- linter بدون warning عبور می‌کند

## 🧪 دستورات اعتبارسنجی
- `pytest -k 'outcome or e2e'`
```

### Step 6: بررسی و اصلاح type-checking برای عبور بدون error برای تسک 1
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای type-checker (مانند mypy) برای اطمینان از عبور بدون error است. اگر error وجود داشته باشد، باید اصلاح شوند. این مرحله فقط بر روی type-checking تمرکز دارد و شامل تست یا linter نمی‌شود.
— [merged] این مرحله شامل اجرای type-checker (مانند mypy) برای اطمینان از عبور بدون error است. اگر error وجود داشته باشد، باید اصلاح شوند. این مرحله فقط بر روی type-checking تمرکز دارد و شامل تست یا linter نمی‌شود.
**Excerpt:**
```
- type-check موفق است (`tsc --noEmit` / `mypy`)

## 🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و اصلاح type-checking (type-c) برای اطمینان از عبور بدون error — بررسی و اصلاح type-checking برای عبور بدون error
```

### Step 7: ایجاد middleware برای ثبت metrics درخواست‌ها با Prometheus client
**Status:** `done` (100%)
**Scope:** این مرحله شامل ایجاد یک middleware در فایل backend/app/middleware.py است که با استفاده از prometheus_client، metrics مربوط به latency، throughput و database connection pool usage را ثبت کند. middleware باید به برنامه FastAPI در backend/app/main.py اضافه شود. این مرحله فقط بر روی middleware تمرکز دارد و شامل endpointهای دیگر نمی‌شود.
**Excerpt:**
```
- کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["prometheus_client", "Histogram", "middleware"], "files_hint": ["backend/app/middleware.py", "backend/app/main.py"]}]

## 🛠 اقدام پیشنهادی
افزودن middleware برای ثبت metrics درخواست‌ها (با استفاده از Prometheus client) و نمایش latency percentiles در outcome data
```

### Step 8: افزودن latency percentiles به outcome data
**Status:** `partial` (50%)
**Scope:** این مرحله شامل افزودن latency percentiles (p50, p95, p99) به outcome data است. باید metrics مربوط به latency را از Prometheus client جمع‌آوری کرده و به صورت percentiles در outcome data نمایش دهد. این مرحله بر روی backend/app/main.py یا فایل‌های مرتبط با outcome data تمرکز دارد.
**Excerpt:**
```
- افزودن latency percentiles به outcome data — افزودن latency percentiles (p50, p95, p99) به outcome data

## 🔧 مراحل remaining که در super-task باید انجام شوند:
  - افزودن latency percentiles به outcome data — افزودن latency percentiles (p50, p95, p99) به outcome data
```

### Step 9: بررسی وجود پیاده‌سازی قبلی برای تسک 1
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی repo با grep/search برای وجود پیاده‌سازی قبلی مربوط به تسک 1 (مانیتورینگ جامع خطاها) است. باید فایل‌های backend/app/main.py، tests/e2e/test_global_exception_handling.py و هر فایل مرتبط دیگر بررسی شوند. اگر قابلیت‌هایی از قبل وجود دارند، نباید دوباره ساخته شوند.
— [merged] این مرحله شامل بررسی repo با grep/search برای وجود پیاده‌سازی قبلی مربوط به تسک 2 (معیارهای عملکردی) است. باید فایل‌های backend/app/middleware.py، backend/app/main.py، tests/e2e/test_performance.py و هر فایل مرتبط دیگر بررسی شوند. اگر قابلیت‌هایی از قبل وجود دارند، نباید دوباره ساخته شوند.
**Excerpt:**
```
♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
```

### Step 10: بررسی وابستگی‌ها و ترتیب اجرای مراحل
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی وابستگی‌های بین مراحل مختلف و اطمینان از ترتیب منطقی اجرا (foundation → core → integration → tests → audit) است. باید اطمینان حاصل شود که مراحل وابسته به یکدیگر به ترتیب صحیح اجرا می‌شوند. این مرحله فقط شامل برنامه‌ریزی است و هیچ تغییری در کد ایجاد نمی‌کند.
**Excerpt:**
```
🔗 **وابستگی‌های تسکی**
_(مستقل)_

📦 **اگر کار طولانی است:**
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
```

### Step 11: ثبت کامیت‌ها با پیام واضح و PR description
**Status:** `partial` (60%)
**Scope:** این مرحله شامل ثبت کامیت‌های متوالی با پیام‌های واضح و ایجاد PR description است. هر کامیت باید یک مرحله مجزا را پوشش دهد و پیام کامیت باید شامل merged-from با شناسه‌های تسک‌ها (7eb31c02-841d-4090-aa7f-29b8f60bc27f, d0185ac2-49b4-4058-bcee-2088ff932e94) باشد. در PR description باید یک checklist از تمام کامیت‌ها نوشته شود.
**Excerpt:**
```
📦 **اگر کار طولانی است:**
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

- در commit message: `merged-from: 7eb31c02-841d-4090-aa7f-29b8f60bc27f, d0185ac2-49b4-4058-bcee-2088ff932e94`
```
