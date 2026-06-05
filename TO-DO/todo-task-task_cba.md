# TODO — Task task_cba (نیاز به تکمیل دستی)

> **افزودن ستون amount و به‌روزرسانی داشبورد**

## 🔎 خلاصه وضعیت

- **task_id**: `task_cba4b5521484`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.98
- **verifier model**: `—`
- **report_id**: `66787849-72a3-4a95-830d-e1bf458fcfa6`
- **created_at**: 2026-06-05T18:46:37.296012+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] مقادیر amount در داشبورد به درستی نمایش داده می‌شوند

## ✅ چه چیزی Claude انجام داد

- [x] ستون amount با NUMERIC(15,2) در migration 002 و مدل facility.py اضافه شده
- [x] endpoint /api/stats/dashboard خطای 500 برنمی‌گرداند و total_amount را برمی‌گرداند
- [x] مقادیر amount در پاسخ داشبورد (total_amount) موجود و در تست‌ها تأیید شده
- [x] finally از یک منبع مرکزی default می‌گیرد (false-positive تشخیص داده شده)
- [x] تست fixture رفتار پیش‌فرض (test_user_id_default) در test_defaults.py نوشته شده
- [x] migration 003_widen_user_id.py برای backward-compat تغییر default value اضافه شده
- [x] ریشه anti-pattern 'Stale assumption' در user.py تشخیص و مستند شده
- [x] کد اصلاح شده (UUID کامل) و کامنت توجیهی در user.py اضافه شده
- [x] تست edge case collision UUID در test_user_uuid.py نوشته شده

## 📝 خلاصهٔ verifier

همه 9 معیار پذیرش تسک (ستون amount، اصلاح داشبورد، استانداردسازی finally) در وضعیت فعلی پروژه به طور کامل پیاده‌سازی شده‌اند. ستون amount با NUMERIC(15,2) در migration و مدل ORM وجود دارد، endpoint dashboard بدون خطای 500 کار می‌کند و total_amount را برمی‌گرداند، finally از یک منبع مرکزی default می‌گیرد، تست‌های fixture و edge case نوشته شده، anti-pattern UUID تشخیص و اصلاح شده، و migration backward-compat اضافه شده است.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- ستون amount با نوع NUMERIC(15,2) در جدول facilities وجود دارد
- endpoint /api/stats/dashboard خطای 500 برنمی‌گرداند
- مقادیر amount در داشبورد به درستی نمایش داده می‌شوند
- `finally` در همه‌جا از یک منبع default می‌گیرد
- تست fixture رفتار پیش‌فرض را تأیید می‌کند
- اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد
- ریشه anti-pattern تشخیص داده شد
- یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- تست edge case نوشته شد

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `1ce1a37`
- `53559c2`
- `8a04170`
- `ce636e6`
- `ba6453d`
- `db84f9a`
- `09a8ad2`
- `d753ff4`
- `754abeb`

**Files lams شده:**
- `backend/migrations/versions/002_add_missing_columns.py`
- `backend/app/models/facility.py`
- `backend/app/routers/stats.py`
- `backend/tests/test_stats.py`
- `backend/tests/test_defaults.py`
- `backend/migrations/versions/003_widen_user_id.py`
- `backend/app/models/user.py`
- `backend/tests/backend/app/models/test_user_uuid.py`
- `backend/tests/unit/test_finally_field.py`

## 💡 ایدهٔ اصلی تسک

🧬 این یک تسک تلفیقی است — از 3 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها به مسائل مربوط به شمای دیتابیس، یکپارچگی داده‌ها و مدل‌های داده‌ای می‌پردازند. رفع خطای 500 داشبورد با افزودن ستون، یکپارچه‌سازی فیلدهای پیش‌فرض و حل الگوهای ضدطراحی در مدل کاربر، همگی به حفظ صحت و پایداری داده‌ها کمک می‌کنند.
🎯 theme: بهبود پایداری و یکپارچگی داده‌ها در بک‌اند
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 3
  id: e155869b-cb38-44ec-a932-5ee8164d5907
  عنوان اصلی: رفع خطای 500 داشبورد با افزودن ستون amount
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/migrations/versions/001_initial_create_tables.py, backend/migrations/versions/002_add_missing_columns.py

📋 acceptance_criteria کامل:
  - ستون amount با نوع NUMERIC(15,2) در جدول facilities وجود دارد [verify_method=static] [verify_plan={"grep_patterns": ["op.add_column('facilities', sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=True))", "Column('amount', Numeric(15, 2))"], "files_hint": ["backend/migrations/version]
  - endpoint /api/stats/dashboard خطای 500 برنمی‌گرداند [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/stats/dashboard", "headers": null, "json_body": null, "expected_status": 200, "required_fields": ["total_amount", "other_stats"], "json_contains": null}]
  - مقادیر amount در داشبورد به درستی نمایش داده می‌شوند [verify_method=ui_interaction] [verify_plan={"base": "frontend", "ui_steps": [{"action"

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