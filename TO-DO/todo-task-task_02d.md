# TODO — Task task_02d (نیاز به تکمیل دستی)

> **تکمیل مانیتورینگ خطا و عملکرد سیستم**

## 🔎 خلاصه وضعیت

- **task_id**: `task_02dfbac2d524`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.98
- **verifier model**: `—`
- **report_id**: `f657fb8f-7ccf-40bf-b935-fda5d3614af2`
- **created_at**: 2026-06-05T01:20:15.907153+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد

## ✅ چه چیزی Claude انجام داد

- [x] outcome target به صورت measurable بازنویسی شد (کامیت 69f4a99)
- [x] کد تغییر کرد تا outcome target محقق شود (MetricsMiddleware, structlog)
- [x] تست E2E برای اندازه‌گیری outcome نوشته و عبور می‌کند (test_global_exception_handling.py)
- [x] metric/log برای تشخیص outcome rate در production اضافه شد (Prometheus, structlog)

## 📝 خلاصهٔ verifier

تمام معیارهای پذیرش تسک تکمیل مانیتورینگ خطا و عملکرد سیستم برآورده شده است. outcome target بازنویسی، کد تغییر، تست E2E عبور می‌کند و metric/log برای production اضافه شده است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- outcome target به‌صورت measurable بازنویسی شد
- کد تغییر کرد تا outcome target محقق شود
- test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `69f4a99`
- `b9dac6d`
- `7ba9a16`
- `2ad0d4e`
- `2c17fe9`

**Files lams شده:**
- `backend/app/main.py`
- `backend/app/middleware.py`
- `backend/app/monitoring.py`
- `backend/tests/e2e/test_global_exception_handling.py`
- `backend/tests/e2e/test_performance.py`
- `docs/OBSERVABILITY.md`
- `prompt/task-task_02dfbac2d524.md`

## 💡 ایدهٔ اصلی تسک

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
  - metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/simulate-unhandled-error", "headers": null, "json_body": null, "expected_status": 500, "required_fields": ["error_id"

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