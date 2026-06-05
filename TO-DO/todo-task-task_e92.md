# TODO — Task task_e92 (نیاز به تکمیل دستی)

> **پاکسازی اسکریپت‌های Inspector Bridge و وابستگی‌های فرانت‌اند**

## 🔎 خلاصه وضعیت

- **task_id**: `task_e92cd1d0c4b4`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.85
- **verifier model**: `—`
- **report_id**: `3c1b2fdf-72aa-4ff7-b901-637bf9dcb67f`
- **created_at**: 2026-06-05T00:20:32.529744+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اسکریپت Inspector Bridge نیست (ناقص - backend/static/ نیاز به بررسی مجدد)
- [ ] صفحه داشبورد بدون خطای runtime بارگذاری می‌شود (ناقص - مشکل static export باقی مانده)
- [ ] اجرای تست‌ها و اعتبارسنجی نهایی (تسک 3 - مرحله 17 ناقص)
- [ ] Commit نهایی و ثبت تغییرات با پیام واضح (تسک 3 - مرحله 18 انجام نشده)

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. بررسی مجدد backend/static/ برای حذف کامل اسکریپت Inspector Bridge
2. رفع مشکل 'Dashboard data unavailable in static mode' برای بارگذاری بدون خطا
3. اجرای تست‌ها و اعتبارسنجی نهایی (pytest, npm run test, npm run lint)
4. Commit نهایی با پیام واضح شامل merged-from شناسه‌های تسک‌ها

## ✅ چه چیزی Claude انجام داد

- [x] اعمال تغییر بدون شکستن تست‌های موجود (تأیید شده توسط code_analysis)
- [x] linter بدون warning عبور می‌کند (ESLint config اضافه شده)
- [x] type-check موفق است (تکمیل TypeScript Facilities و Customers تأیید شده)
- [x] دستور npm install بدون خطا اجرا می‌شود (وابستگی‌های فرانت‌اند کامل)
- [x] فایل package-lock.json حاوی وابستگی sonner است (همگام‌سازی انجام شده)
- [x] حذف اسکریپت Inspector Bridge از frontend/out/ (مرحله 6 و 7 کامل)
- [x] حذف اسکریپت Inspector Bridge از backend/static/ (مرحله 8 و 10 کامل)
- [x] حذف کد تزریق اسکریپت از InspectorBridge.tsx (مرحله 3 کامل)
- [x] حذف پلاگین تزریق اسکریپت از next.config.js (مرحله 4 کامل)
- [x] بررسی و حذف WebSocket URL هاردکد شده از فایل‌های HTML (مرحله 1 و 2 کامل)
- [x] ✓ بررسی و حذف WebSocket URL هاردکد شده از فایل‌های HTML استاتیک (تسک 1 - بخش ⚠️ یادداشت مهم) (code-aware: implemented)
- [x] ✓ حذف کامل اسکریپت Inspector Bridge از تمام فایل‌های HTML استاتیک (تسک 1 - بخش 🎯 هدف) (code-aware: implemented)
- [x] ✓ بررسی و حذف کد تزریق اسکریپت از InspectorBridge.tsx (تسک 1 - بخش ✅ معیار پذیرش) (code-aware: implemented)
- [x] ✓ بررسی و حذف پلاگین تزریق اسکریپت از next.config.js (تسک 1 - بخش 💡 نمونه‌های قبل/بعد) (code-aware: implemented)
- [x] ✓ اجرای تست‌ها و اعتبارسنجی تغییرات (تسک 1 - بخش 🧪 دستورات اعتبارسنجی) (code-aware: implemented)
- [x] ✓ بررسی و حذف اسکریپت Inspector Bridge از frontend/out/ (تسک 2 - بخش ⚠️ یادداشت مهم) (code-aware: implemented)
- [x] ✓ حذف اسکریپت Inspector Bridge از تمام فایل‌های frontend/out/ (تسک 2 - بخش 🎯 هدف) (code-aware: implemented)
- [x] ✓ بررسی و حذف اسکریپت Inspector Bridge از backend/static/ (تسک 2 - بخش ✅ معیار پذیرش) (code-aware: implemented)
- [x] ✓ اجرای تست‌ها و اعتبارسنجی تغییرات (تسک 2 - بخش 💡 نمونه‌های قبل/بعد) (code-aware: implemented)
- [x] ✓ بررسی و حذف اسکریپت Inspector Bridge از backend/static/ (تسک 2 - بخش 🧪 دستورات اعتبارسنجی) (code-aware: implemented)
- [x] ✓ بررسی و اضافه کردن وابستگی sonner به package.json (تسک 3 - بخش ⚠️ یادداشت مهم) (code-aware: implemented)
- [x] ✓ اضافه کردن وابستگی sonner به package.json (تسک 3 - بخش 🎯 هدف) (code-aware: implemented)
- [x] ✓ اجرای npm install برای به‌روزرسانی package-lock.json (تسک 3 - بخش ✅ معیار پذیرش) (code-aware: implemented)
- [x] ✓ حذف وابستگی غیرضروری react-hot-toast از package.json (تسک 3 - بخش 💡 نمونه‌های قبل/بعد) (code-aware: implemented)
- [x] ✓ اجرای npm install مجدد برای به‌روزرسانی package-lock.json پس از حذف react-hot-toast (تسک 3 - بخش 🧪 دستورات اعتبارسنجی) (code-aware: implemented)
- [x] ✓ اجرای build فرانت‌اند برای اعتبارسنجی نهایی (تسک 3 - بخش ⚠️ ریسک‌ها و موارد احتیاط) (code-aware: implemented)

## 📝 خلاصهٔ verifier

بیشتر مراحل پاکسازی اسکریپت‌های Inspector Bridge و مدیریت وابستگی‌های فرانت‌اند انجام شده است. 4 معیار از 7 معیار پذیرش اصلی به طور کامل برآورده شده‌اند. دو معیار (حذف کامل اسکریپت از فایل‌های HTML و بارگذاری بدون خطای داشبورد) ناقص هستند و نیاز به بررسی و رفع مشکل دارند. همچنین مراحل نهایی تسک 3 (اعتبارسنجی و commit) باقی مانده است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است
- هیچ فایل HTML در frontend/out/ و backend/static/ حاوی اس
- صفحه داشبورد بدون خطای runtime بارگذاری شود.
- دستور `npm install` بدون خطا اجرا شود.
- فایل `package-lock.json` حاوی وابستگی `sonner` باشد.

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `54e16b2`
- `3ded908`
- `e6cb0cd`
- `4e3c136`
- `8f09a33`
- `d7b9c5f`

**Files lams شده:**
- `frontend/next.config.js`
- `frontend/.eslintrc.json`
- `frontend/out/dashboard/index.html`
- `backend/static/dashboard/index.html`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 3 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به مسائل مربوط به پیکربندی، ساخت و پاکسازی کد در فرانت‌اند می‌پردازند. شامل پیکربندی WebSocket، حذف کدهای Inspector Bridge از خروجی‌های HTML و همگام‌سازی فایل‌های مدیریت وابستگی (package.json و package-lock.json) است.
🎯 theme: پیکربندی و پاکسازی فرانت‌اند
💎 estimated_difficulty: small

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 3
  id: 2c5a4a0d-4b6e-4a44-8e29-4c4945c4487a
  عنوان اصلی: پیکربندی WebSocket URL و توکن پروژه
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: frontend/next.config.js, frontend/out/dashboard/index.html, frontend/src/app/InspectorBridge.tsx

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["no-warning", "lint.*pass"], "files_hint": ["frontend/"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["type-check.*success", "tsc.*exit.*0"], "files_hint": ["frontend/"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخو

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