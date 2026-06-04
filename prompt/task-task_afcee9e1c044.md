---
task_id: task_afcee9e1c044
title: رفع باگ‌ها و همگام‌سازی نمایش داده‌ها در داشبورد
type: other
priority: critical
execution_priority: 1100
status: pending
external_status: claimed
verification_status: partial
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:06:12.836115+00:00'
updated_at: '2026-06-04T21:30:44.324433+00:00'
tags:
- consolidated
- post_verify_merge
---

# رفع باگ‌ها و همگام‌سازی نمایش داده‌ها در داشبورد

## Raw Idea

🧬 این یک تسک تلفیقی است — از 5 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به طور مستقیم به مشکلات مربوط به نمایش داده‌ها در داشبورد، تطبیق قرارداد API بین بک‌اند و فرانت‌اند برای داده‌های آماری، رفع خطاهای 500 در حالت static build و مدیریت خطاهای مربوط به ستون‌های از دست رفته در داشبورد می‌پردازند. همچنین شامل رفع مشکلات کامپوننت‌های UI تعریف‌نشده در داشبورد است.
🎯 theme: نمایش داده‌های داشبورد
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 5
  id: 57db04f7-e3df-4b27-b5c7-c872e9ccf486
  عنوان اصلی: نمایش داده‌های داشبورد و صفحات مرتبط
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py

📋 acceptance_criteria کامل:
  - صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner) [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "wait_for", "selector": "[data-testid='dashboard-content']
  - در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "wait_for", "selector": "[data-testid='error-message']", ]
  - صفحات customers و facilities نیز داده‌ها را نمایش دهند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/customers"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "wait_for", "selector": "[data-testid='customers-content']

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
داشبورد فرانت‌اند در حالت loading گیر کرده و داده‌ها را نمایش نمی‌دهد

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/stats.py:1-50` — `dashboard_stats` — این endpoint احتمالاً dummy response برمی‌گرداند یا پیاده‌سازی نشده است
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.database import get_db
  
  router = APIRouter()
  
  @router.get('/dashboard')
  async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
      # TODO: implement
      return {'total_customers': 0, 'total_facilities': 0}
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 static export + FastAPI backend

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/src/app/dashboard/page.tsx` (سطر 34) — فرانت‌اند که این endpoint را صدا می‌زند و spinner را نمایش می‌دهد
- `backend/static/dashboard/index.html` (سطر 76) — build استاتیک که spinner را نشان می‌دهد
- `backend/static/customers/index.html` (سطر 82) — همین مشکل در صفحه customers
- `backend/static/facilities/index.html` (سطر 82) — همین مشکل در صفحه facilities
- `backend/app/main.py` — این فایل `stats.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
این باگ روی تمام صفحات اصلی (dashboard, customers, facilities) تأثیر می‌گذارد و تجربه کاربری را کاملاً مختل کرده است.

## 🔍 Context و وضعیت فعلی
صفحات dashboard، customers و facilities در build استاتیک (backend/static/) همگی در حالت loading بی‌نهایت (spinner) باقی می‌مانند. در backend/static/dashboard/index.html خط ۷۶-۸۴ یک div با کلاس 'animate-spin' و متن 'Loading dashboard data...' وجود دارد که هرگز پنهان نمی‌شود. این نشان می‌دهد که فراخوانی API (fetch('/api/stats/dashboard') در frontend/src/app/dashboard/page.tsx خط ۳۴) با خطا مواجه می‌شود یا داده‌ای برنمی‌گرداند. در build استاتیک، این فراخوانی‌ها در سمت کلاینت انجام می‌شوند و اگر بک‌اند در دسترس نباشد یا endpoint پاسخ ندهد، spinner باقی می‌ماند. همچنین در backend/static/customers/index.html و backend/static/facilities/index.html نیز spinner مشابهی دیده می‌شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner)
- [ ] در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود
- [ ] صفحات customers و facilities نیز داده‌ها را نمایش دهند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱. اطمینان حاصل کنید که endpoint /api/stats/dashboard در بک‌اند به درستی پیاده‌سازی شده و داده برمی‌گرداند. ۲. در فرانت‌اند، یک fallback UI برای حالت خطا یا empty state اضافه کنید تا کاربر spinner ابدی نبیند. ۳. خطای 500 که در backend/static/dashboard/index.html خط ۴۴-۴۸ (کد جاوااسکریپت) مدیریت شده را بررسی کنید.

## 💡 نمونه‌های قبل/بعد
**حالت فعلی (spinner ابدی)**

_قبل:_
```
<div class='animate-spin ...'></div><p>Loading dashboard data...</p>
```

_بعد:_
```
<div>داده‌ها نمایش داده می‌شوند یا پیام خطای مناسب
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl http://localhost:8000/api/stats/dashboard`
- `npm run build && npm start (بررسی build استاتیک)`

## ⚠️ ریسک‌ها و موارد احتیاط
نیاز به بررسی endpoint بک‌اند و احتمالاً اصلاح queryهای د

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 5
  id: ab4622a6-7eaa-4d03-bc4f-be7e6207628e
  عنوان اصلی: تطبیق contract داشبورد بک‌اند و فرانت‌اند
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 200, "required_fields": ["total_customers", "total_facilities", "active_facilities", "expiring_]
  - ستون amount در جدول facilities وجود دارد و NOT NULL است [verify_method=static] [verify_plan={"grep_patterns": ["amount.*NOT NULL", "amount.*nullable=False"], "files_hint": ["backend/app/models/facility.py", "docs/DATABASE_SCHEMA.md"]}]
  - dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "assert_visible", "selector": "[data-testid='dashboard-st]
  - تست واحد برای endpoint اضافه شود [verify_method=backend_test] [verify_plan={"test_node": "tests/test_stats.py::test_dashboard_endpoint", "timeout_seconds": 60}]

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
عدم تطابق contract بین endpoint /api/stats/dashboard و فرانت‌اند dashboard/page.tsx

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/stats.py:1-50` — `dashboard_stats` — این endpoint باید response ای مطابق با DashboardStats بدهد
  ```python
  # نیاز به بررسی کامل endpoint
  ```
- `frontend/src/app/dashboard/page.tsx:10-22` — `DashboardStats` — اینترفیس فرانت‌اند که backend باید با آن match کند
  ```tsx
  interface DashboardStats {
    total_customers: number;
    total_facilities: number;
    active_facilities: number;
    expiring_soon: number;
    monthly_revenue: number;
    recent_activities: Array<{...}>;
  }
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + SQLAlchemy + Next.js 14 App Router

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/models/facility.py` (سطر 1) — مدل facility که ستون amount را دارد
- `backend/app/schemas/stats.py` (سطر 1) — شاید schema response تعریف شده
- `backend/migrations/versions/002_add_missing_columns.py` (سطر 1) — مهاجرت برای اضافه کردن ستون‌های缺失
- `backend/app/main.py` — این فایل `stats.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
این endpoint توسط dashboard/page.tsx در فرانت‌اند استفاده می‌شود و وابسته به مدل‌های facility و customer است.

## 🔍 Context و وضعیت فعلی
فرانت‌اند dashboard/page.tsx (خطوط 10-22) یک interface DashboardStats تعریف کرده که شامل فیلدهای total_customers, total_facilities, active_facilities, expiring_soon, monthly_revenue, recent_activities است. اما endpoint /api/stats/dashboard در backend/app/routers/stats.py وجود دارد و مشخص نیست که دقیقاً چه response shape ای برمی‌گرداند. بررسی فایل‌های backend نشان می‌دهد که مدل facility ستون amount را دارد (طبق docs/DATABASE_SCHEMA.md) اما در مدل‌های backend/app/models/facility.py ممکن است این ستون وجود نداشته باشد یا type mismatch داشته باشد. این باعث خطای 500 در dashboard می‌شود که در خروجی static dashboard/index.html (خط 1) به صورت 'Loading dashboard data...' و اسپینر بی‌نهایت دیده می‌شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد
- [ ] ستون amount در جدول facilities وجود دارد و NOT NULL است
- [ ] dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند
- [ ] تست واحد برای endpoint اضافه شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. بررسی و تطبیق کامل response schema endpoint /api/stats/dashboard با interface DashboardStats در frontend. اطمینان از وجود ستون amount در مدل Facility و مهاجرت دیتابیس. اضافه کردن validation با Pydantic برای response.

## 💡 نمونه‌های قبل/بعد
**response shape**

_قبل:_
```
{"total_customers": 0, "error": "column amount does not exist"}
```

_بعد:_
```
{"total_customers": 592, "total_facilities": 150, "active_facilities": 120, "expiring_soon": 5, "monthly_revenue": 500000, "recent_activities": []}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl http://localhost:8000/api/stats/dashboard | jq .`
- `pytest backend/tests/test_facilities.py -k amount`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر در response ممکن است clientهای دیگر را بشکند

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی و تطبیق مدل Facility در backend/app/models/facility.py با ستون amount از DATABASE_SCHEMA.md
  - بررسی و تطبیق schema response در backend/app/schemas/stats.py با interface DashboardStats فرانت‌اند
  - بررسی و رفع مشکل static dashboard/index.html که اسپینر بی‌نهایت نشان می‌دهد
  - بررسی و به‌روزرسانی مهاجرت دیتابیس (migrations) برای اضافه کردن ستون‌های missing در facility
  - نوشتن تست‌های فرانت‌اند برای dashboard/page.tsx

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و اصلاح endpoint dashboard_stats در backend/app/routers/stats.py برای استفاده از schema جدید و بازگرداندن داده‌های صحیح — فیلدهای active_facilities, monthly_revenue, recent_activities در response backend وجود ندارند
  - بررسی و اصلاح فرانت‌اند dashboard/page.tsx برای تطبیق با response جدید endpoint — interface DashboardStats در page.tsx با response backend هماهنگ نیست (فیلدهای اضافی دارد)
  - نوشتن تست‌های واحد برای endpoint /api/stats/dashboard — تست‌ها با خطای داخلی pytest (rc=4) اجرا می‌شوند و نیاز به رفع دارند

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 5
  id: 6a9da54c-089e-4e84-be8c-de73716981ce
  عنوان اصلی: صفحه Dashboard در حالت static build با خطای 500 در endpoint /api/stats/dashboard مواجه است
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش دهد [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_loaded_with_data"}, {"a]
  - در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده شود [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for", "selector": "[data-testid='error-message-dashboard']", "timeout_ms": 5000}, {"action": "assert_vis]
  - دکمه Refresh دوباره داده‌ها را بارگذاری کند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_before_refresh"}, {"act]
  - در حالت static export، یک پیام 'Dashboard data unavailable in static mode' نشان داده شود [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "domcontentloaded"}, {"action": "assert_visible", "selector": "[data-testid='static-]

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
صفحه Dashboard در حالت static build با خطای 500 در endpoint /api/stats/dashboard مواجه است

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/dashboard/page.tsx:30-61` — `fetchDashboardData` — این تابع در حالت static export کار نمی‌کند چون به API واقعی نیاز دارد
  ```tsx
  const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/stats/dashboard');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setStats(data);
      } catch (err: any) {
        ...
      } finally {
        setLoading(false);
      }
    };
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 App Router + FastAPI + PostgreSQL

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/stats.py` (سطر 1) — این endpoint باید داده‌های dashboard را برگرداند
- `backend/static/dashboard/index.html` (سطر 1) — نسخه static شده dashboard که فقط اسپینر نشان می‌دهد
- `docs/DATABASE_SCHEMA.md` (سطر 1) — مستندات دیتابیس که به وجود ستون amount اشاره دارد

## 🌐 نقشهٔ وابستگی‌ها
این صفحه به endpoint /api/stats/dashboard وابسته است که خود به مدل‌های Customer و Facility وابسته است.

## 🔍 Context و وضعیت فعلی
صفحه Dashboard (frontend/src/app/dashboard/page.tsx) در حالت static export (frontend/out/dashboard/index.html) فقط یک اسپینر بی‌نهایت نشان می‌دهد و داده‌ها بارگذاری نمی‌شوند. کد فرانت‌اند از fetch('/api/stats/dashboard') استفاده می‌کند که در حالت static build به یک endpoint واقعی نیاز دارد. همچنین backend/static/dashboard/index.html نیز همین مشکل را دارد. این باعث می‌شود کاربر نتواند آمار داشبورد را ببیند و خطای 500 از سمت backend دریافت کند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش دهد
- [ ] در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده شود
- [ ] دکمه Refresh دوباره داده‌ها را بارگذاری کند
- [ ] در حالت static export، یک پیام 'Dashboard data unavailable in static mode' نشان داده شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. در فایل frontend/src/app/dashboard/page.tsx، تابع fetchDashboardData را اصلاح کنید تا از try-catch مناسب و fallback UI استفاده کند. 2. اطمینان حاصل کنید که endpoint /api/stats/dashboard در backend/app/routers/stats.py به درستی پیاده‌سازی شده و ستون amount در جدول facilities وجود دارد. 3. برای حالت static export، یک mock data یا fallback UI اضافه کنید.

## 💡 نمونه‌های قبل/بعد
**رفع خطای 500 با اضافه کردن fallback**

_قبل:_
```
const response = await fetch('/api/stats/dashboard');
if (!response.ok) throw new Error(...);
```

_بعد:_
```
const response = await fetch('/api/stats/dashboard');
if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X GET http://localhost:8000/api/stats/dashboard -H 'Authorization: Bearer <token>'`
- `npm run build && npm run start`
- `pytest backend/tests/test_dashboard.py -v`

## ⚠️ ریسک‌ها و موارد احتیاط
احتمال شکستن endpoint در صورت عدم وجود ستون amount در دیتابیس

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 4 از 5
  id: e0199147-e69a-4f7e-8435-e61d649f1354
  عنوان اصلی: Implement dashboard error handling for missing column
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - Dashboard shows error message when API call fails instead of infinite spinner [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_error_state"}, {"action]
  - User can click 'Try Again' button to retry the API call [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for", "selector": "[data-testid='dashboard-error-message']", "timeout_ms": 5000}, {"action": "screenshot]
  - Backend returns proper error response when amount column is missing [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["detail"], "json_contains": {"detail": "Error calculating monthly reve]

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
Dashboard page stuck in infinite loading state due to missing 'amount' column in facilities table

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/dashboard/page.tsx:75-99` — `loading state` — Loading state never transitions to error state if fetch fails
  ```tsx
  if (loading) {
      return (
        <div className="container mx-auto p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <Button variant="outline" disabled>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </Button>
          </div>
          ...
        </div>
      );
    }
  ```
- `backend/app/routers/stats.py:1-50` — `dashboard stats endpoint` — Endpoint likely queries facilities.amount which may be missing
  ```python
  // Not provided but referenced in DATABASE_SCHEMA.md as causing 500 error
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + PostgreSQL + Next.js 14 App Router

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `docs/DATABASE_SCHEMA.md` (سطر 1) — Documents the amount column requirement
- `backend/migrations/versions/002_add_missing_columns.py` (سطر 1) — Migration that should add the amount column
- `backend/app/main.py` — این فایل `stats.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
Dashboard page depends on stats endpoint which depends on facilities table schema. Missing column breaks the entire dashboard.

## 🔍 Context و وضعیت فعلی
The dashboard page (`frontend/src/app/dashboard/page.tsx`) fetches data from `/api/stats/dashboard` and shows a loading spinner indefinitely. The backend endpoint `backend/app/routers/stats.py` likely queries the `facilities` table for the `amount` column to calculate `monthly_revenue`. According to `docs/DATABASE_SCHEMA.md`, the `amount` column is critical for dashboard calculations and its absence causes a 500 error. The frontend's error handling (lines 40-55) catches this but the UI remains stuck on the loading state because the error state is not properly rendered when `loading` is true. The static HTML in `backend/static/dashboard/index.html` confirms the loading spinner is always shown.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] Dashboard shows error message when API call fails instead of infinite spinner
- [ ] User can click 'Try Again' button to retry the API call
- [ ] Backend returns proper error response when amount column is missing
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. Ensure the `amount` column exists in the `facilities` table by running the Alembic migration. 2. Fix the frontend error handling in `frontend/src/app/dashboard/page.tsx` to properly display the error state when loading fails. 3. Add a timeout mechanism to break out of infinite loading.

## 💡 نمونه‌های قبل/بعد
**Fix loading state to show error**

_قبل:_
```
if (loading) { return <LoadingSpinner /> }
```

_بعد:_
```
if (loading && !error) { return <LoadingSpinner /> }
if (error) { return <ErrorState message={error} onRetry={handleRefresh} /> }
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X GET http://localhost:8000/api/stats/dashboard -H 'Authorization: Bearer <token>'`
- `Check browser console for network errors on dashboard page`

## ⚠️ ریسک‌ها و موارد احتیاط
Low risk - primarily UI fix and database migration verification

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 5 از 5
  id: 9a50880a-ea5f-4482-867a-cefb621cbffb
  عنوان اصلی: رفع استفاده از کامپوننت‌های UI تعریف‌نشده در داشبورد
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": ".", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "lint", "timeout_seconds": 60}]
  - type-check موفق است [verify_method=backend_test] [verify_plan={"test_node": "typecheck", "timeout_seconds": 60}]

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
استفاده از کامپوننت‌های UI تعریف‌نشده در صفحه داشبورد

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
فایل `frontend/src/app/dashboard/page.tsx` (خطوط 2-5) کامپوننت‌هایی مانند `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Skeleton`, `Alert`, `AlertDescription` را از مسیرهای `@/components/ui/card`, `@/components/ui/button`, `@/components/ui/skeleton`, `@/components/ui/alert` import می‌کند. این کامپوننت‌ها در ساختار پروژه وجود ندارند و باعث خطای build و runtime می‌

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
_(مجری بر اساس Context و معیارهای پذیرش، مراحل را تعیین کند)_

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
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

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
- در commit message: `merged-from: 57db04f7-e3df-4b27-b5c7-c872e9ccf486, ab4622a6-7eaa-4d03-bc4f-be7e6207628e, 6a9da54c-089e-4e84-be8c-de73716981ce, e0199147-e69a-4f7e-8435-e61d649f1354, 9a50880a-ea5f-4482-867a-cefb621cbffb`
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

🧬 این یک تسک تلفیقی است — از 5 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به طور مستقیم به مشکلات مربوط به نمایش داده‌ها در داشبورد، تطبیق قرارداد API بین بک‌اند و فرانت‌اند برای داده‌های آماری، رفع خطاهای 500 در حالت static build و مدیریت خطاهای مربوط به ستون‌های از دست رفته در داشبورد می‌پردازند. همچنین شامل رفع مشکلات کامپوننت‌های UI تعریف‌نشده در داشبورد است.
🎯 theme: نمایش داده‌های داشبورد
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 5
  id: 57db04f7-e3df-4b27-b5c7-c872e9ccf486
  عنوان اصلی: نمایش داده‌های داشبورد و صفحات مرتبط
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py

📋 acceptance_criteria کامل:
  - صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner) [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "wait_for", "selector": "[data-testid='dashboard-content']
  - در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "wait_for", "selector": "[data-testid='error-message']", ]
  - صفحات customers و facilities نیز داده‌ها را نمایش دهند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/customers"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "wait_for", "selector": "[data-testid='customers-content']

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
داشبورد فرانت‌اند در حالت loading گیر کرده و داده‌ها را نمایش نمی‌دهد

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/stats.py:1-50` — `dashboard_stats` — این endpoint احتمالاً dummy response برمی‌گرداند یا پیاده‌سازی نشده است
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.database import get_db
  
  router = APIRouter()
  
  @router.get('/dashboard')
  async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
      # TODO: implement
      return {'total_customers': 0, 'total_facilities': 0}
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 static export + FastAPI backend

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/src/app/dashboard/page.tsx` (سطر 34) — فرانت‌اند که این endpoint را صدا می‌زند و spinner را نمایش می‌دهد
- `backend/static/dashboard/index.html` (سطر 76) — build استاتیک که spinner را نشان می‌دهد
- `backend/static/customers/index.html` (سطر 82) — همین مشکل در صفحه customers
- `backend/static/facilities/index.html` (سطر 82) — همین مشکل در صفحه facilities
- `backend/app/main.py` — این فایل `stats.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
این باگ روی تمام صفحات اصلی (dashboard, customers, facilities) تأثیر می‌گذارد و تجربه کاربری را کاملاً مختل کرده است.

## 🔍 Context و وضعیت فعلی
صفحات dashboard، customers و facilities در build استاتیک (backend/static/) همگی در حالت loading بی‌نهایت (spinner) باقی می‌مانند. در backend/static/dashboard/index.html خط ۷۶-۸۴ یک div با کلاس 'animate-spin' و متن 'Loading dashboard data...' وجود دارد که هرگز پنهان نمی‌شود. این نشان می‌دهد که فراخوانی API (fetch('/api/stats/dashboard') در frontend/src/app/dashboard/page.tsx خط ۳۴) با خطا مواجه می‌شود یا داده‌ای برنمی‌گرداند. در build استاتیک، این فراخوانی‌ها در سمت کلاینت انجام می‌شوند و اگر بک‌اند در دسترس نباشد یا endpoint پاسخ ندهد، spinner باقی می‌ماند. همچنین در backend/static/customers/index.html و backend/static/facilities/index.html نیز spinner مشابهی دیده می‌شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner)
- [ ] در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود
- [ ] صفحات customers و facilities نیز داده‌ها را نمایش دهند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱. اطمینان حاصل کنید که endpoint /api/stats/dashboard در بک‌اند به درستی پیاده‌سازی شده و داده برمی‌گرداند. ۲. در فرانت‌اند، یک fallback UI برای حالت خطا یا empty state اضافه کنید تا کاربر spinner ابدی نبیند. ۳. خطای 500 که در backend/static/dashboard/index.html خط ۴۴-۴۸ (کد جاوااسکریپت) مدیریت شده را بررسی کنید.

## 💡 نمونه‌های قبل/بعد
**حالت فعلی (spinner ابدی)**

_قبل:_
```
<div class='animate-spin ...'></div><p>Loading dashboard data...</p>
```

_بعد:_
```
<div>داده‌ها نمایش داده می‌شوند یا پیام خطای مناسب
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl http://localhost:8000/api/stats/dashboard`
- `npm run build && npm start (بررسی build استاتیک)`

## ⚠️ ریسک‌ها و موارد احتیاط
نیاز به بررسی endpoint بک‌اند و احتمالاً اصلاح queryهای د

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 5
  id: ab4622a6-7eaa-4d03-bc4f-be7e6207628e
  عنوان اصلی: تطبیق contract داشبورد بک‌اند و فرانت‌اند
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 200, "required_fields": ["total_customers", "total_facilities", "active_facilities", "expiring_]
  - ستون amount در جدول facilities وجود دارد و NOT NULL است [verify_method=static] [verify_plan={"grep_patterns": ["amount.*NOT NULL", "amount.*nullable=False"], "files_hint": ["backend/app/models/facility.py", "docs/DATABASE_SCHEMA.md"]}]
  - dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "assert_visible", "selector": "[data-testid='dashboard-st]
  - تست واحد برای endpoint اضافه شود [verify_method=backend_test] [verify_plan={"test_node": "tests/test_stats.py::test_dashboard_endpoint", "timeout_seconds": 60}]

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
عدم تطابق contract بین endpoint /api/stats/dashboard و فرانت‌اند dashboard/page.tsx

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/stats.py:1-50` — `dashboard_stats` — این endpoint باید response ای مطابق با DashboardStats بدهد
  ```python
  # نیاز به بررسی کامل endpoint
  ```
- `frontend/src/app/dashboard/page.tsx:10-22` — `DashboardStats` — اینترفیس فرانت‌اند که backend باید با آن match کند
  ```tsx
  interface DashboardStats {
    total_customers: number;
    total_facilities: number;
    active_facilities: number;
    expiring_soon: number;
    monthly_revenue: number;
    recent_activities: Array<{...}>;
  }
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + SQLAlchemy + Next.js 14 App Router

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/models/facility.py` (سطر 1) — مدل facility که ستون amount را دارد
- `backend/app/schemas/stats.py` (سطر 1) — شاید schema response تعریف شده
- `backend/migrations/versions/002_add_missing_columns.py` (سطر 1) — مهاجرت برای اضافه کردن ستون‌های缺失
- `backend/app/main.py` — این فایل `stats.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
این endpoint توسط dashboard/page.tsx در فرانت‌اند استفاده می‌شود و وابسته به مدل‌های facility و customer است.

## 🔍 Context و وضعیت فعلی
فرانت‌اند dashboard/page.tsx (خطوط 10-22) یک interface DashboardStats تعریف کرده که شامل فیلدهای total_customers, total_facilities, active_facilities, expiring_soon, monthly_revenue, recent_activities است. اما endpoint /api/stats/dashboard در backend/app/routers/stats.py وجود دارد و مشخص نیست که دقیقاً چه response shape ای برمی‌گرداند. بررسی فایل‌های backend نشان می‌دهد که مدل facility ستون amount را دارد (طبق docs/DATABASE_SCHEMA.md) اما در مدل‌های backend/app/models/facility.py ممکن است این ستون وجود نداشته باشد یا type mismatch داشته باشد. این باعث خطای 500 در dashboard می‌شود که در خروجی static dashboard/index.html (خط 1) به صورت 'Loading dashboard data...' و اسپینر بی‌نهایت دیده می‌شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد
- [ ] ستون amount در جدول facilities وجود دارد و NOT NULL است
- [ ] dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند
- [ ] تست واحد برای endpoint اضافه شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. بررسی و تطبیق کامل response schema endpoint /api/stats/dashboard با interface DashboardStats در frontend. اطمینان از وجود ستون amount در مدل Facility و مهاجرت دیتابیس. اضافه کردن validation با Pydantic برای response.

## 💡 نمونه‌های قبل/بعد
**response shape**

_قبل:_
```
{"total_customers": 0, "error": "column amount does not exist"}
```

_بعد:_
```
{"total_customers": 592, "total_facilities": 150, "active_facilities": 120, "expiring_soon": 5, "monthly_revenue": 500000, "recent_activities": []}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl http://localhost:8000/api/stats/dashboard | jq .`
- `pytest backend/tests/test_facilities.py -k amount`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر در response ممکن است clientهای دیگر را بشکند

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی و تطبیق مدل Facility در backend/app/models/facility.py با ستون amount از DATABASE_SCHEMA.md
  - بررسی و تطبیق schema response در backend/app/schemas/stats.py با interface DashboardStats فرانت‌اند
  - بررسی و رفع مشکل static dashboard/index.html که اسپینر بی‌نهایت نشان می‌دهد
  - بررسی و به‌روزرسانی مهاجرت دیتابیس (migrations) برای اضافه کردن ستون‌های missing در facility
  - نوشتن تست‌های فرانت‌اند برای dashboard/page.tsx

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و اصلاح endpoint dashboard_stats در backend/app/routers/stats.py برای استفاده از schema جدید و بازگرداندن داده‌های صحیح — فیلدهای active_facilities, monthly_revenue, recent_activities در response backend وجود ندارند
  - بررسی و اصلاح فرانت‌اند dashboard/page.tsx برای تطبیق با response جدید endpoint — interface DashboardStats در page.tsx با response backend هماهنگ نیست (فیلدهای اضافی دارد)
  - نوشتن تست‌های واحد برای endpoint /api/stats/dashboard — تست‌ها با خطای داخلی pytest (rc=4) اجرا می‌شوند و نیاز به رفع دارند

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 5
  id: 6a9da54c-089e-4e84-be8c-de73716981ce
  عنوان اصلی: صفحه Dashboard در حالت static build با خطای 500 در endpoint /api/stats/dashboard مواجه است
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش دهد [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_loaded_with_data"}, {"a]
  - در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده شود [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for", "selector": "[data-testid='error-message-dashboard']", "timeout_ms": 5000}, {"action": "assert_vis]
  - دکمه Refresh دوباره داده‌ها را بارگذاری کند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_before_refresh"}, {"act]
  - در حالت static export، یک پیام 'Dashboard data unavailable in static mode' نشان داده شود [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "domcontentloaded"}, {"action": "assert_visible", "selector": "[data-testid='static-]

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
صفحه Dashboard در حالت static build با خطای 500 در endpoint /api/stats/dashboard مواجه است

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/dashboard/page.tsx:30-61` — `fetchDashboardData` — این تابع در حالت static export کار نمی‌کند چون به API واقعی نیاز دارد
  ```tsx
  const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/stats/dashboard');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setStats(data);
      } catch (err: any) {
        ...
      } finally {
        setLoading(false);
      }
    };
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Next.js 14 App Router + FastAPI + PostgreSQL

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/stats.py` (سطر 1) — این endpoint باید داده‌های dashboard را برگرداند
- `backend/static/dashboard/index.html` (سطر 1) — نسخه static شده dashboard که فقط اسپینر نشان می‌دهد
- `docs/DATABASE_SCHEMA.md` (سطر 1) — مستندات دیتابیس که به وجود ستون amount اشاره دارد

## 🌐 نقشهٔ وابستگی‌ها
این صفحه به endpoint /api/stats/dashboard وابسته است که خود به مدل‌های Customer و Facility وابسته است.

## 🔍 Context و وضعیت فعلی
صفحه Dashboard (frontend/src/app/dashboard/page.tsx) در حالت static export (frontend/out/dashboard/index.html) فقط یک اسپینر بی‌نهایت نشان می‌دهد و داده‌ها بارگذاری نمی‌شوند. کد فرانت‌اند از fetch('/api/stats/dashboard') استفاده می‌کند که در حالت static build به یک endpoint واقعی نیاز دارد. همچنین backend/static/dashboard/index.html نیز همین مشکل را دارد. این باعث می‌شود کاربر نتواند آمار داشبورد را ببیند و خطای 500 از سمت backend دریافت کند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش دهد
- [ ] در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده شود
- [ ] دکمه Refresh دوباره داده‌ها را بارگذاری کند
- [ ] در حالت static export، یک پیام 'Dashboard data unavailable in static mode' نشان داده شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. در فایل frontend/src/app/dashboard/page.tsx، تابع fetchDashboardData را اصلاح کنید تا از try-catch مناسب و fallback UI استفاده کند. 2. اطمینان حاصل کنید که endpoint /api/stats/dashboard در backend/app/routers/stats.py به درستی پیاده‌سازی شده و ستون amount در جدول facilities وجود دارد. 3. برای حالت static export، یک mock data یا fallback UI اضافه کنید.

## 💡 نمونه‌های قبل/بعد
**رفع خطای 500 با اضافه کردن fallback**

_قبل:_
```
const response = await fetch('/api/stats/dashboard');
if (!response.ok) throw new Error(...);
```

_بعد:_
```
const response = await fetch('/api/stats/dashboard');
if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X GET http://localhost:8000/api/stats/dashboard -H 'Authorization: Bearer <token>'`
- `npm run build && npm run start`
- `pytest backend/tests/test_dashboard.py -v`

## ⚠️ ریسک‌ها و موارد احتیاط
احتمال شکستن endpoint در صورت عدم وجود ستون amount در دیتابیس

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 4 از 5
  id: e0199147-e69a-4f7e-8435-e61d649f1354
  عنوان اصلی: Implement dashboard error handling for missing column
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - Dashboard shows error message when API call fails instead of infinite spinner [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_error_state"}, {"action]
  - User can click 'Try Again' button to retry the API call [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for", "selector": "[data-testid='dashboard-error-message']", "timeout_ms": 5000}, {"action": "screenshot]
  - Backend returns proper error response when amount column is missing [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["detail"], "json_contains": {"detail": "Error calculating monthly reve]

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
Dashboard page stuck in infinite loading state due to missing 'amount' column in facilities table

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/dashboard/page.tsx:75-99` — `loading state` — Loading state never transitions to error state if fetch fails
  ```tsx
  if (loading) {
      return (
        <div className="container mx-auto p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <Button variant="outline" disabled>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </Button>
          </div>
          ...
        </div>
      );
    }
  ```
- `backend/app/routers/stats.py:1-50` — `dashboard stats endpoint` — Endpoint likely queries facilities.amount which may be missing
  ```python
  // Not provided but referenced in DATABASE_SCHEMA.md as causing 500 error
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + PostgreSQL + Next.js 14 App Router

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `docs/DATABASE_SCHEMA.md` (سطر 1) — Documents the amount column requirement
- `backend/migrations/versions/002_add_missing_columns.py` (سطر 1) — Migration that should add the amount column
- `backend/app/main.py` — این فایل `stats.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
Dashboard page depends on stats endpoint which depends on facilities table schema. Missing column breaks the entire dashboard.

## 🔍 Context و وضعیت فعلی
The dashboard page (`frontend/src/app/dashboard/page.tsx`) fetches data from `/api/stats/dashboard` and shows a loading spinner indefinitely. The backend endpoint `backend/app/routers/stats.py` likely queries the `facilities` table for the `amount` column to calculate `monthly_revenue`. According to `docs/DATABASE_SCHEMA.md`, the `amount` column is critical for dashboard calculations and its absence causes a 500 error. The frontend's error handling (lines 40-55) catches this but the UI remains stuck on the loading state because the error state is not properly rendered when `loading` is true. The static HTML in `backend/static/dashboard/index.html` confirms the loading spinner is always shown.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] Dashboard shows error message when API call fails instead of infinite spinner
- [ ] User can click 'Try Again' button to retry the API call
- [ ] Backend returns proper error response when amount column is missing
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. Ensure the `amount` column exists in the `facilities` table by running the Alembic migration. 2. Fix the frontend error handling in `frontend/src/app/dashboard/page.tsx` to properly display the error state when loading fails. 3. Add a timeout mechanism to break out of infinite loading.

## 💡 نمونه‌های قبل/بعد
**Fix loading state to show error**

_قبل:_
```
if (loading) { return <LoadingSpinner /> }
```

_بعد:_
```
if (loading && !error) { return <LoadingSpinner /> }
if (error) { return <ErrorState message={error} onRetry={handleRefresh} /> }
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X GET http://localhost:8000/api/stats/dashboard -H 'Authorization: Bearer <token>'`
- `Check browser console for network errors on dashboard page`

## ⚠️ ریسک‌ها و موارد احتیاط
Low risk - primarily UI fix and database migration verification

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 5 از 5
  id: 9a50880a-ea5f-4482-867a-cefb621cbffb
  عنوان اصلی: رفع استفاده از کامپوننت‌های UI تعریف‌نشده در داشبورد
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": ".", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "lint", "timeout_seconds": 60}]
  - type-check موفق است [verify_method=backend_test] [verify_plan={"test_node": "typecheck", "timeout_seconds": 60}]

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
استفاده از کامپوننت‌های UI تعریف‌نشده در صفحه داشبورد

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
فایل `frontend/src/app/dashboard/page.tsx` (خطوط 2-5) کامپوننت‌هایی مانند `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Skeleton`, `Alert`, `AlertDescription` را از مسیرهای `@/components/ui/card`, `@/components/ui/button`, `@/components/ui/skeleton`, `@/components/ui/alert` import می‌کند. این کامپوننت‌ها در ساختار پروژه وجود ندارند و باعث خطای build و runtime می‌

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
_(مجری بر اساس Context و معیارهای پذیرش، مراحل را تعیین کند)_

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
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

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
- در commit message: `merged-from: 57db04f7-e3df-4b27-b5c7-c872e9ccf486, ab4622a6-7eaa-4d03-bc4f-be7e6207628e, 6a9da54c-089e-4e84-be8c-de73716981ce, e0199147-e69a-4f7e-8435-e61d649f1354, 9a50880a-ea5f-4482-867a-cefb621cbffb`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner) _(verify: ui_interaction)_
2. در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود _(verify: ui_interaction)_
3. صفحات customers و facilities نیز داده‌ها را نمایش دهند _(verify: ui_interaction)_
4. endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد _(verify: api_response)_
5. ستون amount در جدول facilities وجود دارد و NOT NULL است _(verify: static)_
6. dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند _(verify: ui_interaction)_
7. تست واحد برای endpoint اضافه شود _(verify: backend_test)_
8. صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش دهد _(verify: ui_interaction)_
9. در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده شود _(verify: ui_interaction)_
10. دکمه Refresh دوباره داده‌ها را بارگذاری کند _(verify: ui_interaction)_
11. در حالت static export، یک پیام 'Dashboard data unavailable in static mode' نشان داده شود _(verify: ui_interaction)_
12. Dashboard shows error message when API call fails instead of infinite spinner _(verify: ui_interaction)_
13. User can click 'Try Again' button to retry the API call _(verify: ui_interaction)_
14. Backend returns proper error response when amount column is missing _(verify: api_response)_
15. اعمال تغییر بدون شکستن تست‌های موجود _(verify: backend_test)_
16. linter بدون warning عبور می‌کند _(verify: backend_test)_
17. type-check موفق است _(verify: backend_test)_

## Task Steps

### Step 1: بررسی اولیه خودکار repo و تشخیص پیاده‌سازی‌های قبلی پیش از اجرا
**Status:** `done` (100%)
**Scope:** این بخش یک یادداشت هشداردهنده برای مدل اجراکننده است و شامل هیچ دستور اجرایی مشخصی نیست. وظیفه آن الزام مدل به بررسی مستقل repo، جستجوی پیاده‌سازی‌های موجود، و جلوگیری از بازسازی کدهای از قبل موجود است. هیچ مرحله فنی یا تغییری در کد در این بخش تعریف نشده است.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 2: رفع باگ loading بی‌نهایت در داشبورد با پیاده‌سازی endpoint dashboard_stats
**Status:** `done` (100%)
**Scope:** این مرحله فقط به پیاده‌سازی کامل endpoint `GET /dashboard` در `backend/app/routers/stats.py` می‌پردازد. شامل کوئری واقعی از دیتابیس (با استفاده از AsyncSession) برای برگرداندن داده‌های معتبر (total_customers, total_facilities) است. تغییرات در فرانت‌اند یا فایل‌های استاتیک (HTML) جزو این مرحله نیست. endpoint باید به‌جای پاسخ dummy، داده‌های واقعی برگرداند تا spinner در build استاتیک پنهان شود.
**Excerpt:**
```
داشبورد فرانت‌اند در حالت loading گیر کرده و داده‌ها را نمایش نمی‌دهد

- `backend/app/routers/stats.py:1-50` — `dashboard_stats` — این endpoint احتمالاً dummy response برمی‌گرداند یا پیاده‌سازی نشده است
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.database import get_db
  
  router = APIRouter()
  
  @router.get('/dashboard')
  async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
      # TODO: implement
      return {'total_customers': 0, 'total_facilities': 0}
  ```

صفحات dashboard، customers و facilities در build استاتیک (backend/static/) همگی در حالت loading بی‌نهایت (spinner) باقی می‌مانند. در backend/static/dashboard/index.html خط ۷۶-۸۴ یک div با کلاس 'animate-spin' و متن 'Loading dashboard data...' وجود دارد که هرگز پنهان نمی‌شود. این نشان می‌دهد که فراخوانی API (fetch('/api/stats/dashboard') در frontend/src/app/dashboard/page.tsx خط ۳۴) با خطا مواجه می‌شود یا داده‌ای برنمی‌گرداند.
```

### Step 3: همگام‌سازی نمایش داده‌های واقعی در داشبورد و صفحات مرتبط
**Status:** `done` (100%)
**Scope:** این بخش شامل رفع باگ‌های نمایش داده‌ها در داشبورد، صفحات customers و facilities است. تمرکز بر رفتار قابل مشاهده کاربر (نمایش داده‌های واقعی، مدیریت خطا، عدم نمایش spinner ابدی) است. پیاده‌سازی endpoint /api/stats/dashboard در بک‌اند و fallback UI در فرانت‌اند را پوشش می‌دهد. تست‌ها و linting نیز باید پاس شوند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner)
- [ ] در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود
- [ ] صفحات customers و facilities نیز داده‌ها را نمایش دهند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱. اطمینان حاصل کنید که endpoint /api/stats/dashboard در بک‌اند به درستی پیاده‌سازی شده و داده برمی‌گرداند. ۲. در فرانت‌اند، یک fallback UI برای حالت خطا یا empty state اضافه کنید تا کاربر spinner ابدی نبیند. ۳. خطای 500 که در backend/static/dashboard/index.html خط ۴۴-۴۸ (کد جاوااسکریپت) مدیریت شده را بررسی کنید.
```

### Step 4: رفع spinner ابدی و نمایش داده‌ها یا پیام خطا در داشبورد
**Status:** `done` (100%)
**Scope:** این بخش شامل رفع مشکل spinner ابدی در صفحه داشبورد است. خروجی مورد انتظار: داده‌ها نمایش داده شوند یا در صورت خطا، پیام خطای مناسب نشان داده شود. این بخش شامل تغییر در frontend (احتمالاً page.tsx) و backend (احتمالاً stats.py) است. spinner باید با نمایش داده‌ها یا پیام خطا جایگزین شود.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**حالت فعلی (spinner ابدی)**

_قبل:_
```
<div class='animate-spin ...'></div><p>Loading dashboard data...</p>
```

_بعد:_
```
<div>داده‌ها نمایش داده می‌شوند یا پیام خطای مناسب
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 5: بررسی و اصلاح endpoint بک‌اند /api/stats/dashboard برای تطبیق با interface DashboardStats
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی endpoint بک‌اند (backend/app/routers/stats.py) و اصلاح queryهای دیتابیس برای اطمینان از تطبیق کامل response با interface DashboardStats است. وابستگی به فرانت‌اند (frontend/src/app/dashboard/page.tsx) برای تطبیق نوع داده‌ها وجود دارد. این مرحله بخشی از تسک 2 از 5 با اولویت critical است.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
نیاز به بررسی endpoint بک‌اند و احتمالاً اصلاح queryهای د

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 5
  id: ab4622a6-7eaa-4d03-bc4f-be7e6207628e
  عنوان اصلی: تطبیق contract داشبورد بک‌اند و فرانت‌اند
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 200, "required_fields": ["total_customers", "total_facilities", "active_facilities", "expiring_"]
```

### Step 6: تأیید وجود ستون amount در جدول facilities و بارگذاری صحیح داشبورد و افزودن تست واحد
**Status:** `pending` (0%)
**Scope:** این بخش شامل سه وظیفه مجزا اما مرتبط است: (1) تأیید استاتیک وجود ستون amount با محدودیت NOT NULL در مدل و داکیومنت، (2) تأیید تعاملی بارگذاری صحیح صفحه داشبورد بدون خطا و نمایش داده‌ها، (3) افزودن تست واحد برای endpoint داشبورد. هیچ‌کدام از این موارد قبلاً اجرا نشده و صرفاً برای مرجع نیستند.
**Excerpt:**
```
- ستون amount در جدول facilities وجود دارد و NOT NULL است [verify_method=static] [verify_plan={"grep_patterns": ["amount.*NOT NULL", "amount.*nullable=False"], "files_hint": ["backend/app/models/facility.py", "docs/DATABASE_SCHEMA.md"]}]
  - dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "assert_visible", "selector": "[data-testid='dashboard-st']"}]}]
  - تست واحد برای endpoint اضافه شود [verify_method=backend_test] [verify_plan={"test_node": "tests/test_stats.py::test_dashboard_endpoint", "timeout_seconds": 60}]
```

### Step 7: بررسی و همگام‌سازی نمایش داده‌ها در داشبورد با رفع باگ‌های احتمالی
**Status:** `done` (100%)
**Scope:** این بخش شامل بررسی کامل وضعیت فعلی repo برای تشخیص وجود یا عدم وجود پیاده‌سازی‌های مرتبط با رفع باگ‌ها و همگام‌سازی نمایش داده‌ها در داشبورد است. شامل جستجوی فایل‌های backend/app/routers/stats.py، frontend/src/app/dashboard/page.tsx، backend/app/main.py، backend/app/models/facility.py، docs/DATABASE_SCHEMA.md، tests/test_stats.py، backend/app/routers/stats.py، backend/migrations/versions/002_add_missing_columns.py، backend/tests/test_facilities.py و backend/tests/test_dashboard.py می‌شود. نکته حیاتی: قبل از هر اقدامی باید با grep/search و خواندن فایل‌های مرتبط بررسی شود که چه چیزی از قبل وجود دارد و از بازسازی موارد موجود خودداری شود.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 8: همگام‌سازی contract بین endpoint /api/stats/dashboard و فرانت‌اند dashboard/page.tsx
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی و اصلاح کامل endpoint /api/stats/dashboard در backend/app/routers/stats.py است تا response آن دقیقاً با interface DashboardStats تعریف‌شده در frontend/src/app/dashboard/page.tsx (خطوط 10-22) مطابقت داشته باشد. همچنین شامل بررسی وجود ستون amount در مدل facility (backend/app/models/facility.py) و schema response در backend/app/routers/stats.py می‌شود. خارج از scope: تغییرات در فرانت‌اند، مهاجرت دیتابیس، یا تست‌های integration.
**Excerpt:**
```
عدم تطابق contract بین endpoint /api/stats/dashboard و فرانت‌اند dashboard/page.tsx

- `backend/app/routers/stats.py:1-50` — `dashboard_stats` — این endpoint باید response ای مطابق با DashboardStats بدهد
  ```python
  # نیاز به بررسی کامل endpoint
  ```
- `frontend/src/app/dashboard/page.tsx:10-22` — `DashboardStats` — اینترفیس فرانت‌اند که backend باید با آن match کند
  ```tsx
  interface DashboardStats {
    total_customers: number;
    total_facilities: number;
    active_facilities: number;
    expiring_soon: number;
    monthly_revenue: number;
    recent_activities: Array<{...}>;
  }
  ```

بررسی فایل‌های backend نشان می‌دهد که مدل facility ستون amount را دارد (طبق docs/DATABASE_SCHEMA.md) اما در مدل‌های backend/app/models/facility.py ممکن است این ستون وجود نداشته باشد یا type mismatch داشته باشد. این باعث خطای 500 در dashboard می‌شود که در خروجی static dashboard/index.html (خط 1) به صورت 'Loading dashboard data...' و اسپینر بی‌نهایت دیده می‌شود.
```

### Step 9: همگام‌سازی پاسخ endpoint /api/stats/dashboard با interface DashboardStats
**Status:** `done` (100%)
**Scope:** این مرحله تضمین می‌کند که پاسخ JSON برگشتی از endpoint /api/stats/dashboard دقیقاً با ساختار تعریف‌شده در interface DashboardStats مطابقت دارد. شامل بررسی نوع فیلدها، وجود تمام فیلدهای اجباری، و عدم وجود فیلد اضافی است. خارج از scope: منطق محاسبه آمار، اتصال به دیتابیس، یا تغییر در frontend.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد
```

### Step 10: بررسی و تطبیق کامل response schema endpoint /api/stats/dashboard با interface DashboardStats در frontend و اطمینان از وجود ستون amount در مدل Facility
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی و تطبیق کامل schema خروجی endpoint /api/stats/dashboard با interface DashboardStats در frontend، اطمینان از وجود ستون amount در مدل Facility و مهاجرت دیتابیس، و اضافه کردن validation با Pydantic برای response است. خارج از scope این مرحله: تست‌نویسی، linting، type-checking و سایر آیتم‌های لیست که در مراحل بعدی انجام می‌شوند.
**Excerpt:**
```
- [ ] ستون amount در جدول facilities وجود دارد و NOT NULL است
- [ ] dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند
- [ ] تست واحد برای endpoint اضافه شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. بررسی و تطبیق کامل response schema endpoint /api/stats/dashboard با interface DashboardStats در frontend. اطمینان از وجود ستون amount در مدل Facility و مهاجرت دیتابیس. اضافه کردن validation با Pydantic برای response.
```

### Step 11: رفع خطای 'column amount does not exist' و بازگرداندن داده‌های صحیح dashboard
**Status:** `done` (100%)
**Scope:** این بخش شامل رفع باگ در endpoint stats است که خطای 'column amount does not exist' را برمی‌گرداند. خروجی مورد انتظار شامل فیلدهای total_customers, total_facilities, active_facilities, expiring_soon, monthly_revenue, recent_activities است. تغییرات باید در فایل stats.py و احتمالاً migration مربوطه انجام شود. این بخش شامل frontend یا سایر endpointها نمی‌شود.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**response shape**

_قبل:_
```
{"total_customers": 0, "error": "column amount does not exist"}
```

_بعد:_
```
{"total_customers": 592, "total_facilities": 150, "active_facilities": 120, "expiring_soon": 5, "monthly_revenue": 500000, "recent_activities": []}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 12: رفع endpoint dashboard_stats برای بازگرداندن فیلدهای active_facilities, monthly_revenue, recent_activities
**Status:** `done` (100%)
**Scope:** این مرحله شامل بررسی و اصلاح endpoint dashboard_stats در backend/app/routers/stats.py است. هدف، تطبیق response با schema جدید stats.py و بازگرداندن فیلدهای گمشده (active_facilities, monthly_revenue, recent_activities) است. وابستگی‌های قبلی (مدل facility، schema stats، مهاجرت دیتابیس) انجام شده‌اند. تغییرات نباید clientهای دیگر را بشکند. این مرحله شامل اصلاح فرانت‌اند یا تست‌ها نمی‌شود.
**Excerpt:**
```
🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و اصلاح endpoint dashboard_stats در backend/app/routers/stats.py برای استفاده از schema جدید و بازگرداندن داده‌های صحیح — فیلدهای active_facilities, monthly_revenue, recent_activities در response backend وجود ندارند
  - بررسی و اصلاح فرانت‌اند dashboard/page.tsx برای تطبیق با response جدید endpoint — interface DashboardStats در page.tsx با response backend هماهنگ نیست (فیلدهای اضافی دارد)
  - نوشتن تست‌های واحد برای endpoint /api/stats/dashboard — تست‌ها با خطای داخلی pytest (rc=4) اجرا می‌شوند و نیاز به رفع دارند
```

### Step 13: بررسی اولیه خودکار و جلوگیری از بازسازی موارد موجود در ریپازیتوری
**Status:** `done` (100%)
**Scope:** این بخش یک یادداشت هشداردهنده برای مدل اجراکننده است و شامل هیچ دستور اجرایی مستقیمی نیست. وظیفه آن الزام مدل به بررسی مستقل ریپازیتوری پیش از هر تغییری است. شامل: جستجوی فایل‌ها/توابع/قابلیت‌های موجود، عدم بازسازی موارد کامل، اصلاح موارد ناقص/اشتباه، و ثبت کامیت no-op در صورت عدم نیاز به تغییر. خارج از scope: اجرای مستقیم هیچ تغییری در کد.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 14: رفع خطای 500 در endpoint /api/stats/dashboard و همگام‌سازی نمایش داده‌ها در حالت static build
**Status:** `done` (100%)
**Scope:** این مرحله شامل رفع باگ endpoint /api/stats/dashboard در backend است که باعث خطای 500 می‌شود. همچنین شامل اصلاح fetchDashboardData در frontend/src/app/dashboard/page.tsx برای کار در حالت static export با استفاده از داده‌های mock یا pre-rendered. خارج از scope: تغییرات در backend/static/dashboard/index.html (در مرحله جداگانه) و اصلاح مدل‌های دیتابیس.
**Excerpt:**
```
صفحه Dashboard در حالت static build با خطای 500 در endpoint /api/stats/dashboard مواجه است. ... frontend/src/app/dashboard/page.tsx:30-61 — fetchDashboardData — این تابع در حالت static export کار نمی‌کند چون به API واقعی نیاز دارد. ... backend/app/routers/stats.py (سطر 1) — این endpoint باید داده‌های dashboard را برگرداند. ... backend/static/dashboard/index.html (سطر 1) — نسخه static شده dashboard که فقط اسپینر نشان می‌دهد. ... docs/DATABASE_SCHEMA.md (سطر 1) — مستندات دیتابیس که به وجود ستون amount اشاره دارد. ... این صفحه به endpoint /api/stats/dashboard وابسته است که خود به مدل‌های Customer و Facility وابسته است.
```

### Step 15: اصلاح fetchDashboardData، پیاده‌سازی endpoint /api/stats/dashboard و افزودن fallback UI برای static export
**Status:** `done` (100%)
**Scope:** این مرحله شامل سه تغییر هم‌زمان است: (1) اصلاح تابع fetchDashboardData در frontend/src/app/dashboard/page.tsx برای استفاده از try-catch و fallback UI، (2) اطمینان از پیاده‌سازی صحیح endpoint /api/stats/dashboard در backend/app/routers/stats.py و وجود ستون amount در جدول facilities، (3) افزودن mock data یا fallback UI برای حالت static export. خارج از scope: تغییرات در سایر فایل‌ها، اصلاح تست‌ها، یا تغییرات linter/type-check.
**Excerpt:**
```
1. 1. در فایل frontend/src/app/dashboard/page.tsx، تابع fetchDashboardData را اصلاح کنید تا از try-catch مناسب و fallback UI استفاده کند. 2. اطمینان حاصل کنید که endpoint /api/stats/dashboard در backend/app/routers/stats.py به درستی پیاده‌سازی شده و ستون amount در جدول facilities وجود دارد. 3. برای حالت static export، یک mock data یا fallback UI اضافه کنید.
```

### Step 16: رفع خطای 500 با اضافه کردن fallback در fetch داشبورد
**Status:** `done` (100%)
**Scope:** این بخش فقط به تغییر کد در فرانت‌اند (dashboard/page.tsx) مربوط می‌شود تا هنگام دریافت خطا از API، به جای throw کردن خطای عمومی، ابتدا بدنه خطا را parse کرده و پیام معنادار استخراج کند. بک‌اند و تست‌ها در این مرحله تغییر نمی‌کنند. نکته حیاتی: تغییر فقط در بخش fetch مربوط به stats dashboard است، نه سایر fetchها.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**رفع خطای 500 با اضافه کردن fallback**

_قبل:_
```
const response = await fetch('/api/stats/dashboard');
if (!response.ok) throw new Error(...);
```

_بعد:_
```
const response = await fetch('/api/stats/dashboard');
if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 17: پیاده‌سازی مدیریت خطای داشبورد برای ستون گمشده amount
**Status:** `done` (100%)
**Scope:** این بخش شامل پیاده‌سازی کامل تسک 4 از 5 است: مدیریت خطا در فرانت‌اند و بک‌اند برای زمانی که ستون amount در دیتابیس وجود ندارد. شامل: (1) تغییر endpoint بک‌اند برای بازگرداندن خطای 500 با پیام مناسب، (2) تغییر کامپوننت داشبورد فرانت‌اند برای نمایش پیام خطا و دکمه 'Try Again' به جای اسپینر بی‌نهایت. خارج از scope: سایر تسک‌ها، تغییرات دیتابیس، تست‌های واحد.
**Excerpt:**
```
تسک 4 از 5
  id: e0199147-e69a-4f7e-8435-e61d649f1354
  عنوان اصلی: Implement dashboard error handling for missing column
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/routers/stats.py, frontend/src/app/dashboard/page.tsx

📋 acceptance_criteria کامل:
  - Dashboard shows error message when API call fails instead of infinite spinner [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for_load", "state": "networkidle"}, {"action": "screenshot", "label": "dashboard_error_state"}, {"action]
  - User can click 'Try Again' button to retry the API call [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/dashboard"}, {"action": "wait_for", "selector": "[data-testid='dashboard-error-message']", "timeout_ms": 5000}, {"action": "screenshot]
  - Backend returns proper error response when amount column is missing [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["detail"], "json_contains": {"detail": "Error calculating monthly reve]
```

### Step 18: بررسی اولیه خودکار repo و جلوگیری از پیاده‌سازی مجدد قابلیت‌های موجود
**Status:** `done` (100%)
**Scope:** این بخش یک یادداشت هشداردهنده برای مدل اجراکننده است و شامل هیچ کار اجرایی مستقیمی نمی‌شود. وظیفه آن اطلاع‌رسانی درباره احتمال وجود پیاده‌سازی قبلی، لزوم بررسی مستقل repo، و مسئولیت مدل در قبال تشخیص صحیح موقعیت فایل‌ها و کامل بودن پیاده‌سازی است. این بخش صراحتاً می‌گوید که پرامپت ممکن است اشتباه باشد و مدل باید بر اساس قضاوت خود عمل کند. هیچ مرحله اجرایی (تغییر کد، ایجاد فایل، یا تست) در این بخش تعریف نشده است.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 19: رفع مشکل stuck شدن داشبورد در حالت loading به دلیل عدم وجود ستون amount در جدول facilities
**Status:** `done` (100%)
**Scope:** این بخش شامل رفع باگ اصلی است که باعث می‌شود داشبورد در حالت loading بی‌نهایت بماند. علت ریشه‌ای: عدم وجود ستون 'amount' در جدول facilities که منجر به خطای 500 در endpoint stats می‌شود. راه‌حل: افزودن ستون amount از طریق migration موجود (002_add_missing_columns.py) و اصلاح هندلینگ خطا در frontend. این بخش شامل اصلاح کامل backend و frontend است. خارج از scope: سایر باگ‌های احتمالی داشبورد، بهبود UI، یا تغییرات معماری.
**Excerpt:**
```
Dashboard page stuck in infinite loading state due to missing 'amount' column in facilities table

- `frontend/src/app/dashboard/page.tsx:75-99` — `loading state` — Loading state never transitions to error state if fetch fails
  ```tsx
  if (loading) {
      return (
        <div className="container mx-auto p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <Button variant="outline" disabled>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </Button>
          </div>
          ...
        </div>
      );
    }
  ```
- `backend/app/routers/stats.py:1-50` — `dashboard stats endpoint` — Endpoint likely queries facilities.amount which may be missing
  ```python
  // Not provided but referenced in DATABASE_SCHEMA.md as causing 500 error
  ```

Dashboard page depends on stats endpoint which depends on facilities table schema. Missing column breaks the entire dashboard.

The dashboard page (`frontend/src/app/dashboard/page.tsx`) fetches data from `/api/stats/dashboard` and shows a loading spinner indefinitely. The backend endpoint `backend/app/routers/stats.py` likely queries the `facilities` table for the `amount` column to calculate `monthly_revenue`. According to `docs/DATABASE_SCHEMA.md`, the `amount` column is critical for dashboard calculations and its absence causes a 500 error. The frontend's error handling (lines 40-55) catches this but the UI remains stuck on the loading state because the error state is not properly rendered when `loading` is true.
```

### Step 20: پیاده‌سازی معیارهای پذیرش برای مدیریت خطا و همگام‌سازی نمایش داده‌ها در داشبورد
**Status:** `done` (100%)
**Scope:** این مرحله شامل پیاده‌سازی کامل معیارهای پذیرش (AC) برای بخش خطا و بارگذاری مجدد داشبورد است. شامل: (1) اطمینان از وجود ستون amount در جدول facilities از طریق اجرای مهاجرت Alembic، (2) رفع مدیریت خطا در frontend/src/app/dashboard/page.tsx برای نمایش پیام خطا به جای اسپینر بی‌نهایت، (3) افزودن مکانیزم timeout برای جلوگیری از بارگذاری بی‌نهایت. خارج از scope: سایر بخش‌های داشبورد، تست‌های واحد (فقط اجرای تست‌ها برای اطمینان از عدم شکست)، linting و type-checking (فقط اطمینان از عبور). نکته حیاتی: تمام ACها باید به صورت رفتار قابل مشاهده پیاده‌سازی شوند و نام فایل‌ها/کلاس‌ها دقیقاً از لیست داده شده استفاده شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] Dashboard shows error message when API call fails instead of infinite spinner
- [ ] User can click 'Try Again' button to retry the API call
- [ ] Backend returns proper error response when amount column is missing
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. Ensure the `amount` column exists in the `facilities` table by running the Alembic migration. 2. Fix the frontend error handling in `frontend/src/app/dashboard/page.tsx` to properly display the error state when loading fails. 3. Add a timeout mechanism to break out of infinite loading.
```

### Step 21: رفع وضعیت بارگذاری برای نمایش خطا به جای اسپینر بی‌پایان
**Status:** `pending` (0%)
**Scope:** این مرحله فقط تغییر شرط نمایش کامپوننت LoadingSpinner را پوشش می‌دهد تا در صورت وجود error، به جای اسپینر، ErrorState با پیام خطا و دکمه تلاش مجدد نمایش داده شود. خارج از scope: تغییرات دیگر در منطق بارگذاری، مدیریت state خطا در سطح بالاتر، یا تغییر ظاهر کامپوننت‌ها.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**Fix loading state to show error**

_قبل:_
```
if (loading) { return <LoadingSpinner /> }
```

_بعد:_
```
if (loading && !error) { return <LoadingSpinner /> }
if (error) { return <ErrorState message={error} onRetry={handleRefresh} /> }
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 22: رفع استفاده از کامپوننت‌های UI تعریف‌نشده در داشبورد
**Status:** `done` (100%)
**Scope:** این بخش شامل رفع باگ‌های مربوط به کامپوننت‌های UI تعریف‌نشده در داشبورد است. تغییرات باید بدون شکستن تست‌های موجود، عبور از linter و type-check انجام شود. فایل‌های دخیل مشخص نیستند اما احتمالاً frontend/src/app/dashboard/page.tsx و کامپوننت‌های UI مرتبط هستند.
**Excerpt:**
```
تسک 5 از 5
  id: 9a50880a-ea5f-4482-867a-cefb621cbffb
  عنوان اصلی: رفع استفاده از کامپوننت‌های UI تعریف‌نشده در داشبورد
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": ".", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "lint", "timeout_seconds": 60}]
  - type-check موفق است [verify_method=backend_test] [verify_plan={"test_node": "typecheck", "timeout_seconds": 60}]
```

### Step 23: بررسی اولیه خودکار و پیش‌نیازهای اجرایی برای رفع باگ‌ها و همگام‌سازی نمایش داده‌ها در داشبورد
**Status:** `done` (100%)
**Scope:** این بخش شامل دستورالعمل‌های پیش‌اجرایی برای مدل اجراکننده است: بررسی وجود پیاده‌سازی قبلی، جستجوی فایل‌های مرتبط، و تصمیم‌گیری در مورد نیاز به تغییر. این بخش خود یک مرحله اجرایی نیست، بلکه یک یادداشت هشداردهنده برای جلوگیری از کار تکراری یا اشتباه است. هیچ کد جدیدی در این مرحله تولید نمی‌شود، فقط تحلیل و تصمیم‌گیری صورت می‌گیرد. خروجی این بخش می‌تواند 'skip' باشد اگر همه چیز از قبل درست پیاده‌سازی شده باشد.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 24: ایجاد کامپوننت‌های UI تعریف‌نشده در صفحه داشبورد
**Status:** `pending` (0%)
**Scope:** این بخش شامل ایجاد فایل‌های کامپوننت UI برای Card, CardContent, CardHeader, CardTitle, Button, Skeleton, Alert, AlertDescription در مسیرهای مشخص شده است. خارج از scope: تغییر منطق صفحه داشبورد، اصلاح backend، یا ایجاد کامپوننت‌های دیگر. نکته حیاتی: کامپوننت‌ها باید با shadcn/ui یا معادل آن مطابقت داشته باشند و از tailwindcss استفاده کنند.
**Excerpt:**
```
فایل `frontend/src/app/dashboard/page.tsx` (خطوط 2-5) کامپوننت‌هایی مانند `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Button`, `Skeleton`, `Alert`, `AlertDescription` را از مسیرهای `@/components/ui/card`, `@/components/ui/button`, `@/components/ui/skeleton`, `@/components/ui/alert` import می‌کند. این کامپوننت‌ها در ساختار پروژه وجود ندارند و باعث خطای build و runtime می‌شوند.
```

### Step 25: تبدیل معیارهای پذیرش و مراحل اجرایی به یک مرحله اجرایی برای رفع باگ و همگام‌سازی نمایش داده‌ها در داشبورد
**Status:** `done` (100%)
**Scope:** این مرحله شامل اعمال تغییرات کد در فایل‌های مرتبط با رفع باگ‌ها و همگام‌سازی نمایش داده‌ها در داشبورد است. معیارهای پذیرش شامل عدم شکستن تست‌های موجود، عبور linter بدون warning، موفقیت type-check، و عدم fail شدن هیچ تستی است. مراحل اجرایی باید بر اساس Context و معیارهای پذیرش تعیین شوند. خروجی مورد انتظار تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش است.
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

## 🪜 مراحل اجرایی پیشنهادی
_(مجری بر اساس Context و معیارهای پذیرش، مراحل را تعیین کند)_

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 26: اجرای تست‌های موجود پیش از merge برای جلوگیری از رگرشن
**Status:** `done` (100%)
**Scope:** این بخش صرفاً شامل اجرای تست‌های موجود در پروژه (مانند tests/test_stats.py, backend/tests/test_facilities.py, backend/tests/test_dashboard.py) پیش از انجام merge است. هیچ کد جدیدی نوشته نمی‌شود و هیچ تغییری در فایل‌های اصلی اعمال نمی‌گردد. هدف صرفاً اطمینان از عدم شکستن عملکردهای فعلی (regression) است. این مرحله یک گام احتیاطی (pre-merge check) است و بخشی از فرآیند توسعه یا رفع باگ محسوب نمی‌شود.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)
```
