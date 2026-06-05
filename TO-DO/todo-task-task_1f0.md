# TODO — Task task_1f0 (نیاز به تکمیل دستی)

> **تقویت امنیت JWT و مکانیزم‌های احراز هویت**

## 🔎 خلاصه وضعیت

- **task_id**: `task_1f0f55a17f45`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 1
- **verifier confidence**: 0.00
- **verifier model**: `—`
- **report_id**: `7746dc33-88f5-490a-9f85-425d6b1be02e`
- **created_at**: 2026-06-05T00:16:26.764319+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] تنظیم AUTH_DISABLED هنوز در settings وجود دارد و حذف نشده
- [ ] HSTS header با max-age=31536000 در پاسخ‌ها وجود ندارد
- [ ] CORS فقط دامنه‌های مجاز را اجازه نمی‌دهد (پیکربندی نشده)
- [ ] در production HTTP به HTTPS redirect نمی‌شود
- [ ] PR description توضیح نمی‌دهد چرا این تصمیم گرفته شد
- [ ] Rate limiting با Redis برای cross-process پیاده‌سازی نشده (فقط in-memory)
- [ ] Middleware مسدودکننده AUTH_DISABLED در production اضافه نشده

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. حذف کامل AUTH_DISABLED از settings و کد backend
2. افزودن HSTS middleware با max-age=31536000 در main.py
3. پیکربندی CORS برای محدود کردن دامنه‌های مجاز
4. افزودن redirect HTTP به HTTPS در production
5. نوش

## ✅ چه چیزی Claude انجام داد

- [x] ورودی‌های نامعتبر با خطای 422 رد می‌شوند (Pydantic validation + manual checks)
- [x] فیلدهای متنی محدودیت طول دارند (min_length/max_length در Pydantic models)
- [x] الگوهای regex برای فیلدهای حساس اعمال شده (pattern در Field)
- [x] توکن با الگوریتم none توسط middleware رد می‌شود (JWT security hardening)
- [x] کلید JWT از متغیر محیطی خوانده می‌شود (JWT security hardening)
- [x] تمامی تست‌های احراز هویت با موفقیت پاس می‌شوند (verify commits)
- [x] در production خطاهای 500 پیام generic نمایش می‌دهند (no-leak errors)
- [x] لاگ‌ها حاوی password یا token نیستند (no-leak errors)
- [x] exception handler تمام استثناها را catch می‌کند (global exception handler)
- [x] بدون توکن JWT معتبر endpoint /api/customers خطای 401 برمی‌گرداند (auth enforcement)
- [x] پس از logout توکن در blacklist قرار می‌گیرد (token_blacklist.py)
- [x] endpoint /auth/refresh وجود دارد و کار می‌کند (JWT security hardening)
- [x] توکن‌های revoked در middleware بررسی می‌شوند (JWT security hardening)
- [x] اعمال تغییر بدون شکستن تست‌های موجود (verify commits + fix)
- [x] linter بدون warning عبور می‌کند (ESLint config اضافه شده)
- [x] type-check موفق است (TypeScript Facilities و Customers تکمیل)
- [x] هر دو طرف ناسازگاری شناسایی و فرض‌هایشان مستند شد (docstring اصلاح)
- [x] ground truth تعیین شد و طرف دیگر align شد (docstring اصلاح)
- [x] integration test برای pipeline auth بدون شکست عبور می‌کند (verify commits)
- [x] ریشه anti-pattern تشخیص داده شد (مستندات coherence audit)
- [x] کد اصلاح یا کامنت توجیهی اضافه شد (docstring + SECURITY.md)
- [x] تست edge case نوشته شد (hash_password edge cases)
- [x] Rate limiting و account lockout در endpoint لاگین پیاده‌سازی شده
- [x] تلاش‌های لاگین در Redis لاگ می‌شوند (best-effort Redis logging)
- [x] Permission check در auth pipeline پیاده‌سازی شده
- [x] اعتبارسنجی ورودی لاگین در فرانت‌اند و بک‌اند انجام شده
- [x] ✓ یادداشت مهم برای مدل اجراکننده — بررسی مستقل پیش از تغییر (code-aware: implemented)
- [x] ✓ رفع آسیب‌پذیری بحرانی JWT با الگوریتم none و کلید ضعیف (code-aware: implemented)
- [x] ✓ تقویت امنیت JWT: جایگزینی کلید هاردکد، محدودیت الگوریتم و به‌روزرسانی middleware (code-aware: implemented)
- [x] ✓ تقویت امنیت کلید JWT و اعتبارسنجی توکن‌ها با استفاده از متغیر محیطی و options امن (code-aware: implemented)
- [x] ✓ اجرای دستورات اعتبارسنجی امنیت JWT و تست‌های مربوطه (code-aware: implemented)
- [x] ✓ حذف AUTH_DISABLED و الزام احراز هویت برای endpoint /api/customers (code-aware: implemented)
- [x] ✓ بررسی اولیه خودکار و هشدارهای پیش از اجرا برای بخش امنیت و احراز هویت (code-aware: implemented)
- [x] ✓ حذف backdoor AUTH_DISABLED از توابع get_current_user و get_optional_current_user (code-aware: implemented)
- [x] ✓ حذف یا غیرفعال‌سازی شرطی متغیر AUTH_DISABLED و افزودن middleware مسدودکننده در production (code-aware: implemented)
- [x] ✓ حذف شرط AUTH_DISABLED از کد احراز هویت (code-aware: implemented)
- [x] ✓ افزودن تست‌های خطای احراز هویت در auth.py (code-aware: implemented)
- [x] ✓ افزودن تست‌های سناریوهای خطای احراز هویت به tests/test_auth.py (code-aware: implemented)
- [x] ✓ تبدیل معیارهای پذیرش و مراحل اجرایی به یک مرحله اجرایی واحد (code-aware: implemented)
- [x] ✓ پیاده‌سازی rate limiting لاگین با شناسایی ناسازگاری‌ها و مستندسازی فرض‌ها (code-aware: implemented)
- [x] ✓ پیاده‌سازی Rate Limiting برای Endpoint لاگین در بک‌اند (code-aware: implemented)
- [x] ✓ تعریف معیارهای پذیرش رفتار-محور برای رفع ناسازگاری در pipeline احراز هویت (code-aware: implemented)
- [x] ✓ پیاده‌سازی permission check در auth pipeline (code-aware: implemented)
- [x] ✓ افزودن middleware بررسی permission به pipeline احراز هویت (code-aware: implemented)
- [x] ✓ تعریف معیارهای پذیرش رفتار-محور برای یکپارچه‌سازی احراز هویت (code-aware: implemented)
- [x] ✓ [منطق] پیاده‌سازی بررسی مالکیت برای به‌روزرسانی پروفایل و رمز (code-aware: implemented)
- [x] ✓ اعمال بررسی مالکیت (ownership check) در endpointهای به‌روزرسانی پروفایل و تغییر رمز عبور (code-aware: implemented)
- [x] ✓ رفع عدم اعتبارسنجی ورودی در Pydantic models برای facility (code-aware: implemented)
- [x] ✓ افزودن اعتبارسنجی ورودی به Pydantic models برای CustomerCreate و FacilityCreate (code-aware: implemented)
- [x] ✓ اعتبارسنجی ورودی‌ها و اعمال محدودیت‌های طول و الگوهای Regex برای فیلدهای حساس (code-aware: implemented)
- [x] ✓ افزودن اعتبارسنجی (Validation) به فیلدهای مدل‌های Pydantic (code-aware: implemented)
- [x] ✓ پیاده‌سازی Rate Limiting و Brute Force Protection در مسیر لاگین (code-aware: implemented)
- [x] ✓ پیاده‌سازی Rate Limiting و Brute Force Protection برای endpoint لاگین (code-aware: implemented)
- [x] ✓ پیاده‌سازی محدودیت نرخ و قفل حساب با لاگ‌گیری Redis (code-aware: implemented)
- [x] ✓ افزودن محدودیت نرخ (Rate Limiting) به endpoint لاگین (code-aware: implemented)
- [x] ✓ اجرای دستورات اعتبارسنجی نرخ محدودیت (Rate Limiting) لاگین (code-aware: implemented)
- [x] ✓ رفع نشت اطلاعات حساس در لاگ‌ها و خطاها (code-aware: implemented)
- [x] ✓ رفع نشت اطلاعات حساس در لاگ‌ها و خطاهای عمومی و لاگین (code-aware: implemented)
- [x] ✓ پیاده‌سازی مدیریت خطاهای امن و لاگینگ امن در production (code-aware: implemented)
- [x] ✓ جلوگیری از نشت اطلاعات حساس در خطاها و لاگ‌ها (code-aware: implemented)
- [x] ✓ اجرای دستورات اعتبارسنجی لاگین و بررسی exception handlers (code-aware: implemented)
- [x] ✓ رفع anti-pattern ناهماهنگی شرطی در تابع verify_access_token (code-aware: implemented)
- [x] ✓ رفع ناهماهنگی شرطی در اعتبارسنجی issuer و audience توکن دسترسی (code-aware: implemented)
- [x] ✓ تشخیص و رفع anti-pattern در احراز هویت با تست edge case و عبور از CI/CD (code-aware: implemented)
- [x] ✓ جلوگیری از نشت اطلاعات permission در frontend (code-aware: implemented)
- [x] ✓ رفع نشت اطلاعات permission در frontend با محدودسازی حالت AUTH_DISABLED و generic کردن پیام‌های خطا (code-aware: implemented)
- [x] ✓ همگام‌سازی مدیریت session بک‌اند و فرانت‌اند (code-aware: implemented)
- [x] ✓ افزودن endpoint بررسی اعتبار token و sync دوره‌ای session بین backend و frontend (code-aware: implemented)
- [x] ✓ اعتبارسنجی ورودی‌های لاگین (Login Input Validation) (code-aware: implemented)
- [x] ✓ افزودن اعتبارسنجی ورودی‌های لاگین در فرانت‌اند و بک‌اند (code-aware: implemented)
- [x] ✓ تکمیل معیارهای پذیرش رفتار-محور برای pipeline احراز هویت (code-aware: implemented)
- [x] ✓ پیاده‌سازی معیارهای پذیرش امنیتی شامل HSTS، CORS، ریدایرکت HTTPS و هدرهای امنیتی (code-aware: implemented)
- [x] ✓ افزودن middlewareهای امنیتی CORS و TrustedHost به برنامه FastAPI (code-aware: implemented)
- [x] ✓ افزودن قابلیت Refresh و Blacklist توکن (code-aware: implemented)
- [x] ✓ پیاده‌سازی logout واقعی و مکانیزم refresh token در auth.py (code-aware: implemented)
- [x] ✓ پیاده‌سازی مکانیزم Logout با Blacklist توکن و Refresh Token (code-aware: implemented)
- [x] ✓ پیاده‌سازی مکانیزم بلاک‌لیست توکن در logout (code-aware: implemented)
- [x] ✓ مدیریت خطاهای دیتابیس در auth pipeline (code-aware: implemented)
- [x] ✓ بررسی اولیه خودکار و پیش‌نیازهای اجرایی برای تقویت امنیت و احراز هویت (code-aware: implemented)
- [x] ✓ افزودن مکانیزم Retry و Fallback برای خطاهای اتصال دیتابیس در Pipeline Auth (code-aware: implemented)
- [x] ✓ تعیین معیارهای پذیرش رفتار-محور برای هم‌راستاسازی ناسازگاری‌ها و عبور تست‌های pipeline auth (code-aware: implemented)
- [x] ✓ بررسی و مستندسازی وضعیت فعلی اتصال دیتابیس در auth pipeline (code-aware: implemented)

## 📝 خلاصهٔ verifier

Verified consolidated JWT/auth security task (16 sub-tasks) is fully implemented: JWT none-rejection + env secret (security.py/config.py), AUTH_DISABLED enforcement, login rate limiting (rate_limit.py), permission/ownership checks, Pydantic input validation with regex+length limits (schemas/), log sanitization (log_sanitizer.py), generic 500 handler + catch-all exception handler (main.py), HSTS/CORS/HTTPS-redirect middleware, token refresh+blacklist (token_blacklist.py). All referenced test nodes exist and pass; full backend suite 319 passed, 4 skipped. No code changes needed; recorded verification commit.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- ورودی‌های نامعتبر با خطای 422 رد شوند
- تمامی فیلدهای متنی محدودیت طول داشته باشند
- الگوهای regex برای فیلدهای حساس اعمال شده باشد
- پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد
- پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود
- تمامی تلاش‌ها در Redis لاگ شوند
- توکن با الگوریتم none توسط middleware رد شود
- کلید JWT از متغیر محیطی خوانده شود و در کد هاردکد نباشد
- تمامی تست‌های احراز هویت با موفقیت پاس شوند
- در production، خطاهای 500 پیام generic نمایش دهند
- لاگ‌ها حاوی password یا token نباشند
- exception handler تمام استثناها را catch کند
- بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند
- تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود
- HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد
- CORS فقط دامنه‌های مجاز را اجازه دهد
- در production، HTTP به HTTPS redirect شود
- پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد
- endpoint /auth/refresh وجود داشته باشد و کار کند
- توکن‌های revoked در middleware بررسی شوند
- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است
- هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- ground truth تعیین شد و طرف دیگر align شد
- integration test برای pipeline `auth` بدون شکست عبور می‌کند
- PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- ریشه anti-pattern تشخیص داده شد
- یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- تست edge case نوشته شد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `c0f8647`
- `17141ef`
- `8d514c3`
- `08cc81b`
- `5a1db49`
- `ef4f11c`
- `8f09a33`
- `d7b9c5f`
- `762a533`

**Files lams شده:**
- `backend/app/routers/auth.py`
- `backend/app/utils/security.py`
- `backend/app/utils/rate_limit.py`
- `backend/app/utils/token_blacklist.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/tests/test_auth.py`
- `backend/tests/integration/test_auth_pipeline.py`
- `frontend/.eslintrc.json`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 16 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این مجموعه تسک‌ها بر روی بهبود جامع امنیت سیستم، شامل اعتبارسنجی ورودی، مکانیزم‌های احراز هویت (JWT، Rate Limiting)، مدیریت نشست، کنترل دسترسی (Permission Checks) و رفع آسیب‌پذیری‌های امنیتی در بک‌اند و همگام‌سازی آن با فرانت‌اند تمرکز دارد. بسیاری از تسک‌ها به فایل‌های مرتبط با احراز هویت و امنیت در بک‌اند اشاره دارند و برخی نیز نیازمند هماهنگی با فرانت‌اند هستند.
🎯 theme: امنیت و احراز هویت
💎 estimated_difficulty: large

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 16
  id: 56ab7fb9-d9b6-4cab-a0a3-98e3970018e9
  عنوان اصلی: امن‌سازی JWT: رد none و مدیریت کلید
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py, backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - توکن با الگوریتم none توسط middleware رد شود [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": {"Authorization": "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlI]
  - کلید JWT از متغیر محیطی خوانده شود و در کد هاردکد نباشد [verify_method=static] [verify_plan={"grep_patterns": ["JWT_SECRET_KEY", "os.getenv", "SECRET_KEY"], "files_hint": ["backend/app/routers/auth.py", "backend/app/main.py", "backend/.env.example"]}]
  - تمامی تست‌های احراز هویت با موفقیت پاس شوند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60

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