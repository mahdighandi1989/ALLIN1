# TODO — Task task_8a1 (نیاز به تکمیل دستی)

> **تکمیل TypeScript صفحه Facilities و API**

## 🔎 خلاصه وضعیت

- **task_id**: `task_8a1dde11cd7b`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.98
- **verifier model**: `—`
- **report_id**: `20d4c714-c894-405c-80db-cc6f87094a6a`
- **created_at**: 2026-06-04T23:58:31.325650+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] ریشه anti-pattern تشخیص داده شد
- [ ] یا کد اصلاح شد، یا کامنت توجیهی اضافه شد

## ✅ چه چیزی Claude انجام داد

- [x] اعمال تغییر بدون شکستن تست‌های موجود (تأیید شده توسط code_analysis)
- [x] linter بدون warning عبور می‌کند (ESLint config اضافه شده)
- [x] type-check موفق است (تکمیل TypeScript Facilities و Customers تأیید شده)
- [x] ریشه anti-pattern تشخیص داده شد (مستندات coherence audit اضافه شد)
- [x] کد اصلاح یا کامنت توجیهی اضافه شد (مستندات SECURITY.md و decisions.md)
- [x] تست edge case نوشته شد (تست‌های احراز هویت و endpoint داشبورد)
- [x] تأیید شد که /customers orphan است (redirect انجام شده)
- [x] navigation link اضافه یا route حذف/redirect شد (redirect 301 برای /customers)
- [x] تست navigation: کاربر می‌تواند به صفحه مقصد برسد (routing کامل شده)

## 📝 خلاصهٔ verifier

تمامی معیارهای پذیرش تسک 'تکمیل TypeScript صفحه Facilities و API' برآورده شده‌اند. TypeScript صفحات Facilities و Customers تکمیل، routing و redirect مسیر /customers انجام، linter و type-check پیکربندی و عبور داده شده، anti-patternها تشخیص و مستند شده، تست‌های edge case نوشته شده، و تست navigation تأیید شده است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- اعمال تغییر بدون شکستن تست‌های موجود
- linter بدون warning عبور می‌کند
- type-check موفق است
- ریشه anti-pattern تشخیص داده شد
- یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- تست edge case نوشته شد
- تأیید شد که `/customers` orphan است (هیچ Link/router.push اشاره نمی‌کند)
- یا navigation link اضافه شد، یا route حذف/redirect شد
- تست navigation: کاربر بتواند به این صفحه (یا destination) برسد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `a78afe7`
- `663f434`
- `022b485`
- `f5b7693`
- `678e5f7`
- `8f09a33`
- `a018074`
- `d7b9c5f`

**Files lams شده:**
- `frontend/src/app/facilities/page.tsx`
- `frontend/src/app/customers/page.tsx`
- `frontend/.eslintrc.json`
- `docs/SECURITY.md`
- `docs/decisions.md`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 5 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به طور خاص به رفع باگ‌ها و بهبود عملکرد و کد در صفحات فرانت‌اند 'Customers' و 'Facilities' می‌پردازند. شامل فعال‌سازی بارگذاری داده، رفع مشکلات TypeScript، اصلاح کلاینت API و مدیریت دکمه‌های UI است. همچنین شامل پاکسازی مسیرهای بلااستفاده فرانت‌اند و refactor کد در این بخش‌ها می‌شود.
🎯 theme: صفحات فرانت‌اند Customers و Facilities
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 5
  id: 589f3f1d-0170-40d4-92ec-d75796ff83e6
  عنوان اصلی: Fix incomplete TypeScript on Facilities page
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["export default function FacilitiesPage", "import React from 'react'"], "files_hint": ["frontend/src/app/facilities/page.tsx"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["Promise.allSettled", "facilitiesResult.status === 'fulfilled'", "return \\(<div\\>"], "files_hint": ["frontend/src/app/facilities/page.tsx"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، ی

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