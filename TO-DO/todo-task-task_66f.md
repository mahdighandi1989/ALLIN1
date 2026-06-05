# TODO — Task task_66f (نیاز به تکمیل دستی)

> **تست نشت دسترسی در خطاهای API**

## 🔎 خلاصه وضعیت

- **task_id**: `task_66febcc9ff9a`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.98
- **verifier model**: `—`
- **report_id**: `b1d40e55-7b0b-4dec-aec0-ec7a0e3146bc`
- **created_at**: 2026-06-05T00:26:35.103156+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] outcome target به‌صورت measurable بازنویسی شد
- [ ] کد تغییر کرد تا outcome target محقق شود
- [ ] test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- [ ] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد
- [ ] اعمال تغییر بدون شکستن تست‌های موجود

## ✅ چه چیزی Claude انجام داد

- [x] outcome target به صورت measurable بازنویسی شد (PR_DESCRIPTION.md)
- [x] کد تغییر کرد تا outcome target محقق شود (customers/page.tsx)
- [x] test E2E که outcome را اندازه می‌گیرد عبور می‌کند (pytest backend/tests)
- [x] metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد (security.py)
- [x] اعمال تغییر بدون شکستن تست‌های موجود (pytest backend/tests passes)
- [x] linter بدون warning عبور می‌کند (ESLint config اضافه شد)
- [x] type-check موفق است (tsc --noEmit passes)
- [x] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد (PR_DESCRIPTION.md)
- [x] ground truth تعیین شد و طرف دیگر align شد (server as ground truth)
- [x] integration test برای pipeline auth بدون شکست عبور می‌کند (test_auth_pipeline.py)
- [x] PR description توضیح می‌دهد چرا این تصمیم گرفته شد (PR_DESCRIPTION.md)

## 📝 خلاصهٔ verifier

تمامی 11 معیار پذیرش تسک پیاده‌سازی تست‌های امنیتی احراز هویت در وضعیت فعلی پروژه برآورده شده‌اند. شواهد code-aware و محتوای PR_DESCRIPTION.md و کامیت‌های اخیر نشان می‌دهند که outcome target measurable بازنویسی شده، کد تغییر کرده، تست‌ها عبور می‌کنند، metric/log اضافه شده، linter و type-check پاس هستند، ناسازگاری‌ها مستند و align شده‌اند، و PR description تصمیمات را توضیح می‌دهد.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- outcome target به‌صورت measurable بازنویسی شد
- کد تغییر کرد تا outcome target محقق شود
- test E2E که outcome را اندازه می‌گیرد عبور می‌کند
- metric/log اضافه شد تا در production outcome rate قابل تشخیص باشد
- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است
- هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- ground truth تعیین شد و طرف دیگر align شد
- integration test برای pipeline `auth` بدون شکست عبور می‌کند
- PR description توضیح می‌دهد چرا این تصمیم گرفته شد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `b4fe120`
- `2a4bc56`
- `4f6a3a7`
- `762a533`
- `8f09a33`

**Files lams شده:**
- `PR_DESCRIPTION.md`
- `frontend/src/app/customers/page.tsx`
- `backend/app/utils/security.py`
- `backend/app/monitoring.py`
- `backend/tests/test_security.py`
- `backend/tests/integration/test_auth_pipeline.py`
- `frontend/.eslintrc.json`

## 💡 ایدهٔ اصلی تسک

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

📝 i

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