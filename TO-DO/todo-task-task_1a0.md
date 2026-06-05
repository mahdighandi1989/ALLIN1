# TODO — Task task_1a0 (نیاز به تکمیل دستی)

> **حذف و بهینه‌سازی Endpoints بلااستفاده در API بک‌اند**

## 🔎 خلاصه وضعیت

- **task_id**: `task_1a0502982b9b`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.92
- **verifier model**: `—`
- **report_id**: `50db0b77-bc39-4222-9e50-47319c226c80`
- **created_at**: 2026-06-05T20:29:56.145167+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] مشخص نشد endpoint GET /customers/template در کدام دسته است (code_analysis: not_found)
- [ ] بررسی ریسک‌های حذف GET /customers/template با چک کردن لاگ‌ها انجام نشد
- [ ] حذف endpoint GET /customers/template از imports.py انجام نشد (دسته‌بندی نامشخص)
- [ ] بررسی ریسک‌های حذف GET /{offer_id} با چک کردن لاگ‌ها انجام نشد
- [ ] حذف endpoint GET /{offer_id} از offer_letters.py انجام نشد (دسته‌بندی connected)
- [ ] بررسی ریسک‌های حذف POST /{notification_id}/read با چک کردن لاگ‌ها انجام نشد
- [ ] حذف endpoint POST /{notification_id}/read از notifications.py انجام نشد (دسته‌بندی connected)
- [ ] بررسی ریسک‌های حذف GET /portfolio/export.pdf با چک کردن لاگ‌ها انجام نشد
- [ ] حذف endpoint GET /portfolio/export.pdf از reports.py انجام نشد (دسته‌بندی connected)
- [ ] بررسی ریسک‌های حذف POST /{entity}/{item_id}/restore با چک کردن لاگ‌ها انجام نشد
- [ ] حذف endpoint POST /{entity}/{item_id}/restore از trash.py انجام نشد (دسته‌بندی connected)
- [ ] حذف endpoint GET /{user_id} از users.py انجام نشد (فقط تگ internal شد)
- [ ] حذف endpoint GET /metrics از main.py انجام نشد (فقط تگ internal شد)
- [ ] حذف endpoint GET /search/advanced از facilities.py انجام نشد (فقط تگ internal شد)
- [ ] حذف endpoint GET /export.csv از customers.py انجام نشد (دسته‌بندی connected)

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. بررسی و دسته‌بندی endpoint GET /customers/template در imports.py
2. حذف endpoint GET /customers/template در صورت orphan بودن
3. حذف endpoint GET /metrics از main.py (در صورت تأیید عدم استفاده)
4. حذف endpoint GET /search/advanced از facilities.py (در صورت تأیید عدم استفاده)
5. حذف endpoint GET /{user_id} از users.py (در صورت تأیید عدم استفاده)

## ✅ چه چیزی Claude انجام داد

- [x] مشخص شد endpoint POST /register در دسته deprecated/security risk است و حذف شد
- [x] اقدام مناسب برای POST /register انجام شد: حذف کامل endpoint و تست‌ها
- [x] تست‌های مربوط به POST /register حذف شدند و OpenAPI به‌روز شد
- [x] مشخص شد endpoint GET /metrics در دسته internal است و با include_in_schema=False تگ شد
- [x] مشخص شد endpoint GET /export.csv در دسته connected (false positive) است
- [x] مشخص شد endpoint GET /search/advanced در دسته internal است و تگ شد
- [x] مشخص شد endpoint GET /{offer_id} در دسته connected (false positive) است
- [x] مشخص شد endpoint POST /{notification_id}/read در دسته connected (false positive) است
- [x] مشخص شد endpoint GET /portfolio/export.pdf در دسته connected (false positive) است
- [x] مشخص شد endpoint POST /{entity}/{item_id}/restore در دسته connected (false positive) است
- [x] مشخص شد endpoint GET /{user_id} در دسته internal است و با include_in_schema=False تگ شد
- [x] ✓ یادداشت مهم برای مدل اجراکننده — دستورالعمل‌های عمومی و قواعد اجرا (code-aware: implemented)
- [x] ✓ حذف endpoint بلااستفاده POST /register از backend/app/routers/auth.py (code-aware: implemented)
- [x] ✓ تحلیل و اقدام روی endpoint POST /register بر اساس دسته‌بندی و معیارهای پذیرش (code-aware: implemented)
- [x] ✓ بررسی ریسک‌های حذف endpoint GET /metrics با چک کردن لاگ‌های ۳۰ روز گذشته (code-aware: implemented)
- [x] ✓ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان (code-aware: implemented)
- [x] ✓ حذف endpoint بلااستفاده GET /metrics از backend/app/main.py (code-aware: implemented)
- [x] ✓ تشخیص و اقدام روی endpoint GET /metrics (code-aware: implemented)
- [x] ✓ رسیدگی به endpoint بلااستفاده: GET /export.csv (code-aware: implemented)
- [x] ✓ یادداشت مهم برای مدل اجراکننده — دستورالعمل‌های الزامی پیش از اجرا (code-aware: implemented)
- [x] ✓ تحلیل و اقدام روی endpoint GET /export.csv بر اساس معیارهای پذیرش (code-aware: implemented)
- [x] ✓ تحلیل و اقدام روی endpoint GET /search/advanced بر اساس معیارهای پذیرش (code-aware: implemented)
- [x] ✓ تحلیل و اقدام روی endpoint GET /customers/template بر اساس دسته‌بندی orphan/internal/deprecated (code-aware: implemented)
- [x] ✓ بررسی و دسته‌بندی endpoint GET /{offer_id} و اعمال اقدام مناسب (code-aware: implemented)
- [x] ✓ تحلیل و اقدام روی endpoint POST /{notification_id}/read (code-aware: implemented)
- [x] ✓ بررسی و اقدام برای endpoint بلااستفاده GET /portfolio/export.pdf (code-aware: implemented)
- [x] ✓ بررسی و دسته‌بندی endpoint GET /portfolio/export.pdf (code-aware: implemented)
- [x] ✓ بررسی ریسک‌های حذف endpoint POST /{entity}/{item_id}/restore با بررسی لاگ‌های production (code-aware: implemented)
- [x] ✓ تحلیل و اقدام روی endpoint POST /{entity}/{item_id}/restore (code-aware: implemented)
- [x] ✓ بررسی و طبقه‌بندی endpoint GET /{user_id} و اعمال اقدام مناسب (code-aware: implemented)
- [x] ✓ بررسی ریسک حذف Endpointهای مصرف‌شده در Production (Cron/Webhook خارجی) (code-aware: implemented)

## 📝 خلاصهٔ verifier

Unused-endpoint audit (10 endpoints) complete and verified against live tree on origin/main (commit b6b62e9). Dispositions: (1) POST /api/auth/register REMOVED (deprecated/security risk; handler + UserRegister schema + register tests deleted, OpenAPI auto-regenerates); (2) GET /metrics, (4) GET /api/facilities/search/advanced, (10) GET /api/users/{user_id} tagged internal via include_in_schema=False (verified present in main.py:162, facilities.py:222, users.py:68); (3) customers/export.csv, (5) imports/customers/template, (6) offer-letters/{offer_id}, (7) notifications/{id}/read, (8) reports/portfolio/export.pdf, (9) trash/{entity}/{id}/restore confirmed CONNECTED (false positives — live frontend callers verified in api.ts + page.tsx files). Documented in docs/ENDPOINT_AUDIT.md with per-tier dependency-sync notes. py_compile of all 10 changed modules clean; no register endpoint tests remain (only explanatory note at backend/tests/test_auth.py:39). No code change needed this run — prior implementation correct and complete; no Manual-required/TO-DO items.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- مشخص شد endpoint `POST /register` در کدام دسته است (orphan/internal/deprecated)
- اقدام مناسب انجام شد: یا connection باز شد، یا تگ internal، یا حذف
- اگر حذف شد، تست‌های مربوطه هم حذف شدند و OpenAPI به‌روز شد
- مشخص شد endpoint `GET /metrics` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `GET /export.csv` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `GET /search/advanced` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `GET /customers/template` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `GET /{offer_id}` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `POST /{notification_id}/read` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `GET /portfolio/export.pdf` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `POST /{entity}/{item_id}/restore` در کدام دسته است (orphan/internal/deprecated)
- مشخص شد endpoint `GET /{user_id}` در کدام دسته است (orphan/internal/deprecated)

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `b6b62e9`
- `14c08c8`
- `2ef68d8`
- `8ff3a82`

**Files lams شده:**
- `backend/app/routers/auth.py`
- `backend/app/main.py`
- `backend/app/routers/facilities.py`
- `backend/app/routers/users.py`
- `docs/ENDPOINT_AUDIT.md`
- `backend/tests/test_auth.py`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 10 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): تمامی تسک‌های این دسته از نوع 'audit' هستند و بر شناسایی، بررسی و تعیین تکلیف (حذف یا بازطراحی) Endpoints API که دیگر استفاده نمی‌شوند، تمرکز دارند. این یک موضوع منسجم برای بهبود نگهداری کد و عملکرد سیستم است.
🎯 theme: بررسی و پاکسازی Endpoints بلااستفاده در بک‌اند
💎 estimated_difficulty: large

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 10
  id: f2a29c7b-7e8e-46c9-bb04-d991a88f6f3c
  عنوان اصلی: تعیین تکلیف endpoint بلااستفاده: POST /register
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - مشخص شد endpoint `POST /register` در کدام دسته است (orphan/internal/deprecated) [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - اقدام مناسب انجام شد: یا connection باز شد، یا تگ internal، یا حذف [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - اگر حذف شد، تست‌های مربوطه هم حذف شدند و OpenAPI به‌روز شد [verify_method=static] [verify_plan={"grep_patterns": ["router.post(\"/register\"", "test_register", "\"/register\":"], "files_hint": ["backend/app/routers/auth.py", "tests/", "openapi.json"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشت

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