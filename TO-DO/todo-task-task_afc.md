# TODO — Task task_afc (نیاز به تکمیل دستی)

> **رفع باگ‌ها و همگام‌سازی نمایش داده‌ها در داشبورد**

## 🔎 خلاصه وضعیت

- **task_id**: `task_afcee9e1c044`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.95
- **verifier model**: `—`
- **report_id**: `c5806240-8250-4d84-87e7-27f93dfea26a`
- **created_at**: 2026-06-04T23:37:57.305836+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] در حالت static export پیام 'Dashboard data unavailable in static mode' نشان داده نمی‌شود

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. بررسی و پیاده‌سازی نمایش پیام 'Dashboard data unavailable in static mode' در حالت static export

## ✅ چه چیزی Claude انجام داد

- [x] صفحه dashboard داده‌های واقعی را نمایش می‌دهد و spinner ابدی رفع شده است
- [x] در صورت خطا، پیام خطای مناسب با دکمه Try Again به کاربر نشان داده می‌شود
- [x] صفحات customers و facilities داده‌های واقعی را نمایش می‌دهند
- [x] endpoint /api/stats/dashboard response با interface DashboardStats مطابقت دارد
- [x] ستون amount در جدول facilities وجود دارد و NOT NULL است
- [x] dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند
- [x] تست واحد برای endpoint dashboard اضافه شده است
- [x] صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش می‌دهد
- [x] در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده می‌شود
- [x] دکمه Refresh داده‌ها را دوباره بارگذاری می‌کند
- [x] Dashboard به جای spinner بی‌نهایت پیام خطا نشان می‌دهد
- [x] کاربر می‌تواند روی دکمه Try Again کلیک کند تا API دوباره فراخوانی شود
- [x] Backend در صورت نبود ستون amount پاسخ خطای مناسب برمی‌گرداند
- [x] تغییرات بدون شکستن تست‌های موجود اعمال شده است
- [x] linter بدون warning عبور می‌کند
- [x] type-check موفق است

## 📝 خلاصهٔ verifier

16 از 17 معیار پذیرش برآورده شده است. تنها معیار باقی‌مانده نمایش پیام 'Dashboard data unavailable in static mode' در حالت static export است که در کد فعلی پیاده‌سازی نشده است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- صفحه dashboard داده‌های واقعی را نمایش دهد (نه spinner)
- در صورت خطا، پیام خطای مناسب به کاربر نشان داده شود
- صفحات customers و facilities نیز داده‌ها را نمایش دهند
- endpoint /api/stats/dashboard response دقیقاً با interface DashboardStats مطابقت دارد
- ستون amount در جدول facilities وجود دارد و NOT NULL است
- dashboard صفحه بدون خطا لود می‌شود و داده‌ها نمایش داده می‌شوند
- تست واحد برای endpoint اضافه شود
- صفحه Dashboard داده‌های واقعی را از API دریافت و نمایش دهد
- در صورت خطای 500، پیام خطای مناسب به کاربر نشان داده شود
- دکمه Refresh دوباره داده‌ها را بارگذاری کند
- در حالت static export، یک پیام 'Dashboard data unavailable in static mode' نشان داده شود
- Dashboard shows error message when API call fails instead of infinite spinner
- User can click 'Try Again' button to retry the API call
- Backend returns proper error response when amount column is missing
- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `30ffeb1`
- `5a1db49`
- `d0b7e4e`
- `d4a9843`
- `ee926b4`
- `d7b9c5f`
- `8f09a33`

**Files lams شده:**
- `backend/app/routers/stats.py`
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/app/facilities/page.tsx`
- `frontend/src/app/customers/page.tsx`
- `backend/tests/test_stats.py`
- `frontend/.eslintrc.json`

## 💡 ایدهٔ اصلی تسک

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
  - صفحات customers و facilities نیز داده‌ها را نمایش دهند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action": "navigate", "url": "/

## 📜 پرامپت اصلی (excerpt)

```
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
  با

_[truncated — full prompt در پنل]_
```

---

_این فایل توسط Claude Auto-Runner تولید شده است. تسک با حالت_ `max_retries` _آرشیو شده و دیگر به‌صورت خودکار pickup نمی‌شود._