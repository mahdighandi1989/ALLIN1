# TODO — Task task_bd8 (نیاز به تکمیل دستی)

> **افزایش پایداری و اعتبارسنجی پایپلاین اکسل**

## 🔎 خلاصه وضعیت

- **task_id**: `task_bd83a960a6ab`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 1
- **verifier confidence**: 0.85
- **verifier model**: `—`
- **report_id**: `4d212b37-11a0-495d-81a6-9d3bf0810351`
- **created_at**: 2026-06-05T00:41:14.485033+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] تست‌های unit برای validation schema (مرحله 12) ناقص است
- [ ] تست‌های unit برای کامپوننت‌های اصلاح‌شده pipeline (مرحله 19) ناقص است
- [ ] کتابخانه‌های openpyxl و xlrd به وابستگی‌ها اضافه نشده (مرحله 21)
- [ ] تست‌های unit برای handlerهای جدید (مرحله 27) یافت نشد
- [ ] قابلیت اجرای macro برای فایل‌های .xlsm (مرحله 25 و 26) پیاده‌سازی نشده
- [ ] تست integration واقعی pipeline داده با pytest خطای داخلی داده (rc=4)

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. رفع خطای pytest در test_data_pipeline.py::test_integration
2. اضافه کردن تست‌های unit برای validation schema (مرحله 12)
3. اضافه کردن تست‌های unit برای کامپوننت‌های اصلاح‌شده pipeline (مرحله 19)
4. اضافه کردن openpyxl و xlrd به requirements.txt (مرحله 21)
5. نوشتن تست‌های unit برای handlerهای جدید read_xlsm_file و read_xls_file (مرحله 27)

## ✅ چه چیزی Claude انجام داد

- [x] ناسازگاری‌های pipeline داده شناسایی و در ADR-004 مستند شده
- [x] ground truth (fail-closed typed reader) تعیین و طرف دیگر align شده
- [x] تست‌های integration برای pipeline داده در test_data_pipeline.py و test_pipeline_data.py پیاده‌سازی شده
- [x] PR description در PR_DESCRIPTION.md توضیح تصمیمات را داده
- [x] مراحل 1 تا 11 و 13 تا 24 و 27 تا 31 بر اساس شواهد code-aware انجام شده
- [x] مستندات ADR-004 و docs/decisions به‌روز شده

## 📝 خلاصهٔ verifier

بخش عمده تسک (مستندسازی ناسازگاری‌ها، تعیین ground truth، align کردن طرف دیگر، تست‌های integration و مستندسازی) انجام شده. اما ۶ آیتم باقی مانده: تست‌های unit ناقص، وابستگی‌های کتابخانه‌ای اضافه نشده، قابلیت اجرای macro پیاده‌سازی نشده، و تست integration با خطای pytest مواجه شده.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- ground truth تعیین شد و طرف دیگر align شد
- integration test برای pipeline `data` بدون شکست عبور می‌کند
- PR description توضیح می‌دهد چرا این تصمیم گرفته شد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `b9caf1b`
- `2c17fe9`
- `f8f6681`

**Files lams شده:**
- `docs/decisions/ADR-004-excel-data-pipeline.md`
- `PR_DESCRIPTION.md`
- `backend/tests/test_data_pipeline.py`
- `backend/tests/test_pipeline_data.py`
- `backend/app/services/data_pipeline.py`

**Issues:**
- pytest internal error (rc=4) در test_data_pipeline.py::test_integration

## 💡 ایدهٔ اصلی تسک

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
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["why", "decision", "rationale", "reason"], "files_hint": [

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