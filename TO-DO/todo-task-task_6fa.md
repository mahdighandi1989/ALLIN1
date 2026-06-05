# TODO — Task task_6fa (نیاز به تکمیل دستی)

> **رفع Anti-patternهای اعتبارسنجی و پایداری**

## 🔎 خلاصه وضعیت

- **task_id**: `task_6fa50cdd5530`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 1
- **verifier confidence**: 0.98
- **verifier model**: `—`
- **report_id**: `c4343e5c-5190-443f-9987-0ffd5aedfa7b`
- **created_at**: 2026-06-05T01:25:24.487584+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] (step probe #4) تشخیص ریشه anti-pattern AI بدون validation در frontend/src/app/facilities/page.t
- [ ] (step probe #5) اصلاح کد یا افزودن کامنت توجیهی برای AI بدون validation در frontend/src/app/faci

## ✅ چه چیزی Claude انجام داد

- [x] ریشه anti-pattern Under-engineering در user.py تشخیص داده شد (کامنت توجیهی + تست)
- [x] ریشه anti-pattern AI بدون validation در facilities/page.tsx تشخیص و اصلاح شد (کامنت توجیهی)
- [x] ریشه anti-pattern Broken feedback loop در main.py تشخیص داده شد (تست edge case)
- [x] ریشه anti-pattern AI بدون validation در facility.py تشخیص داده شد (تست edge case)
- [x] تست edge case برای Under-engineering در tests/test_user_id_generation.py نوشته شد
- [x] تست edge case برای AI بدون validation در tests/frontend/test_facilities_reason_validation.py نوشته شد
- [x] تست edge case برای Broken feedback loop در tests/test_main.py نوشته شد
- [x] تست edge case برای AI بدون validation در tests/backend/test_facility.py نوشته شد

## 📝 خلاصهٔ verifier

تمام 3 AC اصلی (تشخیص ریشه، اصلاح/کامنت، تست edge case) برای هر 4 anti-pattern (Under-engineering, AI بدون validation در frontend و backend, Broken feedback loop) برآورده شده‌اند. شواهد code-aware و commits اخیر تأیید می‌کنند.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- ریشه anti-pattern تشخیص داده شد
- یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- تست edge case نوشته شد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `a6cc321`
- `47b4922`
- `ac48046`
- `b9dac6d`
- `2ad0d4e`

**Files lams شده:**
- `backend/app/models/user.py`
- `frontend/src/app/facilities/page.tsx`
- `backend/app/main.py`
- `backend/app/models/facility.py`
- `tests/test_user_id_generation.py`
- `tests/frontend/test_facilities_reason_validation.py`
- `tests/test_main.py`
- `tests/backend/test_facility.py`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 4 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها همگی به شناسایی و رفع 'anti-pattern'های موجود در کدبیس، از جمله مشکلات مربوط به اعتبارسنجی (validation) و حلقه‌های بازخورد (feedback loops)، می‌پردازند. این اقدامات برای بهبود نگهداری‌پذیری، خوانایی و پایداری کلی کد ضروری هستند و شامل هر دو بخش فرانت‌اند و بک‌اند می‌شوند.
🎯 theme: رفع Anti-patternها و بهبود کیفیت کد
💎 estimated_difficulty: large

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 4
  id: 29f8d56d-7a43-4b0e-8768-564c7963a2d6
  عنوان اصلی: Address Under-engineering Anti-pattern
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/models/user.py

📋 acceptance_criteria کامل:
  - ریشه anti-pattern تشخیص داده شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["uuid\\.uuid4()\\.hex", "uuid\\.uuid4()\\.int", "// NOTE: 8-char UUID is sufficient for current scale", "# NOTE: 8-char UUID is sufficient for current scale", "// TODO: Address pote]
  - تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_user_id_generation.py::test_uuid_collision_prevention", "timeout_seconds": 60}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — مم

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