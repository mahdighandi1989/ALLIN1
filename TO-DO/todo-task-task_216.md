# TODO — Task task_216 (نیاز به تکمیل دستی)

> **پیاده‌سازی Rate Limit و رفع JWT احراز هویت**

## 🔎 خلاصه وضعیت

- **task_id**: `task_21687b9591ca`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.92
- **verifier model**: `—`
- **report_id**: `303273ed-6696-4d7e-8e30-47d0e5f03e4b`
- **created_at**: 2026-06-05T18:28:53.174458+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] تست واحد (unit test) برای rate limiting اضافه نشده
- [ ] type-check موفق تأیید نشده
- [ ] diff frontend/src/lib/axios.ts بررسی و تأثیر بر auth.tsx مستند نشده
- [ ] بررسی و تطبیق auth.tsx با تغییرات axios.ts انجام نشده
- [ ] بررسی مصرف env var در CI/CD و Dockerfile/Render config ناقص است

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. اضافه کردن تست واحد (unit test) برای منطق rate limiter
2. اجرای type-checker و رفع خطاهای احتمالی
3. بررسی diff فایل frontend/src/lib/axios.ts و مستندسازی تأثیر بر auth.tsx
4. تطبیق auth.tsx با تغییرات axios.ts برای جلوگیری از regression
5. بررسی کامل CI/CD pipeline و Dockerfile/Render config برای env varهای مصرفی

## ✅ چه چیزی Claude انجام داد

- [x] Rate limiter با Redis و fallback in-memory پیاده‌سازی شده
- [x] endpoint /api/auth/login بعد از ۵ تلاش ناموفق ۴۲۹ برمی‌گرداند
- [x] تغییرات بدون شکستن تست‌های موجود اعمال شده
- [x] linter بدون warning عبور می‌کند
- [x] ریشه anti-pattern تشخیص داده شده
- [x] کد اصلاح یا کامنت توجیهی اضافه شده
- [x] تست edge case نوشته شده
- [x] هر دو طرف ناسازگاری شناسایی و مستند شده
- [x] ground truth تعیین و طرف دیگر align شده
- [x] integration test برای pipeline auth بدون شکست عبور می‌کند
- [x] PR description توضیح تصمیمات را داده
- [x] کد dependent با contract جدید align شده
- [x] integration test پوشش‌دهنده هر دو فایل عبور می‌کند
- [x] ACCESS_TOKEN_EXPIRE_MINUTES در هیچ کدی خوانده نمی‌شود
- [x] ACCESS_TOKEN_EXPIRE_MINUTES از .env.example حذف شده
- [x] اگر secret بوده، rotate و مقدار جدید تنظیم شده
- [x] رفع آسیب‌پذیری بایپس موقت احراز هویت در auth.py
- [x] اصلاح anti-pattern در احراز هویت با تست edge case
- [x] Clarify Auth Granularity برای پروفایل/رمز عبور
- [x] اعمال granularity مجوز برای به‌روزرسانی پروفایل
- [x] تعریف معیارهای پذیرش برای رفع ناسازگاری pipeline auth
- [x] Return Consistent 401 برای خطاهای لاگین
- [x] رفع نشت اطلاعات endpoint ورود از طریق کد وضعیت HTTP
- [x] حذف متغیر محیطی بلااستفاده ACCESS_TOKEN_EXPIRE_MINUTES

## 📝 خلاصهٔ verifier

بیشتر معیارهای پذیرش (19 از 24) برآورده شده‌اند. rate limiter با Redis و fallback in-memory پیاده‌سازی شده، تست‌های integration و edge case اضافه شده، anti-pattern‌ها تشخیص و اصلاح شده‌اند، و متغیر بلااستفاده ACCESS_TOKEN_EXPIRE_MINUTES حذف شده. اما تست واحد (unit test) برای rate limiting، type-check، بررسی تأثیر تغییرات axios.ts بر auth.tsx، و بررسی کامل env varها در CI/CD باقی مانده است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- endpoint /api/auth/login بعد از ۵ درخواست ناموفق در ۶۰ ثانیه ۴۲۹ Too Many Requests برگرداند
- rate limiter از Redis استفاده کند (fallback به in-memory)
- تست واحد برای rate limiting اضافه شود
- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است
- ریشه anti-pattern تشخیص داده شد
- یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- تست edge case نوشته شد
- هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- ground truth تعیین شد و طرف دیگر align شد
- integration test برای pipeline `auth` بدون شکست عبور می‌کند
- PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- diff `frontend/src/lib/axios.ts` بررسی شد و تأثیر بر `frontend/src/lib/auth.tsx` مستند شد
- کد dependent با contract جدید align شد
- integration test که هر دو فایل را پوشش می‌دهد عبور می‌کند
- `ACCESS_TOKEN_EXPIRE_MINUTES` در هیچ کدی خوانده نمی‌شود (تأیید شده)
- از `.env.example` و deployment configs حذف شد
- اگر secret بوده، rotate شد و در deployment new value تنظیم شد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `754abeb`
- `0738792`
- `53559c2`
- `f73109c`
- `5e8a03a`
- `09a8ad2`
- `8a04170`

**Files lams شده:**
- `backend/app/utils/rate_limit.py`
- `backend/tests/integration/test_auth_rate_limit.py`
- `backend/tests/unit/test_rate_limit.py`
- `backend/tests/security/test_auth_bypass_edge_cases.py`
- `backend/tests/integration/test_auth_granularity.py`
- `backend/.env.example`
- `backend/app/config.py`
- `backend/app/models/user.py`
- `backend/app/routers/auth.py`
- `backend/app/utils/security.py`
- `backend/tests/test_config_security.py`
- `backend/tests/backend/app/models/test_user_uuid.py`
- `docs/TASK_STATUS.md`
- `pull_request_description.md`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 7 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به طور مستقیم به تقویت مکانیزم‌های احراز هویت، رفع آسیب‌پذیری‌های امنیتی (مانند اعتبارسنجی JWT و الگوهای ضدامنیتی)، بهبود یکپارچگی خطاهای ورود و همگام‌سازی احراز هویت فرانت‌اند با بک‌اند مربوط می‌شوند. پیاده‌سازی rate limiting یک ویژگی امنیتی حیاتی است و حذف متغیر محیطی بلااستفاده نیز به پیکربندی امنیتی مرتبط است.
🎯 theme: تقویت سیستم احراز هویت و امنیت بک‌اند و فرانت‌اند
💎 estimated_difficulty: large

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 7
  id: a13ae0e8-48bd-45f7-b4c5-84144db25f7d
  عنوان اصلی: پیاده‌سازی rate limiting برای endpoint‌های احراز هویت
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/main.py

📋 acceptance_criteria کامل:
  - endpoint /api/auth/login بعد از ۵ درخواست ناموفق در ۶۰ ثانیه ۴۲۹ Too Many Requests برگرداند [verify_method=backend_test] [verify_plan={"test_node": "tests/integration/test_auth_rate_limit.py::test_login_rate_limiting_too_many_requests", "timeout_seconds": 60}]
  - rate limiter از Redis استفاده کند (fallback به in-memory) [verify_method=static] [verify_plan={"grep_patterns": ["redis", "Redis", "in_memory", "InMemoryRateLimiter", "rate_limit.py"], "files_hint": ["backend/app/main.py", "backend/app/utils/rate_limit.py"]}]
  - تست واحد برای rate limiting اضافه شود [verify_method=backend_test] [verify_plan={"test_node": "tests/unit/test_rate_limit.py::test_rate_limiting_logic", "timeout_seconds": 60}]

📝 idea_p

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