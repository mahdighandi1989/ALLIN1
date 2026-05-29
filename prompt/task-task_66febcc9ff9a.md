---
task_id: task_66febcc9ff9a
title: 'تقویت جامع امنیت و احراز هویت: از اعتبارسنجی ورودی تا تست‌های خودکار و جلوگیری از نشت اطلاعات'
type: other
priority: critical
execution_priority: 1000
status: pending
external_status: pending
verification_status: pending
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:13:50.338007+00:00'
updated_at: '2026-05-29T22:13:50.338011+00:00'
tags:
- consolidated
- post_verify_merge
---

# تقویت جامع امنیت و احراز هویت: از اعتبارسنجی ورودی تا تست‌های خودکار و جلوگیری از نشت اطلاعات

## Raw Idea

🧬 این یک تسک تلفیقی است — از 3 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها همگی بر روی شناسایی و رفع آسیب‌پذیری‌های امنیتی، بهبود مکانیزم‌های احراز هویت و اعتبارسنجی ورودی‌ها، و جلوگیری از نشت اطلاعات حساس تمرکز دارند. این اقدامات برای افزایش پایداری و اعتمادپذیری سیستم حیاتی هستند.
🎯 theme: تقویت امنیت و احراز هویت سیستم
💎 estimated_difficulty: large

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 3
  id: 3b6da420-9914-4d33-aaa8-3d169dc50e69
  عنوان اصلی: افزودن تست‌های خودکار احراز هویت و امنیت
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["def test_hash_password", "def test_create_access_token", "def test_verify_token", "pytest.mark.parametrize", "jwt.encode", "jwt.decode"], "files_hint": ["tests/test_security.py", "]
  - test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_security.py", "timeout_seconds": 60}]
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=static] [verify_plan={"grep_patterns": ["logger.info", "logger.warning", "metrics.inc", "metrics.observe"], "files_hint": ["backend/app/security.py", "backend/app/api/auth.py"]}]

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
[Effectiveness] عدم وجود تست خودکار برای احراز هویت و امنیت

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 🎯 هدف مطلوب (outcome target)
پس از افزودن تست‌های امنیتی، ۱۰۰٪ سناریوهای احراز هویت (شامل توکن‌های منقضی، رمز عبور اشتباه، حملات brute force) باید پوشش داده شود

## 📊 وضعیت فعلی
فایل security.py وجود دارد اما هیچ تستی برای توابع hash_password, create_access_token, verify_token در outcome data دیده نمی‌شود

## 🛠 اقدام پیشنهادی
افزودن تست‌های unit و integration برای توابع امنیتی با پوشش edge cases مانند توکن JWT با signature نامعتبر، رمز عبور تکراری، و race condition در hash

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
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - افزودن تست‌های unit برای تابع hash_password با پوشش edge cases — نوشتن تست‌های unit برای hash_password با پوشش edge cases (رمز عبور تکراری، خالی، کاراکترهای خاص، race condition)
  - افزودن تست‌های integration برای سناریوهای احراز هویت کامل — نوشتن تست‌های integration برای سناریوهای احراز هویت کامل (توکن منقضی، رمز عبور اشتباه، brute force، JWT نامعتبر)
  - افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production — افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production
  - بازنویسی outcome target به صورت measurable — بازنویسی outcome target به صورت measurable در فایل تسک
  - اجرای تست‌ها و linter برای اطمینان از عدم شکست — اجرای تست‌ها و linter برای اطمینان از عدم شکست

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 3
  id: f7c14bb3-904f-4da1-b5a0-e8691ee049a4
  عنوان اصلی: Add input validation for customer form fields
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["eslint-disable", "// @ts-ignore", "// @ts-expect-error"], "files_hint": ["frontend/src/app/customers/page.tsx", "frontend/src/app/customers/**/*.ts", "frontend/src/app/customers/**]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["// @ts-ignore", "// @ts-expect-error", "any as"], "files_hint": ["frontend/src/app/customers/page.tsx", "frontend/src/app/customers/**/*.ts", "frontend/src/app/customers/**/*.tsx"]]

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
Missing input validation for customer form fields

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
In `frontend/src/app/customers/page.tsx`, the `CustomerForm` component (lines 182-315) does not validate input fields beyond basic HTML `required` attributes. Fields like `account_no`, `name`, `email`, `phone`, and `branch` are not sanitized or validated on the client side. This could allow users to submit malicious data (e.g., XSS payloads, SQL injection attempts) that would be sent directly to the backend API. While backend validation is expected, client-side validation is a critical first line of defense and improves user experience by providing immediate feedback.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. Add client-side validation for all form fields in CustomerForm. Validate email format, phone number format, required field lengths, and sanitize input to prevent XSS.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 3
  id: 6ec6ac9a-3418-48bc-a124-46ca50b1a03d
  عنوان اصلی: جلوگیری از نشت اطلاعات permission در خطاهای API
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/integration/test_auth_pipeline.py::test_no_permission_leak_in_errors", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]

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
[منطق] نشت اطلاعات permission در خطاهای API

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در مستندات frontend (login/page.tsx) اشاره به 'Error toast messages for various failure scenarios' شده است. اگر خطاهای API شامل جزئیات permission (مثلاً 'شما دسترسی ادمین ندارید') باشد، مهاجم می‌تواند از این پیام‌ها برای نقشه‌برداری از ساختار مجوزها استفاده کند.

## 💥 پیامد (impact)
اطلاعات مربوط به permission (مانند نقش‌ها، سطوح دسترسی) به کاربران نهایی نشت می‌کند و امکان حملات brute-force یا privilege escalation را فراهم می‌کند.

## 🛠 پیشنهاد رفع اولیه
تمام پیام‌های خطای مربوط به permission را به یک پیام عمومی مانند 'دسترسی غیرمجاز' تبدیل کنید. جزئیات خطا فقط در لاگ‌های سرور ثبت شود.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
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
  - شناسایی و مستندسازی ناسازگاری منطقی در pipeline auth — شناسایی و مستندسازی کامل ناسازگاری منطقی در pipeline auth
  - اصلاح backend API برای بازگرداندن پیام خطای عمومی به جای جزئیات permission — اصلاح backend API برای بازگرداندن پیام خطای عمومی
  - به‌روزرسانی frontend برای نمایش پیام خطای عمومی و حذف جزئیات permission — به‌روزرسانی frontend برای نمایش پیام خطای عمومی

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 3b6da420-9914-4d33-aaa8-3d169dc50e69, f7c14bb3-904f-4da1-b5a0-e8691ee049a4, 6ec6ac9a-3418-48bc-a124-46ca50b1a03d`
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

🧬 این یک تسک تلفیقی است — از 3 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها همگی بر روی شناسایی و رفع آسیب‌پذیری‌های امنیتی، بهبود مکانیزم‌های احراز هویت و اعتبارسنجی ورودی‌ها، و جلوگیری از نشت اطلاعات حساس تمرکز دارند. این اقدامات برای افزایش پایداری و اعتمادپذیری سیستم حیاتی هستند.
🎯 theme: تقویت امنیت و احراز هویت سیستم
💎 estimated_difficulty: large

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 3
  id: 3b6da420-9914-4d33-aaa8-3d169dc50e69
  عنوان اصلی: افزودن تست‌های خودکار احراز هویت و امنیت
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - outcome target به‌صورت measurable بازنویسی شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["def test_hash_password", "def test_create_access_token", "def test_verify_token", "pytest.mark.parametrize", "jwt.encode", "jwt.decode"], "files_hint": ["tests/test_security.py", "]
  - test E2E که outcome را اندازه می‌گیرد عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_security.py", "timeout_seconds": 60}]
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=static] [verify_plan={"grep_patterns": ["logger.info", "logger.warning", "metrics.inc", "metrics.observe"], "files_hint": ["backend/app/security.py", "backend/app/api/auth.py"]}]

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
[Effectiveness] عدم وجود تست خودکار برای احراز هویت و امنیت

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 🎯 هدف مطلوب (outcome target)
پس از افزودن تست‌های امنیتی، ۱۰۰٪ سناریوهای احراز هویت (شامل توکن‌های منقضی، رمز عبور اشتباه، حملات brute force) باید پوشش داده شود

## 📊 وضعیت فعلی
فایل security.py وجود دارد اما هیچ تستی برای توابع hash_password, create_access_token, verify_token در outcome data دیده نمی‌شود

## 🛠 اقدام پیشنهادی
افزودن تست‌های unit و integration برای توابع امنیتی با پوشش edge cases مانند توکن JWT با signature نامعتبر، رمز عبور تکراری، و race condition در hash

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
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - افزودن تست‌های unit برای تابع hash_password با پوشش edge cases — نوشتن تست‌های unit برای hash_password با پوشش edge cases (رمز عبور تکراری، خالی، کاراکترهای خاص، race condition)
  - افزودن تست‌های integration برای سناریوهای احراز هویت کامل — نوشتن تست‌های integration برای سناریوهای احراز هویت کامل (توکن منقضی، رمز عبور اشتباه، brute force، JWT نامعتبر)
  - افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production — افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production
  - بازنویسی outcome target به صورت measurable — بازنویسی outcome target به صورت measurable در فایل تسک
  - اجرای تست‌ها و linter برای اطمینان از عدم شکست — اجرای تست‌ها و linter برای اطمینان از عدم شکست

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 3
  id: f7c14bb3-904f-4da1-b5a0-e8691ee049a4
  عنوان اصلی: Add input validation for customer form fields
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["eslint-disable", "// @ts-ignore", "// @ts-expect-error"], "files_hint": ["frontend/src/app/customers/page.tsx", "frontend/src/app/customers/**/*.ts", "frontend/src/app/customers/**]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["// @ts-ignore", "// @ts-expect-error", "any as"], "files_hint": ["frontend/src/app/customers/page.tsx", "frontend/src/app/customers/**/*.ts", "frontend/src/app/customers/**/*.tsx"]]

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
Missing input validation for customer form fields

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
In `frontend/src/app/customers/page.tsx`, the `CustomerForm` component (lines 182-315) does not validate input fields beyond basic HTML `required` attributes. Fields like `account_no`, `name`, `email`, `phone`, and `branch` are not sanitized or validated on the client side. This could allow users to submit malicious data (e.g., XSS payloads, SQL injection attempts) that would be sent directly to the backend API. While backend validation is expected, client-side validation is a critical first line of defense and improves user experience by providing immediate feedback.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. Add client-side validation for all form fields in CustomerForm. Validate email format, phone number format, required field lengths, and sanitize input to prevent XSS.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 3
  id: 6ec6ac9a-3418-48bc-a124-46ca50b1a03d
  عنوان اصلی: جلوگیری از نشت اطلاعات permission در خطاهای API
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/integration/test_auth_pipeline.py::test_no_permission_leak_in_errors", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]

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
[منطق] نشت اطلاعات permission در خطاهای API

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در مستندات frontend (login/page.tsx) اشاره به 'Error toast messages for various failure scenarios' شده است. اگر خطاهای API شامل جزئیات permission (مثلاً 'شما دسترسی ادمین ندارید') باشد، مهاجم می‌تواند از این پیام‌ها برای نقشه‌برداری از ساختار مجوزها استفاده کند.

## 💥 پیامد (impact)
اطلاعات مربوط به permission (مانند نقش‌ها، سطوح دسترسی) به کاربران نهایی نشت می‌کند و امکان حملات brute-force یا privilege escalation را فراهم می‌کند.

## 🛠 پیشنهاد رفع اولیه
تمام پیام‌های خطای مربوط به permission را به یک پیام عمومی مانند 'دسترسی غیرمجاز' تبدیل کنید. جزئیات خطا فقط در لاگ‌های سرور ثبت شود.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
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
  - شناسایی و مستندسازی ناسازگاری منطقی در pipeline auth — شناسایی و مستندسازی کامل ناسازگاری منطقی در pipeline auth
  - اصلاح backend API برای بازگرداندن پیام خطای عمومی به جای جزئیات permission — اصلاح backend API برای بازگرداندن پیام خطای عمومی
  - به‌روزرسانی frontend برای نمایش پیام خطای عمومی و حذف جزئیات permission — به‌روزرسانی frontend برای نمایش پیام خطای عمومی

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 3b6da420-9914-4d33-aaa8-3d169dc50e69, f7c14bb3-904f-4da1-b5a0-e8691ee049a4, 6ec6ac9a-3418-48bc-a124-46ca50b1a03d`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. outcome target به‌صورت measurable بازنویسی شد _(verify: manual_only)_
2. کد تغییر کرد تا outcome target محقق شود _(verify: static)_
3. test E2E که outcome را اندازه می‌گیرد عبور می‌کند _(verify: backend_test)_
4. metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد _(verify: static)_
5. اعمال تغییر بدون شکستن تست‌های موجود _(verify: backend_test)_
6. linter بدون warning عبور می‌کند _(verify: static)_
7. type-check موفق است _(verify: static)_
8. هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد _(verify: manual_only)_
9. ground truth تعیین شد و طرف دیگر align شد _(verify: manual_only)_
10. integration test برای pipeline `auth` بدون شکست عبور می‌کند _(verify: backend_test)_
11. PR description توضیح می‌دهد چرا این تصمیم گرفته شد _(verify: manual_only)_

## Task Steps

### Step 1: بررسی اولیه خودکار repo برای وجود تست‌های امنیتی
**Status:** `pending` (0%)
**Scope:** این مرحله شامل جستجوی grep برای یافتن فایل‌های تست موجود (tests/test_security.py)، توابع hash_password، create_access_token، verify_token و هرگونه تست unit یا integration مرتبط است. خارج از این مرحله: ایجاد یا تغییر هیچ کدی انجام نمی‌شود. نکته حیاتی: این مرحله صرفاً برای تشخیص وضعیت فعلی است و مبنای تصمیم‌گیری برای مراحل بعدی خواهد بود.
**Excerpt:**
```
♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
```

### Step 2: بازنویسی outcome target به صورت measurable برای تست‌های امنیتی
**Status:** `pending` (0%)
**Scope:** این مرحله شامل بازنویسی هدف (outcome target) از حالت کیفی به حالت کمی و قابل اندازه‌گیری است. مثال: 'پس از افزودن تست‌های امنیتی، ۱۰۰٪ سناریوهای احراز هویت (شامل توکن‌های منقضی، رمز عبور اشتباه، حملات brute force) باید پوشش داده شود'. خارج از این مرحله: تغییر کد یا نوشتن تست. نکته حیاتی: این هدف باید در فایل تسک یا مستندات مرتبط ثبت شود.
**Excerpt:**
```
## 🎯 هدف مطلوب (outcome target)
پس از افزودن تست‌های امنیتی، ۱۰۰٪ سناریوهای احراز هویت (شامل توکن‌های منقضی، رمز عبور اشتباه، حملات brute force) باید پوشش داده شود

- [ ] outcome target به‌صورت measurable بازنویسی شد
```

### Step 3: نوشتن تست‌های unit برای تابع hash_password با پوشش edge cases
**Status:** `pending` (0%)
**Scope:** این مرحله شامل نوشتن تست‌های unit برای تابع hash_password در فایل tests/test_security.py است. edge cases شامل: رمز عبور تکراری (تأیید اینکه hashهای متفاوت تولید می‌شوند)، رمز عبور خالی، رمز عبور با کاراکترهای خاص (مانند <script>، SQL injection payloads)، و شبیه‌سازی race condition (فراخوانی همزمان تابع). خارج از این مرحله: تست‌های integration یا E2E. نکته حیاتی: تست‌ها باید با pytest و با استفاده از parametrize نوشته شوند.
— [merged] این مرحله شامل نوشتن تست‌های unit برای تابع create_access_token در فایل tests/test_security.py است. edge cases شامل: ایجاد توکن با payload خالی، ایجاد توکن با payload حاوی داده‌های حساس، و بررسی صحت ساختار JWT. خارج از این مرحله: تست‌های integration یا E2E. نکته حیاتی: تست‌ها باید با pytest و با استفاده از parametrize نوشته شوند.
— [merged] این مرحله شامل نوشتن تست‌های unit برای تابع verify_token در فایل tests/test_security.py است. edge cases شامل: توکن معتبر، توکن منقضی، توکن با signature نامعتبر، توکن با payload دستکاری‌شده، و توکن خالی. خارج از این مرحله: تست‌های integration یا E2E. نکته حیاتی: تست‌ها باید با pytest و با استفاده از parametrize نوشته شوند.
**Excerpt:**
```
- افزودن تست‌های unit برای تابع hash_password با پوشش edge cases — نوشتن تست‌های unit برای hash_password با پوشش edge cases (رمز عبور تکراری، خالی، کاراکترهای خاص، race condition)

- [ ] کد تغییر کرد تا outcome target محقق شود [verify_method=static] [verify_plan={"grep_patterns": ["def test_hash_password", "def test_create_access_token", "def test_verify_token", "pytest.mark.parametrize", "jwt.encode", "jwt.decode"], "files_hint": ["tests/test_security.py"]}]
```

### Step 4: نوشتن تست‌های integration برای سناریوی توکن منقضی
**Status:** `pending` (0%)
**Scope:** این مرحله شامل نوشتن تست‌های integration در فایل tests/integration/test_auth_pipeline.py برای سناریوی توکن منقضی است. این تست باید یک توکن با تاریخ انقضای گذشته ایجاد کند و سپس سعی کند با آن به یک endpoint محافظت‌شده دسترسی پیدا کند. خارج از این مرحله: تست‌های unit یا E2E. نکته حیاتی: تست باید از طریق API واقعی (HTTP client) اجرا شود.
**Excerpt:**
```
- افزودن تست‌های integration برای سناریوهای احراز هویت کامل — نوشتن تست‌های integration برای سناریوهای احراز هویت کامل (توکن منقضی، رمز عبور اشتباه، brute force، JWT نامعتبر)
```

### Step 5: نوشتن تست‌های integration برای سناریوی رمز عبور اشتباه
**Status:** `pending` (0%)
**Scope:** این مرحله شامل نوشتن تست‌های integration در فایل tests/integration/test_auth_pipeline.py برای سناریوی رمز عبور اشتباه است. این تست باید با یک نام کاربری معتبر و رمز عبور اشتباه به endpoint لاگین درخواست دهد. خارج از این مرحله: تست‌های unit یا E2E. نکته حیاتی: تست باید از طریق API واقعی (HTTP client) اجرا شود.
**Excerpt:**
```
- افزودن تست‌های integration برای سناریوهای احراز هویت کامل — نوشتن تست‌های integration برای سناریوهای احراز هویت کامل (توکن منقضی، رمز عبور اشتباه، brute force، JWT نامعتبر)
```

### Step 6: نوشتن تست‌های integration برای سناریوی brute force
**Status:** `pending` (0%)
**Scope:** این مرحله شامل نوشتن تست‌های integration در فایل tests/integration/test_auth_pipeline.py برای سناریوی brute force است. این تست باید چندین تلاش ناموفق برای لاگین (با رمز عبور اشتباه) انجام دهد و سپس بررسی کند که آیا سیستم پس از تعداد مشخصی تلاش، درخواست‌ها را مسدود می‌کند یا تأخیر ایجاد می‌کند. خارج از این مرحله: تست‌های unit یا E2E. نکته حیاتی: تست باید از طریق API واقعی (HTTP client) اجرا شود.
**Excerpt:**
```
- افزودن تست‌های integration برای سناریوهای احراز هویت کامل — نوشتن تست‌های integration برای سناریوهای احراز هویت کامل (توکن منقضی، رمز عبور اشتباه، brute force، JWT نامعتبر)
```

### Step 7: نوشتن تست‌های integration برای سناریوی JWT نامعتبر
**Status:** `pending` (0%)
**Scope:** این مرحله شامل نوشتن تست‌های integration در فایل tests/integration/test_auth_pipeline.py برای سناریوی JWT نامعتبر است. این تست باید یک توکن JWT با signature نامعتبر (مثلاً با کلید متفاوت امضا شده) ایجاد کند و سپس سعی کند با آن به یک endpoint محافظت‌شده دسترسی پیدا کند. خارج از این مرحله: تست‌های unit یا E2E. نکته حیاتی: تست باید از طریق API واقعی (HTTP client) اجرا شود.
**Excerpt:**
```
- افزودن تست‌های integration برای سناریوهای احراز هویت کامل — نوشتن تست‌های integration برای سناریوهای احراز هویت کامل (توکن منقضی، رمز عبور اشتباه، brute force، JWT نامعتبر)
```

### Step 8: افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن metric و log به فایل‌های backend/app/security.py و backend/app/api/auth.py است. metric باید نرخ موفقیت (success rate) احراز هویت را اندازه‌گیری کند (مثلاً با استفاده از Prometheus metrics). log باید شامل logger.info یا logger.warning برای رویدادهای مختلف احراز هویت (موفق، ناموفق، توکن منقضی) باشد. خارج از این مرحله: تغییر در frontend. نکته حیاتی: metric باید در production قابل تشخیص باشد.
**Excerpt:**
```
- افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production — افزودن metric/log برای تشخیص نرخ موفقیت احراز هویت در production

- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=static] [verify_plan={"grep_patterns": ["logger.info", "logger.warning", "metrics.inc", "metrics.observe"], "files_hint": ["backend/app/security.py", "backend/app/api/auth.py"]}]
```

### Step 9: اجرای تست‌ها و linter برای اطمینان از عدم شکست
**Status:** `pending` (0%)
**Scope:** این مرحله شامل اجرای تمام تست‌های موجود (pytest) و linter (مانند flake8 یا pylint) برای اطمینان از اینکه تغییرات ایجاد شده باعث شکست هیچ تستی یا ایجاد warning جدید نشده است. خارج از این مرحله: تغییر کد. نکته حیاتی: این مرحله باید پس از تمام تغییرات کد انجام شود.
— [merged] این مرحله شامل اجرای تمام تست‌های موجود (pytest و npm run test) و linter (npm run lint) برای اطمینان از اینکه تغییرات ایجاد شده در frontend باعث شکست هیچ تستی یا ایجاد warning جدید نشده است. خارج از این مرحله: تغییر کد. نکته حیاتی: این مرحله باید پس از تمام تغییرات کد در frontend انجام شود.
**Excerpt:**
```
- اجرای تست‌ها و linter برای اطمینان از عدم شکست — اجرای تست‌ها و linter برای اطمینان از عدم شکست

- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)
```

### Step 10: بررسی اولیه خودکار repo برای وجود اعتبارسنجی فرم مشتری
**Status:** `pending` (0%)
**Scope:** این مرحله شامل جستجوی grep برای یافتن فایل frontend/src/app/customers/page.tsx و بررسی وجود هرگونه اعتبارسنجی سمت کلاینت برای فیلدهای فرم (account_no, name, email, phone, branch) است. خارج از این مرحله: ایجاد یا تغییر هیچ کدی انجام نمی‌شود. نکته حیاتی: این مرحله صرفاً برای تشخیص وضعیت فعلی است و مبنای تصمیم‌گیری برای مراحل بعدی خواهد بود.
**Excerpt:**
```
♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
```

### Step 11: افزودن اعتبارسنجی سمت کلاینت برای فیلد account_no در فرم مشتری
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن اعتبارسنجی سمت کلاینت برای فیلد account_no در کامپوننت CustomerForm در فایل frontend/src/app/customers/page.tsx است. اعتبارسنجی باید شامل: بررسی اینکه فیلد خالی نباشد، طول آن در محدوده مشخصی باشد (مثلاً ۱۰-۲۰ کاراکتر)، و فقط شامل اعداد باشد. خارج از این مرحله: اعتبارسنجی سایر فیلدها. نکته حیاتی: اعتبارسنجی باید با استفاده از توابع JavaScript/TypeScript خالص و بدون وابستگی به کتابخانه‌های خارجی انجام شود.
— [merged] این مرحله شامل افزودن اعتبارسنجی سمت کلاینت برای فیلد name در کامپوننت CustomerForm در فایل frontend/src/app/customers/page.tsx است. اعتبارسنجی باید شامل: بررسی اینکه فیلد خالی نباشد، طول آن در محدوده مشخصی باشد (مثلاً ۲-۱۰۰ کاراکتر)، و فقط شامل حروف و فاصله باشد (بدون اعداد یا کاراکترهای خاص). خارج از این مرحله: اعتبارسنجی سایر فیلدها. نکته حیاتی: اعتبارسنجی باید با استفاده از توابع JavaScript/TypeScript خالص انجام شود.
— [merged] این مرحله شامل افزودن اعتبارسنجی سمت کلاینت برای فیلد email در کامپوننت CustomerForm در فایل frontend/src/app/customers/page.tsx است. اعتبارسنجی باید شامل: بررسی فرمت ایمیل با استفاده از یک regex ساده (مانند test@example.com)، بررسی اینکه فیلد خالی نباشد، و sanitize کردن ورودی برای جلوگیری از XSS. خارج از این مرحله: اعتبارسنجی سایر فیلدها. نکته حیاتی: اعتبارسنجی باید با استفاده از توابع JavaScript/TypeScript خالص انجام شود.
— [merged] این مرحله شامل افزودن اعتبارسنجی سمت کلاینت برای فیلد phone در کامپوننت CustomerForm در فایل frontend/src/app/customers/page.tsx است. اعتبارسنجی باید شامل: بررسی فرمت شماره تلفن (مثلاً ۱۱ رقمی و شروع با ۰۹)، بررسی اینکه فیلد خالی نباشد، و sanitize کردن ورودی برای جلوگیری از XSS. خارج از این مرحله: اعتبارسنجی سایر فیلدها. نکته حیاتی: اعتبارسنجی باید با استفاده از توابع JavaScript/TypeScript خالص انجام شود.
— [merged] این مرحله شامل افزودن اعتبارسنجی سمت کلاینت برای فیلد branch در کامپوننت CustomerForm در فایل frontend/src/app/customers/page.tsx است. اعتبارسنجی باید شامل: بررسی اینکه فیلد خالی نباشد، طول آن در محدوده مشخصی باشد (مثلاً ۲-۵۰ کاراکتر)، و sanitize کردن ورودی برای جلوگیری از XSS. خارج از این مرحله: اعتبارسنجی سایر فیلدها. نکته حیاتی: اعتبارسنجی باید با استفاده از توابع JavaScript/TypeScript خالص انجام شود.
**Excerpt:**
```
1. Add client-side validation for all form fields in CustomerForm. Validate email format, phone number format, required field lengths, and sanitize input to prevent XSS.
```

### Step 12: شناسایی و مستندسازی ناسازگاری منطقی در pipeline auth
**Status:** `pending` (0%)
**Scope:** این مرحله شامل شناسایی کامل ناسازگاری منطقی در pipeline auth است. باید دو طرف ناسازگاری (frontend login/page.tsx و backend API) را بخوانیم و فرض‌های هر کدام را لیست کنیم. سپس ground truth را تعیین کرده و مستند کنیم. خارج از این مرحله: تغییر کد. نکته حیاتی: این مرحله صرفاً برای تحلیل و مستندسازی است.
**Excerpt:**
```
- شناسایی و مستندسازی ناسازگاری منطقی در pipeline auth — شناسایی و مستندسازی کامل ناسازگاری منطقی در pipeline auth

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
- [ ] ground truth تعیین شد و طرف دیگر align شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
```

### Step 13: اصلاح backend API برای بازگرداندن پیام خطای عمومی به جای جزئیات permission
**Status:** `pending` (0%)
**Scope:** این مرحله شامل اصلاح backend API (احتمالاً در فایل backend/app/api/auth.py) است تا به جای بازگرداندن پیام‌های خطای حاوی جزئیات permission (مانند 'شما دسترسی ادمین ندارید')، یک پیام خطای عمومی مانند 'دسترسی غیرمجاز' بازگرداند. جزئیات خطا باید فقط در لاگ‌های سرور ثبت شود. خارج از این مرحله: تغییر frontend. نکته حیاتی: این تغییر باید بدون شکستن تست‌های موجود انجام شود.
**Excerpt:**
```
- اصلاح backend API برای بازگرداندن پیام خطای عمومی به جای جزئیات permission — اصلاح backend API برای بازگرداندن پیام خطای عمومی

## 🛠 پیشنهاد رفع اولیه
تمام پیام‌های خطای مربوط به permission را به یک پیام عمومی مانند 'دسترسی غیرمجاز' تبدیل کنید. جزئیات خطا فقط در لاگ‌های سرور ثبت شود.
```

### Step 14: به‌روزرسانی frontend برای نمایش پیام خطای عمومی و حذف جزئیات permission
**Status:** `pending` (0%)
**Scope:** این مرحله شامل به‌روزرسانی frontend (احتمالاً در فایل frontend/src/app/customers/page.tsx یا login/page.tsx) است تا به جای نمایش جزئیات permission از خطاهای API، پیام خطای عمومی را نمایش دهد. همچنین باید هرگونه ارجاع به جزئیات permission در frontend حذف شود. خارج از این مرحله: تغییر backend. نکته حیاتی: این تغییر باید با backend هماهنگ باشد.
**Excerpt:**
```
- به‌روزرسانی frontend برای نمایش پیام خطای عمومی و حذف جزئیات permission — به‌روزرسانی frontend برای نمایش پیام خطای عمومی

## 💥 پیامد (impact)
اطلاعات مربوط به permission (مانند نقش‌ها، سطوح دسترسی) به کاربران نهایی نشت می‌کند و امکان حملات brute-force یا privilege escalation را فراهم می‌کند.
```

### Step 15: نوشتن integration test برای جلوگیری از نشت permission در خطاهای API
**Status:** `pending` (0%)
**Scope:** این مرحله شامل نوشتن یک integration test در فایل tests/integration/test_auth_pipeline.py با نام test_no_permission_leak_in_errors است. این تست باید بررسی کند که هیچ خطای API حاوی جزئیات permission (مانند 'admin', 'user', 'role') نیست و همه خطاها به یک پیام عمومی تبدیل شده‌اند. خارج از این مرحله: تست‌های unit یا E2E. نکته حیاتی: تست باید از طریق API واقعی (HTTP client) اجرا شود.
**Excerpt:**
```
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/integration/test_auth_pipeline.py::test_no_permission_leak_in_errors", "timeout_seconds": 60}]

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.
```
