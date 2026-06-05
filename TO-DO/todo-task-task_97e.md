# TODO — Task task_97e (نیاز به تکمیل دستی)

> **افزایش پوشش تست و کیفیت کد بک‌اند**

## 🔎 خلاصه وضعیت

- **task_id**: `task_97e9c7c534d9`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.92
- **verifier model**: `—`
- **report_id**: `fe8114c5-0191-4037-aa32-007c79c745c0`
- **created_at**: 2026-06-05T01:09:05.737614+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] پوشش کد (coverage) حداقل 80% نیست (روی 70% تنظیم شده)
- [ ] backward-compat layer برای تغییر default value user_id اضافه نشده
- [ ] فایل compat.py برای backward compatibility ایجاد نشده
- [ ] فایل offer_letter.py هنوز حذف نشده (فقط از main.py رفرنس حذف شده)
- [ ] تست‌های مربوط به offer_letter.py حذف نشده‌اند
- [ ] مستندسازی offer_letter.py در README انجام نشده
- [ ] بررسی entry point بودن offer_letter.py در CI/CD مستند نشده
- [ ] اجرای py_compile و ruff روی offer_letter.py انجام نشده
- [ ] اجرای linter و type-check برای backend (ruff/mypy) مستند نشده

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. افزایش coverage gate به 80% یا مستندسازی دلیل عدم امکان
2. ایجاد backend/app/compat.py برای backward compatibility در صورت نیاز
3. حذف فیزیکی فایل offer_letter.py و تست‌های مربوطه
4. اجرای ruff و mypy روی backend و ثبت نتایج
5. مستندسازی وضعیت offer_letter.py در README

## ✅ چه چیزی Claude انجام داد

- [x] ساختار دایرکتوری tests/ و فایل‌های تست پایه ایجاد شده
- [x] تست‌های واحد برای models و schemas (user_id) نوشته شده
- [x] تست‌های یکپارچگی برای API endpoints تا 70% پیشرفت
- [x] تست‌های امنیتی (SQL Injection, XSS, JWT) پیاده‌سازی شده
- [x] GitHub Actions برای اجرای خودکار تست‌ها تنظیم شده
- [x] تست‌ها در CI/CD بدون شکستن تست‌های موجود عبور می‌کنند
- [x] linter و type-check برای frontend بدون warning عبور می‌کنند
- [x] user_id از یک منبع واحد (generate_id) default می‌گیرد
- [x] تست fixture رفتار پیش‌فرض user_id را تأیید می‌کند
- [x] ریشه anti-pattern (SSL, user_id) تشخیص داده شده
- [x] anti-pattern SSL در database.py اصلاح و مستند شده
- [x] تست edge case برای SSL configuration نوشته شده
- [x] فایل offer_letter.py از main.py حذف (dead code) شده
- [x] PR description با merged-from IDs و checklist ایجاد شده
- [x] ✓ ایجاد ساختار دایرکتوری tests/ و فایل‌های تست پایه برای backend (code-aware: implemented)
- [x] ✓ نوشتن تست‌های واحد برای models و schemas backend (code-aware: implemented)
- [x] ✓ تنظیم GitHub Actions برای اجرای خودکار تست‌ها (code-aware: implemented)
- [x] ✓ بررسی و هماهنگ‌سازی وابستگی‌های requirements.txt با pyproject.toml (code-aware: implemented)
- [x] ✓ اجرای تست‌های موجود برای اطمینان از عدم شکستن پس از تغییر وابستگی‌ها (code-aware: implemented)
- [x] ✓ اجرای linter و type-check برای اطمینان از عدم وجود warning (code-aware: implemented)
- [x] ✓ شناسایی تمام مکان‌های دارای default متفاوت برای فیلد user_id (code-aware: implemented)
- [x] ✓ انتخاب یک منبع واحد برای default value فیلد user_id (code-aware: implemented)
- [x] ✓ نوشتن تست fixture برای تأیید رفتار پیش‌فرض user_id (code-aware: implemented)
- [x] ✓ بررسی و تشخیص ریشه anti-pattern در backend/app/database.py (code-aware: implemented)
- [x] ✓ اصلاح یا مستندسازی anti-pattern در backend/app/database.py (code-aware: implemented)
- [x] ✓ نوشتن تست edge case برای SSL configuration در test_database.py (code-aware: implemented)
- [x] ✓ اجرای py_compile و ruff check روی backend/app/database.py (code-aware: implemented)
- [x] ✓ بررسی وضعیت فایل offer_letter.py با grep روی importها (code-aware: implemented)
- [x] ✓ بررسی entry point بودن offer_letter.py در CI/CD و scripts (code-aware: implemented)
- [x] ✓ اجرای کامل pytest برای اطمینان از عدم شکستن تست‌ها پس از تغییرات (code-aware: implemented)
- [x] ✓ بررسی و رفع warningهای linter در تمام فایل‌های تغییر یافته (code-aware: implemented)
- [x] ✓ بررسی و رفع warningهای type-check در تمام فایل‌های تغییر یافته (code-aware: implemented)
- [x] ✓ نوشتن commit message با merged-from IDs (code-aware: implemented)
- [x] ✓ ایجاد PR description با checklist از تمام کامیت‌ها (code-aware: implemented)
- [x] ✓ بررسی نهایی و merge تغییرات (code-aware: implemented)
- [x] ✓ نوشتن release note برای تغییرات اعمال‌شده (code-aware: implemented)

## 📝 خلاصهٔ verifier

بیشتر معیارهای پذیرش (13 از 15) برآورده شده‌اند. تست‌ها، CI/CD، linter، type-check، یکپارچگی user_id، تشخیص anti-pattern و اصلاح SSL انجام شده. دو معیار اصلی باقی‌مانده: پوشش کد 80% (فعلاً 70%) و backward-compat layer برای user_id. همچنین پاکسازی کامل offer_letter.py ناقص است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد
- پوشش کد (coverage) حداقل 80% باشد
- تست‌ها در CI/CD به صورت خودکار اجرا شوند
- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است
- `user_id` در همه‌جا از یک منبع default می‌گیرد
- تست fixture رفتار پیش‌فرض را تأیید می‌کند
- اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد
- ریشه anti-pattern تشخیص داده شد
- یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- تست edge case نوشته شد
- مشخص شد فایل dead است یا entry point/dynamic
- اقدام مناسب: حذف یا مستندسازی
- تست‌های مربوطه (در صورت حذف) هم حذف شدند

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `b9dac6d`
- `ac48046`
- `2c17fe9`
- `b4fe120`
- `81e9eb1`
- `8b11f67`
- `6958c83`
- `8c72366`

**Files lams شده:**
- `backend/tests/test_defaults.py`
- `backend/tests/test_database.py`
- `backend/tests/test_security.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_customers.py`
- `backend/tests/test_facilities.py`
- `backend/tests/conftest.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `docs/TASK_STATUS.md`
- `PR_DESCRIPTION.md`
- `.github/workflows/ci.yml`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 5 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی بهبود کلی زیرساخت بک‌اند، شامل پیاده‌سازی تست‌های واحد و یکپارچگی، همگام‌سازی وابستگی‌های پایتون، یکپارچه‌سازی فیلدهای پیش‌فرض، رفع الگوهای ضد-طراحی (anti-pattern) و پاکسازی کدهای بلااستفاده یا قدیمی تمرکز دارند. این موارد به پایداری و قابلیت نگهداری کد کمک می‌کنند.
🎯 theme: نگهداری و بهبود زیرساخت بک‌اند
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 5
  id: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9
  عنوان اصلی: پیاده‌سازی تست‌های واحد و یکپارچگی بک‌اند
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/pyproject.toml, backend/tests/

📋 acceptance_criteria کامل:
  - حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/", "timeout_seconds": 120}]
  - پوشش کد (coverage) حداقل 80% باشد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی"}]
  - تست‌ها در CI/CD به صورت خودکار اجرا شوند [verify_method=static] [verify_plan={"grep_patterns": ["pytest", "run:", "script:"], "files_hint": [".github/workflows/*.yml", ".gitlab-ci.yml", "Jenkinsfile"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل

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