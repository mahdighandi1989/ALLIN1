# CLAUDE.md — Working on this repository

سیستم عملیات بانکی (**Banking Operations System**) — FastAPI + Next.js، در حال اجرا
روی Render در **production** با داده‌ی واقعی مشتریان و تسهیلات.
`main` با `autoDeploy: true` مستقیم دیپلوی می‌شود؛ هر تغییر را یک تغییر production در نظر بگیر.

## Non-negotiable rules

1. **اول `experiences/` را بخوان.** هر فایل آنجا یک چالش حل‌شده و الزام‌آور است؛
   تکرار همان خطا ممنوع. درس جدید هر تسک را طبق فرمت `experiences/README.md`
   ثبت کن (kebab-case، frontmatter کامل — **merge، نه replace**).
2. **هیچ قابلیتی را حذف نکن** (endpoint، صفحه، دکمه، fallback، فیچر). به‌جای حذف
   قرنطینه کن و در `docs/REMOVAL_CANDIDATES.md` ثبت کن. حذف فقط با تأیید صریح مالک.
3. **تغییرات منطق حساس** (auth، محاسبات مالی amortization/FX/exposure، ایمپورت اکسل،
   موتور de-dup پاکسازی دیتابیس، backup) نیازمند تحلیل root-cause + وابستگی‌ها در
   `docs/AUDIT_LOG.md`، قدم‌های کوچکِ برگشت‌پذیر، و حفظ مسیر قبلی (flag یا مسیر موازی).
4. **قبل از مرج تأیید کن:** `cd backend && python -m pytest -q` و
   `cd frontend && npm run type-check && npm run build` هر دو باید سبز باشند.
   (CI در `.github/workflows/ci.yml` همین‌ها را اجرا می‌کند.)
5. **بعد از هر تسک، بدون این‌که کسی بخواهد،** هر یافته/تغییر/برگشت را به
   `docs/AUDIT_LOG.md` اضافه کن (append، جدیدترین در انتها) و درس قابل‌استفاده‌مجدد
   را در `experiences/` ثبت کن. این اختیاری نیست.

## Owner standing directives (دستورات دائمی مالک)

- **گردش‌کار مرج:** وقتی قانون ۴ به‌صورت محلی سبز شد، **مستقیم روی `main` کامیت و
  مرج کن** — منتظر تأیید یا دستور جداگانه نمان و PR باز نکن مگر صریحاً خواسته شود.
  قوانین ۱–۳ و ۵ همچنان الزام‌آورند. `main` خودکار روی Render دیپلوی می‌شود؛
  بنابراین «سبزِ محلی» دروازه‌ی ایمنی است — اول تأیید، بعد مرج.
- **دیپلوی فرانت‌اند = کامیتِ خروجی build:** Render فقط بک‌اند را نصب می‌کند و
  فرانت‌اندِ از-پیش-ساخته را از `backend/static/` سرو می‌کند. بعد از **هر** تغییر
  فرانت‌اند: `cd frontend && npm run build` و سپس خروجی `frontend/out/` را به
  `backend/static/` کپی کن (الگوی `build.sh`) و **هر دو را با هم کامیت کن** —
  وگرنه تغییر UI هرگز دیپلوی نمی‌شود.
- **مستندها زنده بمانند:** README فقط فیچرهای واقعاً پیاده‌شده را فهرست می‌کند؛
  فیچر برنامه‌ریزی‌شده به `FEATURE_BACKLOG.md` می‌رود. تصمیم‌های معماری/امنیتی به
  `docs/decisions.md` (ADR) اضافه می‌شوند.

## What this system is

جایگزین وبیِ سیستم اکسل-محور مدیریت عملیات بانکی: مدیریت مشتریان (پروفایل ۲۹۰+
فیلدی)، تسهیلات (OD/Loan/LG/LC + amortization + authorization)، نامه‌های پیشنهاد،
نرخ ارز/exposure، ایمپورت اکسل، گزارش‌ها، بکاپ Google Drive، اعلان‌های درون‌برنامه‌ای
و تلگرام (دوطرفه)، audit log، سطل بازیافت (soft delete)، چندکاربره با JWT.

```
Next.js 14 (static export, RTL فارسی) ──build──▶ backend/static ◀──serve── FastAPI
                                                        │
   frontend/src/lib/api.ts ──axios──▶ /api/* routers ──▶ SQLAlchemy 2.0 async ──▶ PostgreSQL
                                                        │            (dev/test: SQLite)
                              services/ (excel_import, db_cleanup, amortization, fx,
                              telegram, backup/google_drive, notifications, expiry)
```

## فلسفه‌های تثبیت‌شده (تغییرشان نده)

- **Simplicity over features** (ROADMAP) — راه‌حل ساده‌ی کارا بر معماری پیچیده مقدم است.
- **سرور ground truth است** (ADR-001) — مجوزها، rate-limit، و طول عمر session را
  فقط بک‌اند تعیین می‌کند؛ فرانت‌اند صرفاً UI feedback است.
- **پاکسازی/De-dup محافظه‌کار و review-first است** — هیچ رکوردی بدون بازبینی حذف
  نمی‌شود؛ در شک، duplicate اعلام نکن (کامیت‌های `53176f0`, `e592e4e`).
- **`AUTH_DISABLED` عمداً وجود دارد** — خواسته‌ی مالک برای بایپس موقت لاگین؛ حذفش
  نکن، فقط مطمئن باش وقتی auth فعال است همه‌چیز امن است.
- **Startup باید self-heal باشد** — مهاجرت ناموفق نباید بوت را بشکند
  (`app/db_init.py` + `render.yaml` startCommand).

## How to run

```bash
# Backend (Python 3.11)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload           # dev
python -m pytest -q                     # tests (needs: pytest pytest-asyncio pytest-cov pytest-mock aiosqlite xlwt)

# Frontend (Node 18/20)
cd frontend && npm ci
npm run dev                             # dev server
npm run type-check && npm run build     # خروجی static در frontend/out/
```

## Where things live

| Area | Location |
|------|----------|
| FastAPI app + wiring + global handlers | `backend/app/main.py`, `middleware.py`, `monitoring.py` |
| Routers (۲۵ ماژول: auth, customers, facilities, fx, imports, letters, cleanup, …) | `backend/app/routers/` |
| Business logic (excel_import, db_cleanup, amortization, fx, telegram, backup, …) | `backend/app/services/` |
| Models / schemas / migrations | `backend/app/models/`, `backend/app/schemas/`, `backend/migrations/` |
| Auth (JWT + Google Sign-In, rate-limit, blacklist) | `backend/app/routers/auth.py`, `google_auth.py`, `backend/app/utils/security.py` |
| Frontend pages (App Router, static export) | `frontend/src/app/*/page.tsx` |
| API client + auth context | `frontend/src/lib/api.ts`, `lib/axios.ts`, `lib/auth.tsx` |
| سرو-شده در production (خروجی build کامیت‌شده) | `backend/static/` |
| Tests | `backend/tests/` (اصلی)، `tests/` (ریشه — smoke/lint) |
| Audit log (این سند را زنده نگه دار) | `docs/AUDIT_LOG.md` |
| ADRs / امنیت / اسکیما | `docs/decisions.md`, `docs/SECURITY.md`, `docs/DATABASE_SCHEMA.md` |
| Binding lessons | `experiences/` |
| Owner's task log (ابزار بیرونی می‌سازد — دست نزن) | `prompt/` |
| فیچرهای پیاده‌نشده | `FEATURE_BACKLOG.md` |

## Conventions

- Commits: `type(scope): summary` — کوچک، تک-موضوع، برگشت‌پذیر؛ فقط سبزِ تأییدشده مرج شود.
- UI فارسی/RTL است. **قانون bidi:** هر رشته‌ی فارسیِ آمیخته با لاتین/عدد/علائم باید
  داخل ancestor صریحِ `dir="rtl"` باشد وگرنه مرورگر ترتیب عبارت را به‌هم می‌ریزد؛
  build سبز این را نمی‌گیرد — بصری چک کن.
- خطاهای API با `parseApiError` در فرانت‌اند هندل می‌شوند؛ پاسخ خطای بک‌اند
  ساختار `{detail: ...}` استاندارد FastAPI را نگه دارد.
- تاریخ‌ها در UI جلالی (شمسی) نمایش داده می‌شوند؛ ذخیره‌سازی ISO/UTC است — هنگام
  دست‌زدن به تاریخ هر دو سمت را چک کن.
- ایمپورت اکسل: تشخیص فرمت با magic-byte، ستون‌های اجباری fail-fast،
  خطاهای طبقه‌بندی‌شده (`ExcelParseError`) — این قرارداد را نگه دار.
