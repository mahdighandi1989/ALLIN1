---
task_id: task_e92cd1d0c4b4
title: پاکسازی اسکریپت‌های Inspector Bridge و وابستگی‌های فرانت‌اند
type: other
priority: critical
execution_priority: 1200
status: pending
external_status: done
verification_status: applied_externally_pending_verify
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:12:35.442679+00:00'
updated_at: '2026-06-04T23:57:28.977165+00:00'
tags:
- consolidated
- post_verify_merge
---

# پاکسازی اسکریپت‌های Inspector Bridge و وابستگی‌های فرانت‌اند

## Raw Idea

🧬 این یک تسک تلفیقی است — از 3 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به مسائل مربوط به پیکربندی، ساخت و پاکسازی کد در فرانت‌اند می‌پردازند. شامل پیکربندی WebSocket، حذف کدهای Inspector Bridge از خروجی‌های HTML و همگام‌سازی فایل‌های مدیریت وابستگی (package.json و package-lock.json) است.
🎯 theme: پیکربندی و پاکسازی فرانت‌اند
💎 estimated_difficulty: small

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 3
  id: 2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a
  عنوان اصلی: پیکربندی WebSocket URL و توکن پروژه
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/next.config.js, frontend/out/dashboard/index.html, frontend/src/app/InspectorBridge.tsx

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["no-warning", "lint.*pass"], "files_hint": ["frontend/"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["type-check.*success", "tsc.*exit.*0"], "files_hint": ["frontend/"]}]

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
WebSocket URL هاردکد شده با توکن پروژه در فایل‌های استاتیک فرانت‌اند

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/out/dashboard/index.html:2-400` — `Inspector Bridge Script` — این اسکریپت در تمام صفحات استاتیک تزریق شده است
  ```
  <!-- Inspector Bridge Script - Auto-injected -->
  <script>
  (function() {
    const WS_URL = 'wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1';
    ...
    window.addEventListener('click', function(e) {
      sendToInspector('click', {...});
    }, true);
  })();
  </script>
  ```
- `frontend/src/app/InspectorBridge.tsx:1-50` — `InspectorBridge component` — فایل منبع احتمالی تزریق
  ```tsx
  // این کامپوننت احتمالاً اسکریپت bridge را تزریق می‌کند
  ```
- `frontend/next.config.js:1-30` — `next.config.js` — پیکربندی Next.js که ممکن است شامل پلاگین تزریق باشد
  ```jsx
  // احتمالاً پلاگین یا rewrites برای تزریق اسکریپت
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 Static Export + FastAPI Static Files

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/out/index.html` (سطر 2) — همین اسکریپت در صفحه اصلی
- `frontend/out/customers/index.html` (سطر 2) — همین اسکریپت در صفحه مشتریان
- `frontend/out/facilities/index.html` (سطر 2) — همین اسکریپت در صفحه تسهیلات
- `frontend/out/login/index.html` (سطر 2) — همین اسکریپت در صفحه ورود
- `backend/static/dashboard/index.html` (سطر 2) — همین اسکریپت در نسخه استاتیک بک‌اند

## 🌐 نقشهٔ وابستگی‌ها
این اسکریپت در تمام 10+ فایل HTML استاتیک تزریق شده و تمام رویدادهای کاربر را به یک سرور خارجی ارسال می‌کند.

## 🔍 Context و وضعیت فعلی
در تمام فایل‌های HTML استاتیک خروجی (frontend/out/*/index.html و backend/static/*/index.html) یک WebSocket URL هاردکد شده با شناسه پروژه وجود دارد: 'wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1'. این URL حاوی شناسه منحصربه‌فرد پروژه (gh_mahdighandi1989_allin1) است که می‌تواند برای شناسایی و هدف‌گیری پروژه استفاده شود. همچنین این اسکریپت تمام رویدادهای کاربر (کلیک، اسکرول، تایپ، خطاها) را به یک سرور خارجی ارسال می‌کند که نقض جدی حریم خصوصی و امنیت است.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. حذف کامل اسکریپت Inspector Bridge از تمام فایل‌های HTML استاتیک و پیکربندی build فرانت‌اند برای عدم تزریق خودکار این اسکریپت. همچنین بررسی کنید که این اسکریپت از کجا به build تزریق می‌شود (احتمالاً از InspectorBridge.tsx یا یک پلاگین next.config.js).

## 💡 نمونه‌های قبل/بعد
**حذف اسکریپت از HTML**

_قبل:_
```
<!-- Inspector Bridge Script - Auto-injected -->
<script>
...
</script>
```

_بعد:_
```
<!-- اسک
```

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
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 3
  id: 6079265b-4be3-4b4f-87b3-65bdbe250e39
  عنوان اصلی: حذف کد Inspector Bridge از HTMLهای خروجی
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: frontend/out/dashboard/index.html

📋 acceptance_criteria کامل:
  - هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس [verify_method=static] [verify_plan={"grep_patterns": ["Inspector Bridge", "WebSocket", "MutationObserver", "window.addEventListener"], "files_hint": ["frontend/out/", "backend/static/"]}]

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
کد تکراری و حجیم Inspector Bridge در تمام فایل‌های HTML خروجی فرانت‌اند

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/out/dashboard/index.html:2-400` — `Inspector Bridge Script` — این اسکریپت در تمام فایل‌های frontend/out/ و backend/static/ تکرار شده است
  ```
  <!-- Inspector Bridge Script - Auto-injected -->
  <script>
  (function() {
    console.log('🌉 Inspector Bridge: Script starting...');
    ...
    // 300+ lines of code
  })();
  </script>
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 Static Export + FastAPI Static Files

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/out/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/customers/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/facilities/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/login/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/404/index.html` (سطر 2) — همان اسکریپت تکراری
- `backend/static/dashboard/index.html` (سطر 2) — نسخه دوم اسکریپت با document.addEventListener
- `backend/static/customers/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/facilities/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/login/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/404/index.html` (سطر 2) — نسخه دوم اسکریپت

## 🌐 نقشهٔ وابستگی‌ها
این اسکریپت در 12 فایل HTML تکراری شده است و هیچ وابستگی به کد اصلی پروژه ندارد.

## 🔍 Context و وضعیت فعلی
اسکریپت Inspector Bridge (بیش از 300 خط) به صورت دستی و تکراری در تمام فایل‌های HTML خروجی استاتیک فرانت‌اند (frontend/out/ و backend/static/) تزریق شده است. این اسکریپت شامل WebSocket connection، event listeners، error handling، console interception و MutationObserver است. این حجم عظیم از dead code در خروجی نهایی باعث افزایش حجم فایل‌ها، کاهش performance و ایجاد noise در لاگ‌ها می‌شود. همچنین دو نسخه متفاوت از این اسکریپت وجود دارد: یکی در frontend/out/ (با window.addEventListener) و دیگری در backend/static/ (با document.addEventListener).

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. حذف کامل اسکریپت Inspector Bridge از تمام فایل‌های HTML خروجی. این اسکریپت متعلق به محیط توسعه و دیباگ است و نباید در build نهایی حضور داشته باشد. برای محیط توسعه، از یک اسکریپت خارجی (external script) که در next.config.js یا middleware بارگذاری می‌شود استفاده شود.

## 💡 نمونه‌های قبل/بعد
**حذف اسکریپت از فایل HTML**

_قبل:_
```
<!-- Inspector Bridge Script - Auto-injected -->
<script>
(function() {
  // 300+ lines
})();
</script>
```

_بعد:_
```
<!-- اسکریپت حذف شد -->
```

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
- نوع: refactor
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 3
  id: 1de3634f-33f0-429a-87a8-278171a2dd75
  عنوان اصلی: همگام‌سازی package.json و package-lock.json
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/package.json, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - صفحه داشبورد بدون خطای runtime بارگذاری شود. [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_loaded_without_errors"}]
  - دستور `npm install` بدون خطا اجرا شود. [verify_method=backend_test] [verify_plan={"test_node": "tests/frontend/test_npm_install_success.py::test_npm_install_runs_without_errors", "timeout_seconds": 120}]
  - فایل `package-lock.json` حاوی وابستگی `sonner` باشد. [verify_method=static] [verify_plan={"grep_patterns": ["\"sonner\":"], "files_hint": ["frontend/package-lock.json"]}]

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
عدم تطابق نسخه‌های وابستگی‌های فرانت‌اند بین package.json و package-lock.json

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/package.json:14-20` — `dependencies` — وابستگی `sonner` در این لیست وجود ندارد.
  ```json
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "axios": "1.6.5",
    "lucide-react": "0.312.0",
    "react-hot-toast": "2.4.1"
  }
  ```
- `frontend/src/app/dashboard/page.tsx:7` — `import` — این import به یک وابستگی نصب‌نشده اشاره دارد.
  ```tsx
  import { toast } from 'sonner';
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 + React 18 + npm

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/package-lock.json` (سطر 1) — فایل lock که باید حاوی وابستگی `sonner` باشد.
- `frontend/src/app/dashboard/page.tsx` (سطر 7) — فایلی که از `sonner` استفاده می‌کند.

## 🌐 نقشهٔ وابستگی‌ها
این مشکل بر روی صفحه داشبورد تأثیر می‌گذارد و باعث خطای runtime در زمان بارگذاری آن می‌شود.

## 🔍 Context و وضعیت فعلی
در فایل package.json، وابستگی `react-hot-toast` با نسخه `2.4.1` تعریف شده است، اما در فایل package-lock.json این وابستگی وجود ندارد. همچنین، وابستگی `sonner` که در فایل `frontend/src/app/dashboard/page.tsx` (خط 7) import شده است، در هیچکدام از فایل‌های package.json و package-lock.json تعریف نشده است. این ناسازگاری باعث خطای runtime در زمان اجرای فرانت‌اند می‌شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه داشبورد بدون خطای runtime بارگذاری شود.
- [ ] دستور `npm install` بدون خطا اجرا شود.
- [ ] فایل `package-lock.json` حاوی وابستگی `sonner` باشد.
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. وابستگی `sonner` را به `dependencies` در `frontend/package.json` اضافه کنید. 2. دستور `npm install` را اجرا کنید تا `package-lock.json` به‌روزرسانی شود. 3. در صورت عدم نیاز به `react-hot-toast`، آن را از `dependencies` حذف کنید.

## 💡 نمونه‌های قبل/بعد
**اصلاح package.json**

_قبل:_
```
"react-hot-toast": "2.4.1"
```

_بعد:_
```
"react-hot-toast": "2.4.1",
"sonner": "^1.4.0"
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm install`
- `cd frontend && npm run build`

## ⚠️ ریسک‌ها و موارد احتیاط
کم

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a, 6079265b-4be3-4b4f-87b3-65bdbe250e39, 1de3634f-33f0-429a-87a8-278171a2dd75`
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
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به مسائل مربوط به پیکربندی، ساخت و پاکسازی کد در فرانت‌اند می‌پردازند. شامل پیکربندی WebSocket، حذف کدهای Inspector Bridge از خروجی‌های HTML و همگام‌سازی فایل‌های مدیریت وابستگی (package.json و package-lock.json) است.
🎯 theme: پیکربندی و پاکسازی فرانت‌اند
💎 estimated_difficulty: small

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 3
  id: 2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a
  عنوان اصلی: پیکربندی WebSocket URL و توکن پروژه
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/next.config.js, frontend/out/dashboard/index.html, frontend/src/app/InspectorBridge.tsx

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["no-warning", "lint.*pass"], "files_hint": ["frontend/"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["type-check.*success", "tsc.*exit.*0"], "files_hint": ["frontend/"]}]

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
WebSocket URL هاردکد شده با توکن پروژه در فایل‌های استاتیک فرانت‌اند

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/out/dashboard/index.html:2-400` — `Inspector Bridge Script` — این اسکریپت در تمام صفحات استاتیک تزریق شده است
  ```
  <!-- Inspector Bridge Script - Auto-injected -->
  <script>
  (function() {
    const WS_URL = 'wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1';
    ...
    window.addEventListener('click', function(e) {
      sendToInspector('click', {...});
    }, true);
  })();
  </script>
  ```
- `frontend/src/app/InspectorBridge.tsx:1-50` — `InspectorBridge component` — فایل منبع احتمالی تزریق
  ```tsx
  // این کامپوننت احتمالاً اسکریپت bridge را تزریق می‌کند
  ```
- `frontend/next.config.js:1-30` — `next.config.js` — پیکربندی Next.js که ممکن است شامل پلاگین تزریق باشد
  ```jsx
  // احتمالاً پلاگین یا rewrites برای تزریق اسکریپت
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 Static Export + FastAPI Static Files

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/out/index.html` (سطر 2) — همین اسکریپت در صفحه اصلی
- `frontend/out/customers/index.html` (سطر 2) — همین اسکریپت در صفحه مشتریان
- `frontend/out/facilities/index.html` (سطر 2) — همین اسکریپت در صفحه تسهیلات
- `frontend/out/login/index.html` (سطر 2) — همین اسکریپت در صفحه ورود
- `backend/static/dashboard/index.html` (سطر 2) — همین اسکریپت در نسخه استاتیک بک‌اند

## 🌐 نقشهٔ وابستگی‌ها
این اسکریپت در تمام 10+ فایل HTML استاتیک تزریق شده و تمام رویدادهای کاربر را به یک سرور خارجی ارسال می‌کند.

## 🔍 Context و وضعیت فعلی
در تمام فایل‌های HTML استاتیک خروجی (frontend/out/*/index.html و backend/static/*/index.html) یک WebSocket URL هاردکد شده با شناسه پروژه وجود دارد: 'wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1'. این URL حاوی شناسه منحصربه‌فرد پروژه (gh_mahdighandi1989_allin1) است که می‌تواند برای شناسایی و هدف‌گیری پروژه استفاده شود. همچنین این اسکریپت تمام رویدادهای کاربر (کلیک، اسکرول، تایپ، خطاها) را به یک سرور خارجی ارسال می‌کند که نقض جدی حریم خصوصی و امنیت است.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. حذف کامل اسکریپت Inspector Bridge از تمام فایل‌های HTML استاتیک و پیکربندی build فرانت‌اند برای عدم تزریق خودکار این اسکریپت. همچنین بررسی کنید که این اسکریپت از کجا به build تزریق می‌شود (احتمالاً از InspectorBridge.tsx یا یک پلاگین next.config.js).

## 💡 نمونه‌های قبل/بعد
**حذف اسکریپت از HTML**

_قبل:_
```
<!-- Inspector Bridge Script - Auto-injected -->
<script>
...
</script>
```

_بعد:_
```
<!-- اسک
```

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
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 3
  id: 6079265b-4be3-4b4f-87b3-65bdbe250e39
  عنوان اصلی: حذف کد Inspector Bridge از HTMLهای خروجی
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: frontend/out/dashboard/index.html

📋 acceptance_criteria کامل:
  - هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس [verify_method=static] [verify_plan={"grep_patterns": ["Inspector Bridge", "WebSocket", "MutationObserver", "window.addEventListener"], "files_hint": ["frontend/out/", "backend/static/"]}]

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
کد تکراری و حجیم Inspector Bridge در تمام فایل‌های HTML خروجی فرانت‌اند

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/out/dashboard/index.html:2-400` — `Inspector Bridge Script` — این اسکریپت در تمام فایل‌های frontend/out/ و backend/static/ تکرار شده است
  ```
  <!-- Inspector Bridge Script - Auto-injected -->
  <script>
  (function() {
    console.log('🌉 Inspector Bridge: Script starting...');
    ...
    // 300+ lines of code
  })();
  </script>
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 Static Export + FastAPI Static Files

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/out/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/customers/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/facilities/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/login/index.html` (سطر 2) — همان اسکریپت تکراری
- `frontend/out/404/index.html` (سطر 2) — همان اسکریپت تکراری
- `backend/static/dashboard/index.html` (سطر 2) — نسخه دوم اسکریپت با document.addEventListener
- `backend/static/customers/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/facilities/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/login/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/index.html` (سطر 2) — نسخه دوم اسکریپت
- `backend/static/404/index.html` (سطر 2) — نسخه دوم اسکریپت

## 🌐 نقشهٔ وابستگی‌ها
این اسکریپت در 12 فایل HTML تکراری شده است و هیچ وابستگی به کد اصلی پروژه ندارد.

## 🔍 Context و وضعیت فعلی
اسکریپت Inspector Bridge (بیش از 300 خط) به صورت دستی و تکراری در تمام فایل‌های HTML خروجی استاتیک فرانت‌اند (frontend/out/ و backend/static/) تزریق شده است. این اسکریپت شامل WebSocket connection، event listeners، error handling، console interception و MutationObserver است. این حجم عظیم از dead code در خروجی نهایی باعث افزایش حجم فایل‌ها، کاهش performance و ایجاد noise در لاگ‌ها می‌شود. همچنین دو نسخه متفاوت از این اسکریپت وجود دارد: یکی در frontend/out/ (با window.addEventListener) و دیگری در backend/static/ (با document.addEventListener).

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. حذف کامل اسکریپت Inspector Bridge از تمام فایل‌های HTML خروجی. این اسکریپت متعلق به محیط توسعه و دیباگ است و نباید در build نهایی حضور داشته باشد. برای محیط توسعه، از یک اسکریپت خارجی (external script) که در next.config.js یا middleware بارگذاری می‌شود استفاده شود.

## 💡 نمونه‌های قبل/بعد
**حذف اسکریپت از فایل HTML**

_قبل:_
```
<!-- Inspector Bridge Script - Auto-injected -->
<script>
(function() {
  // 300+ lines
})();
</script>
```

_بعد:_
```
<!-- اسکریپت حذف شد -->
```

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
- نوع: refactor
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 3
  id: 1de3634f-33f0-429a-87a8-278171a2dd75
  عنوان اصلی: همگام‌سازی package.json و package-lock.json
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/package.json, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - صفحه داشبورد بدون خطای runtime بارگذاری شود. [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_loaded_without_errors"}]
  - دستور `npm install` بدون خطا اجرا شود. [verify_method=backend_test] [verify_plan={"test_node": "tests/frontend/test_npm_install_success.py::test_npm_install_runs_without_errors", "timeout_seconds": 120}]
  - فایل `package-lock.json` حاوی وابستگی `sonner` باشد. [verify_method=static] [verify_plan={"grep_patterns": ["\"sonner\":"], "files_hint": ["frontend/package-lock.json"]}]

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
عدم تطابق نسخه‌های وابستگی‌های فرانت‌اند بین package.json و package-lock.json

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/package.json:14-20` — `dependencies` — وابستگی `sonner` در این لیست وجود ندارد.
  ```json
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "axios": "1.6.5",
    "lucide-react": "0.312.0",
    "react-hot-toast": "2.4.1"
  }
  ```
- `frontend/src/app/dashboard/page.tsx:7` — `import` — این import به یک وابستگی نصب‌نشده اشاره دارد.
  ```tsx
  import { toast } from 'sonner';
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 + React 18 + npm

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/package-lock.json` (سطر 1) — فایل lock که باید حاوی وابستگی `sonner` باشد.
- `frontend/src/app/dashboard/page.tsx` (سطر 7) — فایلی که از `sonner` استفاده می‌کند.

## 🌐 نقشهٔ وابستگی‌ها
این مشکل بر روی صفحه داشبورد تأثیر می‌گذارد و باعث خطای runtime در زمان بارگذاری آن می‌شود.

## 🔍 Context و وضعیت فعلی
در فایل package.json، وابستگی `react-hot-toast` با نسخه `2.4.1` تعریف شده است، اما در فایل package-lock.json این وابستگی وجود ندارد. همچنین، وابستگی `sonner` که در فایل `frontend/src/app/dashboard/page.tsx` (خط 7) import شده است، در هیچکدام از فایل‌های package.json و package-lock.json تعریف نشده است. این ناسازگاری باعث خطای runtime در زمان اجرای فرانت‌اند می‌شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه داشبورد بدون خطای runtime بارگذاری شود.
- [ ] دستور `npm install` بدون خطا اجرا شود.
- [ ] فایل `package-lock.json` حاوی وابستگی `sonner` باشد.
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. وابستگی `sonner` را به `dependencies` در `frontend/package.json` اضافه کنید. 2. دستور `npm install` را اجرا کنید تا `package-lock.json` به‌روزرسانی شود. 3. در صورت عدم نیاز به `react-hot-toast`، آن را از `dependencies` حذف کنید.

## 💡 نمونه‌های قبل/بعد
**اصلاح package.json**

_قبل:_
```
"react-hot-toast": "2.4.1"
```

_بعد:_
```
"react-hot-toast": "2.4.1",
"sonner": "^1.4.0"
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm install`
- `cd frontend && npm run build`

## ⚠️ ریسک‌ها و موارد احتیاط
کم

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a, 6079265b-4be3-4b4f-87b3-65bdbe250e39, 1de3634f-33f0-429a-87a8-278171a2dd75`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. اعمال تغییر بدون شکستن تست‌های موجود _(verify: backend_test)_
2. linter بدون warning عبور می‌کند _(verify: static)_
3. type-check موفق است _(verify: static)_
4. هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس _(verify: static)_
5. صفحه داشبورد بدون خطای runtime بارگذاری شود. _(verify: ui_interaction)_
6. دستور `npm install` بدون خطا اجرا شود. _(verify: backend_test)_
7. فایل `package-lock.json` حاوی وابستگی `sonner` باشد. _(verify: static)_

## Task Steps

### Step 1: بررسی و حذف WebSocket URL هاردکد شده از فایل‌های HTML استاتیک (تسک 1 - بخش ⚠️ یادداشت مهم)
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی اولیه و حذف WebSocket URL هاردکد شده ('wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1') از تمام فایل‌های HTML استاتیک در frontend/out/ و backend/static/ است. خارج از این مرحله: تغییر در فایل‌های منبع (InspectorBridge.tsx, next.config.js) و اجرای تست‌ها. نکته حیاتی: قبل از هر تغییری، با grep/search بررسی کنید که آیا این اسکریپت قبلاً حذف شده است یا خیر.
**Excerpt:**
```
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
```

### Step 2: حذف کامل اسکریپت Inspector Bridge از تمام فایل‌های HTML استاتیک (تسک 1 - بخش 🎯 هدف)
**Status:** `done` (100%)
**Scope:** این مرحله شامل حذف کامل بلوک اسکریپت Inspector Bridge (شامل تگ <script> و محتوای آن) از تمام فایل‌های HTML استاتیک در frontend/out/ و backend/static/ است. خارج از این مرحله: تغییر در فایل‌های منبع (InspectorBridge.tsx, next.config.js) و اجرای تست‌ها. نکته حیاتی: اسکریپت با کامنت '<!-- Inspector Bridge Script - Auto-injected -->' شروع می‌شود و بیش از 300 خط کد دارد.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
WebSocket URL هاردکد شده با توکن پروژه در فایل‌های استاتیک فرانت‌اند

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/out/dashboard/index.html:2-400` — `Inspector Bridge Script` — این اسکریپت در تمام صفحات استاتیک تزریق شده است
  ```
  <!-- Inspector Bridge Script - Auto-injected -->
  <script>
  (function() {
    const WS_URL = 'wss://ai-creator-backend-q677.onrender.com/api/render/ws/bridge/gh_mahdighandi1989_allin1';
    ...
    window.addEventListener('click', function(e) {
      sendToInspector('click', {...});
    }, true);
  })();
  </script>
  ```
```

### Step 3: بررسی و حذف کد تزریق اسکریپت از InspectorBridge.tsx (تسک 1 - بخش ✅ معیار پذیرش)
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی فایل frontend/src/app/InspectorBridge.tsx و حذف یا غیرفعال کردن کدی است که اسکریپت Inspector Bridge را به خروجی HTML تزریق می‌کند. خارج از این مرحله: تغییر در next.config.js و حذف اسکریپت از فایل‌های HTML موجود. نکته حیاتی: اگر این کامپوننت فقط برای محیط توسعه استفاده می‌شود، آن را با شرط process.env.NODE_ENV محافظت کنید.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)
```

### Step 4: بررسی و حذف پلاگین تزریق اسکریپت از next.config.js (تسک 1 - بخش 💡 نمونه‌های قبل/بعد)
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی فایل frontend/next.config.js و حذف یا غیرفعال کردن هر پلاگین یا تنظیمی که باعث تزریق اسکریپت Inspector Bridge به خروجی HTML می‌شود. خارج از این مرحله: تغییر در InspectorBridge.tsx و حذف اسکریپت از فایل‌های HTML موجود. نکته حیاتی: اگر پلاگین تزریق برای محیط توسعه ضروری است، آن را با شرط محیطی محافظت کنید.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**حذف اسکریپت از HTML**

_قبل:_
```
<!-- Inspector Bridge Script - Auto-injected -->
<script>
...
</script>
```

_بعد:_
```
<!-- اسک
```
```

### Step 5: اجرای تست‌ها و اعتبارسنجی تغییرات (تسک 1 - بخش 🧪 دستورات اعتبارسنجی)
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای دستورات اعتبارسنجی (pytest, npm run build, npm run lint) برای اطمینان از عدم شکستن تست‌های موجود و عبور linter و type-check است. خارج از این مرحله: تغییر در کد. نکته حیاتی: اگر تستی fail شد، باید قبل از ادامه رفع شود.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.
```

### Step 6: بررسی و حذف اسکریپت Inspector Bridge از frontend/out/ (تسک 2 - بخش ⚠️ یادداشت مهم)
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی اولیه و حذف اسکریپت Inspector Bridge از تمام فایل‌های HTML در frontend/out/ است. خارج از این مرحله: تغییر در backend/static/ و فایل‌های منبع. نکته حیاتی: قبل از هر تغییری، با grep/search بررسی کنید که آیا این اسکریپت قبلاً حذف شده است یا خیر.
**Excerpt:**
```
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
```

### Step 7: حذف اسکریپت Inspector Bridge از تمام فایل‌های frontend/out/ (تسک 2 - بخش 🎯 هدف)
**Status:** `done` (100%)
**Scope:** این مرحله شامل حذف کامل بلوک اسکریپت Inspector Bridge از تمام فایل‌های HTML در frontend/out/ است. خارج از این مرحله: تغییر در backend/static/ و فایل‌های منبع. نکته حیاتی: اسکریپت با کامنت '<!-- Inspector Bridge Script - Auto-injected -->' شروع می‌شود و بیش از 300 خط کد دارد.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
کد تکراری و حجیم Inspector Bridge در تمام فایل‌های HTML خروجی فرانت‌اند

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/out/dashboard/index.html:2-400` — `Inspector Bridge Script` — این اسکریپت در تمام فایل‌های frontend/out/ و backend/static/ تکرار شده است
  ```
  <!-- Inspector Bridge Script - Auto-injected -->
  <script>
  (function() {
    console.log('🌉 Inspector Bridge: Script starting...');
    ...
    // 300+ lines of code
  })();
  </script>
  ```
```

### Step 8: بررسی و حذف اسکریپت Inspector Bridge از backend/static/ (تسک 2 - بخش ✅ معیار پذیرش)
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی و حذف اسکریپت Inspector Bridge از تمام فایل‌های HTML در backend/static/ است. خارج از این مرحله: تغییر در frontend/out/ و فایل‌های منبع. نکته حیاتی: نسخه اسکریپت در backend/static/ از document.addEventListener استفاده می‌کند در حالی که نسخه frontend/out/ از window.addEventListener استفاده می‌کند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)
```

### Step 9: اجرای تست‌ها و اعتبارسنجی تغییرات (تسک 2 - بخش 💡 نمونه‌های قبل/بعد)
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای دستورات اعتبارسنجی (pytest, npm run build, npm run lint) برای اطمینان از عدم شکستن تست‌های موجود و عبور linter و type-check است. خارج از این مرحله: تغییر در کد. نکته حیاتی: اگر تستی fail شد، باید قبل از ادامه رفع شود.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**حذف اسکریپت از فایل HTML**

_قبل:_
```
<!-- Inspector Bridge Script - Auto-injected -->
<script>
(function() {
  // 300+ lines
})();
</script>
```

_بعد:_
```
<!-- اسکریپت حذف شد -->
```
```

### Step 10: بررسی و حذف اسکریپت Inspector Bridge از backend/static/ (تسک 2 - بخش 🧪 دستورات اعتبارسنجی)
**Status:** `done` (100%)
**Scope:** این مرحله شامل حذف کامل بلوک اسکریپت Inspector Bridge از تمام فایل‌های HTML در backend/static/ است. خارج از این مرحله: تغییر در frontend/out/ و فایل‌های منبع. نکته حیاتی: نسخه اسکریپت در backend/static/ از document.addEventListener استفاده می‌کند در حالی که نسخه frontend/out/ از window.addEventListener استفاده می‌کند.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.
```

### Step 11: بررسی و اضافه کردن وابستگی sonner به package.json (تسک 3 - بخش ⚠️ یادداشت مهم)
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی اولیه و اضافه کردن وابستگی 'sonner' به بخش dependencies در فایل frontend/package.json است. خارج از این مرحله: اجرای npm install و به‌روزرسانی package-lock.json. نکته حیاتی: قبل از هر تغییری، بررسی کنید که آیا وابستگی sonner از قبل در package.json وجود دارد یا خیر.
**Excerpt:**
```
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
```

### Step 12: اضافه کردن وابستگی sonner به package.json (تسک 3 - بخش 🎯 هدف)
**Status:** `done` (100%)
**Scope:** این مرحله شامل اضافه کردن وابستگی 'sonner' با نسخه '^1.4.0' به بخش dependencies در فایل frontend/package.json است. خارج از این مرحله: اجرای npm install و به‌روزرسانی package-lock.json. نکته حیاتی: وابستگی 'react-hot-toast' ممکن است غیرضروری باشد و باید در مرحله بعد حذف شود.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
عدم تطابق نسخه‌های وابستگی‌های فرانت‌اند بین package.json و package-lock.json

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/package.json:14-20` — `dependencies` — وابستگی `sonner` در این لیست وجود ندارد.
  ```json
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "axios": "1.6.5",
    "lucide-react": "0.312.0",
    "react-hot-toast": "2.4.1"
  }
  ```
```

### Step 13: اجرای npm install برای به‌روزرسانی package-lock.json (تسک 3 - بخش ✅ معیار پذیرش)
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای دستور 'npm install' در دایرکتوری frontend برای نصب وابستگی sonner و به‌روزرسانی فایل package-lock.json است. خارج از این مرحله: تغییر در package.json. نکته حیاتی: اطمینان حاصل کنید که دستور npm install بدون خطا اجرا می‌شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه داشبورد بدون خطای runtime بارگذاری شود.
- [ ] دستور `npm install` بدون خطا اجرا شود.
- [ ] فایل `package-lock.json` حاوی وابستگی `sonner` باشد.
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)
```

### Step 14: حذف وابستگی غیرضروری react-hot-toast از package.json (تسک 3 - بخش 💡 نمونه‌های قبل/بعد)
**Status:** `done` (100%)
**Scope:** این مرحله شامل حذف وابستگی 'react-hot-toast' از بخش dependencies در فایل frontend/package.json است، در صورتی که دیگر در پروژه استفاده نمی‌شود. خارج از این مرحله: اجرای npm install و به‌روزرسانی package-lock.json. نکته حیاتی: قبل از حذف، بررسی کنید که آیا react-hot-toast در جای دیگری از پروژه استفاده می‌شود یا خیر.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**اصلاح package.json**

_قبل:_
```
"react-hot-toast": "2.4.1"
```

_بعد:_
```
"react-hot-toast": "2.4.1",
"sonner": "^1.4.0"
```
```

### Step 15: اجرای npm install مجدد برای به‌روزرسانی package-lock.json پس از حذف react-hot-toast (تسک 3 - بخش 🧪 دستورات اعتبارسنجی)
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای مجدد دستور 'npm install' در دایرکتوری frontend برای به‌روزرسانی فایل package-lock.json پس از حذف وابستگی react-hot-toast است. خارج از این مرحله: تغییر در package.json. نکته حیاتی: اطمینان حاصل کنید که دستور npm install بدون خطا اجرا می‌شود.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm install`
- `cd frontend && npm run build`

## ⚠️ ریسک‌ها و موارد احتیاط
کم
```

### Step 16: اجرای build فرانت‌اند برای اعتبارسنجی نهایی (تسک 3 - بخش ⚠️ ریسک‌ها و موارد احتیاط)
**Status:** `done` (100%)
**Scope:** این مرحله شامل اجرای دستور 'npm run build' در دایرکتوری frontend برای اطمینان از build موفق پروژه پس از تغییرات وابستگی‌ها است. خارج از این مرحله: تغییر در کد. نکته حیاتی: اگر build با خطا مواجه شد، باید قبل از ادامه رفع شود.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
کم

## 🔗 وابستگی‌های تسکی
_(مستقل)_
```

### Step 17: اجرای تست‌ها و اعتبارسنجی نهایی (تسک 3 - بخش 🏷 دسته‌بندی)
**Status:** `partial` (95%)
**Scope:** این مرحله شامل اجرای دستورات اعتبارسنجی (pytest, npm run test, npm run lint) برای اطمینان از عدم شکستن تست‌های موجود و عبور linter و type-check است. خارج از این مرحله: تغییر در کد. نکته حیاتی: اگر تستی fail شد، باید قبل از ادامه رفع شود.
**Excerpt:**
```
## 🏷 دسته‌بندی
- نوع: bug
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)
```

### Step 18: Commit نهایی و ثبت تغییرات با پیام واضح (تسک 3 - بخش 💡 نکات استاندارد)
**Status:** `done` (100%)
**Scope:** این مرحله شامل commit کردن تمام تغییرات با یک پیام واضح و جامع است که شامل merged-from با شناسه‌های تسک‌ها (2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a, 6079265b-4be3-4b4f-87b3-65bdbe250e39, 1de3634f-33f0-429a-87a8-278171a2dd75) و توضیح مختصری از تغییرات انجام شده است. خارج از این مرحله: تغییر در کد. نکته حیاتی: پیام commit باید شامل merged-from و توضیح تغییرات باشد.
**Excerpt:**
```
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a, 6079265b-4be3-4b4f-87b3-65bdbe250e39, 1de3634f-33f0-429a-87a8-278171a2dd75`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند
```
