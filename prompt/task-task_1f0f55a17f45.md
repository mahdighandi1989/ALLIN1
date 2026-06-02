---
task_id: task_1f0f55a17f45
title: تقویت امنیت JWT و مکانیزم‌های احراز هویت
type: other
priority: critical
execution_priority: 1050
status: pending
external_status: done
verification_status: applied_externally_pending_verify
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:04:20.175732+00:00'
updated_at: '2026-06-02T13:04:34.981632+00:00'
tags:
- consolidated
- post_verify_merge
---

# تقویت امنیت JWT و مکانیزم‌های احراز هویت

## Raw Idea

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
  - تمامی تست‌های احراز هویت با موفقیت پاس شوند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع آسیب‌پذیری بحرانی JWT با الگوریتم none و کلید ضعیف

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:1-50` — `create_access_token` — کلید ثابت و ضعیف، عدم بررسی الگوریتم none
  ```python
  from jose import jwt
  SECRET_KEY = "your-secret-key"
  ALGORITHM = "HS256"
  def create_access_token(data: dict):
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(minutes=30)
      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
      return encoded_jwt
  ```
- `backend/app/main.py:20-40` — `verify_token` — عدم استفاده از options برای امنیت بیشتر
  ```python
  def verify_token(token: str = Depends(oauth2_scheme)):
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          return payload
      except JWTError:
          raise HTTPException(status_code=401)
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + python-jose + JWT + OAuth2

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/.env.example` (سطر 5) — شامل کلید پیش‌فرض ضعیف
- `backend/app/config.py` (سطر 10) — محل بارگذاری تنظیمات JWT

## 🌐 نقشهٔ وابستگی‌ها
سیستم احراز هویت کل پروژه به این ماژول وابسته است. تمام endpointهای محافظت‌شده از این middleware استفاده می‌کنند.

## 🔍 Context و وضعیت فعلی
در فایل backend/app/routers/auth.py از کتابخانه python-jose با الگوریتم HS256 و یک کلید ثابت و ضعیف ('your-secret-key' در .env.example) استفاده شده است. این پیکربندی امکان حملات signature bypass (CVE-2022-23529) و brute-force را فراهم می‌کند. همچنین middleware احراز هویت در backend/app/main.py بررسی نمی‌کند که آیا توکن با الگوریتم 'none' امضا شده است یا خیر. این آسیب‌پذیری به مهاجم اجازه می‌دهد توکن‌های جعلی با دسترسی ادمین تولید کند.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] توکن با الگوریتم none توسط middleware رد شود
- [ ] کلید JWT از متغیر محیطی خوانده شود و در کد هاردکد نباشد
- [ ] تمامی تست‌های احراز هویت با موفقیت پاس شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. کلید JWT را با یک کلید 256 بیتی تصادفی از متغیر محیطی JWT_SECRET_KEY جایگزین کنید.
2. در تنظیمات JWT، پارامتر 'options' را با {'verify_signature': True, 'require': ['exp', 'iat']} تنظیم کنید.
3. الگوریتم‌های مجاز را به ['HS256'] محدود کنید.
4. از کتابخانه 'authlib' یا 'PyJWT' به جای python-jose استفاده کنید که امن‌تر است.
5. middleware احراز هویت را برای رد توکن‌های با الگوریتم none به‌روزرسانی کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: کلید ثابت در کد**

_قبل:_
```
SECRET_KEY = "your-secret-key"
```

_بعد:_
```
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
```

**قبل: decode بدون options**

_قبل:_
```
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

_بعد:_
```
payload = jwt.decode(token, SECRET_KEY, options={"verify_signature": True, "require": ["exp", "iat"]}, algorithms=["HS256"])
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `python -c "from jose import jwt; token = jwt.encode({'sub':'admin'}, '', algorithm='none'); print('VULNERABLE' if jwt.decode(token, '', options={'verify_signature': False}) else 'FIXED')"`
- `pytest tests/test_auth.py -v -k "test_jwt_security"`

## ⚠️ ریسک‌ها و موارد احتیاط
پس از تغییر کلید، تمام توکن‌های قبلی نامعتبر می‌شوند و کاربران باید دوباره لاگین کنند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: critical
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 16
  id: 62de5589-02b3-4084-8051-a0047f6735a9
  عنوان اصلی: حذف AUTH_DISABLED و الزام احراز هویت
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/utils/security.py

📋 acceptance_criteria کامل:
  - بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/customers", "headers": null, "json_body": null, "expected_status": 401, "required_fields": [], "json_contains": null}]
  - تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود [verify_method=static] [verify_plan={"grep_patterns": ["AUTH_DISABLED"], "files_hint": ["backend/app/utils/security.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
AUTH_DISABLED=true باعث دور زدن کامل احراز هویت می‌شود

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/utils/security.py:193-219` — `get_current_user` — بلاک شرطی که احراز هویت را کاملاً دور می‌زند
  ```python
  async def get_current_user(
      db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
  ) -> "User":
      if settings.AUTH_DISABLED:
          result = await db.execute(select(User).where(User.username == "demo"))
          user = result.scalar_one_or_none()
          if user is None:
              user = User(
                  username="demo",
                  email="demo@example.com",
                  hashed_password=hash_password("demo"),
                  full_name="Demo User",
                  is_active=True,
              )
              db.add(user)
              await db.commit()
              await db.refresh(user)
          return user
  ```
- `backend/app/utils/security.py:243-269` — `get_optional_current_user` — همان رفتار در تابع دوم
  ```python
  async def get_optional_current_user(
      db: AsyncSession = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
  ) -> Optional["User"]:
      if settings.AUTH_DISABLED:
          result = await db.execute(select(User).where(User.username == "demo"))
          user = result.scalar_one_or_none()
          if user is None:
              user = User(
                  username="demo",
                  ...
              )
              db.add(user)
              await db.commit()
              await db.refresh(user)
          return user
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + JWT + SQLAlchemy async session

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/config.py` (سطر 1) — محل تعریف settings.AUTH_DISABLED
- `docker-compose.prod.yml` (سطر 1) — محل احتمالی تنظیم متغیر محیطی
- `render.yaml` (سطر 1) — محل احتمالی تنظیم متغیر محیطی
- `backend/app/database.py` — `security.py` این فایل را import می‌کند
- `backend/app/models/user.py` — `security.py` این فایل را import می‌کند
- `backend/tests/conftest.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_auth.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_models.py` — این فایل `security.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
این تابع توسط تمام روترهای backend (auth, customers, facilities, stats) از طریق Depends استفاده می‌شود.

## 🔍 Context و وضعیت فعلی
در فایل backend/app/utils/security.py، خط 204، اگر settings.AUTH_DISABLED برابر True باشد، تابع get_current_user بدون بررسی توکن، کاربر demo را برمی‌گرداند. این یعنی هر درخواستی بدون نیاز به توکن معتبر می‌تواند به endpointهای محافظت‌شده دسترسی پیدا کند. این یک backdoor عمدی است که در محیط production نباید وجود داشته باشد. همچنین در خط 254 همین فایل، تابع get_optional_current_user نیز همین رفتار را دارد.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند
- [ ] تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱. متغیر محیطی AUTH_DISABLED را از settings حذف کنید یا مقدار پیش‌فرض آن را False قرار دهید. ۲. در docker-compose.prod.yml و render.yaml این متغیر را حذف کنید. ۳. یک middleware اضافه کنید که در محیط production اگر AUTH_DISABLED=True بود، اخطار لاگ بدهد و از اجرا جلوگیری کند.

## 💡 نمونه‌های قبل/بعد
**حذف شرط AUTH_DISABLED**

_قبل:_
```
if settings.AUTH_DISABLED:
    return demo_user
# ادامه کد
```

_بعد:_
```
# حذف کامل بلاک if settings.AUTH_DISABLED
# ادامه کد
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 16
  id: 42cbcd99-7b21-4491-816e-cad31d6791cf
  عنوان اصلی: افزودن تست‌های خطای احراز هویت در auth.py
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["lint", "flake8", "pylint", "ruff"], "files_hint": ["backend/"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["mypy", "pyright", "type: ignore"], "files_hint": ["backend/"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
فایل backend/app/routers/auth.py فاقد تست برای سناریوهای خطای احراز هویت است

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
فایل backend/tests/test_auth.py وجود دارد اما تست‌های آن سناریوهای بحرانی مانند تلاش‌های مکرر لاگین (rate limiting)، توکن منقضی، و توکن نامعتبر را پوشش نمی‌دهد. با توجه به اینکه frontend/src/app/login/page.tsx محدودیت 5 تلاش لاگین را پیاده‌سازی کرده، backend نیز باید این محدودیت را اع

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
_(مجری بر اساس Context و معیارهای پذیرش، مراحل را تعیین کند)_

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 4 از 16
  id: ea641ffd-df5b-46e4-8d2f-9f1586208457
  عنوان اصلی: [منطق] پیاده‌سازی rate limiting لاگین
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["login attempts", "rate limit", "rate_limit", "brute force"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/tests/test_auth.py", "backend/app/auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["rate_limit", "RateLimiter", "throttle", "redis"], "files_hint": ["backend/app/auth.py", "backend/app/middleware.py", "backend/app/rate_limiter.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/test_auth.py::test_login_rate_limit", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی"}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] نبود rate limiting در login endpoint

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در frontend/src/app/login/page.tsx، شمارنده login attempts وجود دارد، اما این شمارنده فقط در سمت کلاینت است و قابل bypass توسط مهاجم است. backend (backend/tests/test_auth.py) هیچ محدودیتی برای تعداد تلاش‌های لاگین ندارد.

## 💥 پیامد (impact)
حملات brute-force به راحتی قابل انجام است. مهاجم می‌تواند هزاران درخواست لاگین در ثانیه ارسال کند تا رمز عبور را حدس بزند.

## 🛠 پیشنهاد رفع اولیه
در backend، یک rate limiter (مثلاً با redis یا in-memory) برای endpoint لاگین پیاده‌سازی کنید. بعد از 5 تلاش ناموفق، IP را برای 15 دقیقه مسدود کنید. شمارنده frontend را فقط برای UI feedback نگه دارید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی ناسازگاری منطقی بین شمارنده کلاینت و عدم محدودیت سرور — بررسی و مستندسازی ناسازگاری منطقی بین شمارنده کلاینت و عدم محدودیت سرور انجام نشده
  - پیاده‌سازی rate limiter سمت سرور برای endpoint لاگین با محدودیت ۵ تلاش ناموفق و مسدودیت ۱۵ دقیقه‌ای — rate limiter سمت سرور برای endpoint لاگین پیاده‌سازی نشده
  - اصلاح شمارنده frontend به UI feedback-only و حذف منطق محدودیت سمت کلاینت — شمارنده frontend به UI feedback-only تبدیل نشده
  - نوشتن تست‌های unit و integration برای rate limiter backend — تست‌های unit و integration برای rate limiter نوشته نشده
  - به‌روزرسانی مستندات و معیارهای پذیرش نهایی — مستندات و معیارهای پذیرش نهایی به‌روزرسانی نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 5 از 16
  id: ae87a6ca-2f66-469b-b263-79b1785240b3
  عنوان اصلی: پیاده‌سازی permission check در auth pipeline
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["permission", "authorization", "role", "access control"], "files_hint": ["backend/auth/pipeline.py", "backend/auth/README.md", "docs/auth.md"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "permission check", "authorization"], "files_hint": ["backend/auth/pipeline.py", "backend/auth/README.md"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why", "rationale"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md", "docs/decisions.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم وجود permission check در auth pipeline

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در مستندات ارائه شده، هیچ اشاره‌ای به مکانیزم permission یا authorization در pipeline احراز هویت نشده است. تمام مسیرهای mutation (مانند تغییر رمز عبور، ثبت‌نام، لاگین) بدون بررسی سطح دسترسی (role-based یا resource-based) اجرا می‌شوند. این یک شکاف امنیتی جدی است.

## 💥 پیامد (impact)
هر کاربر احراز هویت شده می‌تواند به عملیات‌های حساس مانند تغییر رمز عبور سایر کاربران یا دسترسی به منابع غیرمجاز دست یابد. این نقض اصل least privilege است.

## 🛠 پیشنهاد رفع اولیه
یک middleware یا decorator برای بررسی permission در endpoints اضافه کنید. مثلاً در backend/tests/test_auth.py و backend/app/database.py، قبل از هر mutation، سطح دسترسی کاربر را با token یا role چک کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی endpoint لاگین و اعمال permission در صورت نیاز
  - بررسی و رفع coherence issues در pipeline auth

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی permission در auth pipeline — مستندسازی کامل فرض‌های دو طرف ناسازگاری انجام نشده
  - طراحی مدل داده‌ای Role و Permission در database — مدل‌های Role و Permission در database ایجاد نشده
  - پیاده‌سازی decorator require_permission در backend — decorator require_permission پیاده‌سازی نشده
  - پیاده‌سازی تابع get_user_permissions از token — تابع get_user_permissions پیاده‌سازی نشده
  - اعمال decorator require_permission بر روی endpoint تغییر رمز عبور — decorator بر روی endpoint تغییر رمز اعمال نشده
  - اعمال decorator require_permission بر روی endpoint ثبت‌نام کاربر جدید — decorator بر روی endpoint ثبت‌نام اعمال نشده
  - اضافه کردن seed data برای roles و permissions در migration — seed data برای roles و permissions اضافه نشده
  - نوشتن unit tests برای decorator require_permission — unit tests برای decorator require_permission نوشته نشده
  - نوشتن integration tests برای permission در endpoints auth — integration tests برای permission در endpoints auth نوشته نشده
  - به‌روزرسانی مستندات API با permission requirements — مستندات API با permission requirements به‌روزرسانی نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 6 از 16
  id: 84bedb2d-3590-4311-ab28-4c105d6d8f4c
  عنوان اصلی: [منطق] پیاده‌سازی بررسی مالکیت برای به‌روزرسانی پروفایل و رمز
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/integration/test_auth_pipeline.py::test_profile_update_and_password_change_secure", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم بررسی ownership در profile update و password change

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در تست‌ها (test_auth.py) به endpoints 'profile update' و 'password change' اشاره شده، اما هیچ مکانیزمی برای اطمینان از اینکه کاربر فقط پروفایل خودش را به‌روزرسانی می‌کند (ownership check) دیده نمی‌شود.

## 💥 پیامد (impact)
یک کاربر می‌تواند با تغییر userId در درخواست، پروفایل یا رمز عبور کاربران دیگر را تغییر دهد (IDOR vulnerability).

## 🛠 پیشنهاد رفع اولیه
در endpointهای مربوطه، userId را از توکن احراز هویت استخراج کنید و با userId درخواست مقایسه کنید. اگر مطابقت نداشت، خطای 403 برگردانید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - شناسایی و مستندسازی فرض‌های ناسازگار در pipeline auth — بررسی کامل کدهای pipeline auth برای شناسایی فرض‌های ناسازگار در استخراج userId
  - تعیین ground truth و align کردن طرف دیگر (رفع IDOR vulnerability) — پیاده‌سازی ownership check با استخراج userId از JWT و بازگرداندن خطای 403
  - نوشتن integration test برای pipeline auth با پوشش ownership check — نوشتن integration test برای سناریوهای مجاز/غیرمجاز در به‌روزرسانی پروفایل و تغییر رمز

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 7 از 16
  id: 568f1abe-58ef-40bc-ba40-b9fa76d4ab1a
  عنوان اصلی: رفع عدم اعتبارسنجی ورودی در Pydantic models
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/schemas/__init__.py, backend/app/schemas/facility.py

📋 acceptance_criteria کامل:
  - ورودی‌های نامعتبر با خطای 422 رد شوند [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/facilities", "headers": null, "json_body": {"name": "", "phone": "invalid", "national_code": "123", "email": "not-an-email", "capacity": -1}, "expected_status": 422, "]
  - تمامی فیلدهای متنی محدودیت طول داشته باشند [verify_method=static] [verify_plan={"grep_patterns": ["max_length", "min_length", "String.*max_length"], "files_hint": ["backend/app/schemas/__init__.py", "backend/app/schemas/facility.py"]}]
  - الگوهای regex برای فیلدهای حساس اعمال شده باشد [verify_method=static] [verify_plan={"grep_patterns": ["regex", "pattern", "Field.*regex", "constr.*regex"], "files_hint": ["backend/app/schemas/__init__.py", "backend/app/schemas/facility.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم اعتبارسنجی ورودی در Pydantic models

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/schemas/__init__.py:10-30` — `CustomerCreate` — فیلدها بدون validation
  ```python
  class CustomerCreate(BaseModel):
      name: str
      phone: str
      national_id: str
      email: str
      address: str
  ```
- `backend/app/schemas/facility.py:5-20` — `FacilityCreate` — عدم محدودیت برای amount و type
  ```python
  class FacilityCreate(BaseModel):
      amount: float
      type: str
      description: str
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + Pydantic v2

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/customers.py` (سطر 15) — استفاده از schema بدون validation
- `backend/app/routers/facilities.py` (سطر 12) — استفاده از schema بدون validation

## 🌐 نقشهٔ وابستگی‌ها
تمام endpointهای POST/PUT از این schemaها استفاده می‌کنند. عدم validation باعث ورود داده‌های فاسد می‌شود.

## 🔍 Context و وضعیت فعلی
در backend/app/schemas/__init__.py و فایل‌های schemas مربوطه، بسیاری از فیلدها بدون اعتبارسنجی مناسب تعریف شده‌اند. مثلاً فیلدهای شماره تلفن، کد ملی، ایمیل و مقادیر عددی بدون validation pattern یا محدودیت طول هستند. این موضوع باعث می‌شود داده‌های نامعتبر وارد دیتابیس شوند و همچنین امکان حملات XSS از طریق فیلدهای متنی فراهم شود.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] ورودی‌های نامعتبر با خطای 422 رد شوند
- [ ] تمامی فیلدهای متنی محدودیت طول داشته باشند
- [ ] الگوهای regex برای فیلدهای حساس اعمال شده باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. به تمام فیلدهای متنی validatorهای مناسب اضافه کنید.
2. از Pydantic's Field با constraints استفاده کنید.
3. برای فیلدهای حساس (تلفن، کد ملی) از regex pattern استفاده کنید.
4. محدودیت طول برای تمام فیلدهای متنی اعمال کنید.
5. از html.escape یا Markup برای جلوگیری از XSS استفاده کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: بدون validation**

_قبل:_
```
phone: str
```

_بعد:_
```
phone: str = Field(..., pattern=r'^09\d{9}$', min_length=11, max_length=11)
```

**قبل: بدون محدودیت**

_قبل:_
```
amount: float
```

_بعد:_
```
amount: float = Field(..., gt=0, le=1_000_000_000)
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/customers" -H "Content-Type: application/json" -d '{"phone":"123"}'`
- `pytest tests/test_schemas.py -v`

## ⚠️ ریسک‌ها و موارد احتیاط
validationهای سختگیرانه ممکن است داده‌های معتبر قدیمی را رد کنند، نیاز به بررسی backward compatibility دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 8 از 16
  id: 258b7c7d-6e73-44a0-a1b7-8b7c59a77df2
  عنوان اصلی: پیاده‌سازی Rate Limiting و Brute Force Protection
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": null, "json_body": {"username": "test@example.com", "password": "wrong"}, "expected_status": 429, "required_fields": [], "json_contains": null}]
  - پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": null, "json_body": {"username": "test@example.com", "password": "wrong"}, "expected_status": 423, "required_fields": [], "json_contains": null}]
  - تمامی تلاش‌ها در Redis لاگ شوند [verify_method=static] [verify_plan={"grep_patterns": ["redis", "Redis", "r.set", "r.get", "r.expire", "r.incr"], "files_hint": ["backend/app/routers/auth.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم مدیریت Rate Limiting و Brute Force Protection

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:50-80` — `login` — بدون rate limiting و account lockout
  ```python
  @router.post("/auth/login")
  async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
      user = db.query(User).filter(User.email == credentials.email).first()
      if not user or not verify_password(credentials.password, user.hashed_password):
          raise HTTPException(status_code=401, detail="Invalid credentials")
      return {"access_token": create_access_token({"sub": user.id})}
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + Redis + slowapi

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر 15) — محل اضافه کردن تنظیمات rate limit
- `backend/app/database.py` (سطر 20) — برای ذخیره تلاش‌های ناموفق در Redis

## 🌐 نقشهٔ وابستگی‌ها
این ماژول امنیت احراز هویت را تأمین می‌کند. بدون rate limiting، کل سیستم در معرض brute force است.

## 🔍 Context و وضعیت فعلی
در backend/app/routers/auth.py هیچ محدودیت نرخی (rate limiting) برای endpointهای لاگین و ثبت‌نام وجود ندارد. این موضوع امکان حملات brute force برای حدس رمز عبور را فراهم می‌کند. همچنین هیچ مکانیزمی برای قفل کردن حساب پس از تلاش‌های ناموفق وجود ندارد. با توجه به ماهیت بانکی پروژه، این یک آسیب‌پذیری بحرانی است.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد
- [ ] پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود
- [ ] تمامی تلاش‌ها در Redis لاگ شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. از middleware rate limiting مانند slowapi یا fastapi-limiter استفاده کنید.
2. محدودیت 5 تلاش در دقیقه برای endpoint لاگین اعمال کنید.
3. پس از 10 تلاش ناموفق، حساب کاربر را به مدت 30 دقیقه قفل کنید.
4. لاگ تمام تلاش‌های ناموفق را در Redis ذخیره کنید.
5. اعلان ایمیلی برای تلاش‌های مشکوک ارسال کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: بدون محدودیت**

_قبل:_
```
@router.post("/auth/login")
async def login(...):
```

_بعد:_
```
@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `for i in {1..10}; do curl -X POST "http://localhost:8000/auth/login" -d '{"email":"test@test.com","password":"wrong"}'; done`
- `pytest tests/test_auth.py -v -k "test_rate_limiting"`

## ⚠️ ریسک‌ها و موارد احتیاط
rate limiting ممکن است کاربران واقعی را تحت تأثیر قرار دهد، نیاز به تنظیم دقیق محدودیت‌ها دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 9 از 16
  id: a4ea3f65-5f4e-47a2-b85d-e2740ed0bd38
  عنوان اصلی: رفع نشت اطلاعات حساس در لاگ‌ها و خطاها
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py, backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - در production، خطاهای 500 پیام generic نمایش دهند [verify_method=static] [verify_plan={"grep_patterns": ["def.*exception_handler.*500", "HTTPException.*500.*detail.*generic"], "files_hint": ["backend/app/main.py"]}]
  - لاگ‌ها حاوی password یا token نباشند [verify_method=static] [verify_plan={"grep_patterns": ["logging\\.(info|debug|error|warning)\\(.*password", "logging\\.(info|debug|error|warning)\\(.*token", "logger\\.(info|debug|error|warning)\\(.*password", "logger\\.(info|debug|erro]
  - exception handler تمام استثناها را catch کند [verify_method=static] [verify_plan={"grep_patterns": ["@app\\.exception_handler\\(Exception\\)", "def.*exception_handler.*Exception"], "files_hint": ["backend/app/main.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع نشت اطلاعات حساس در لاگ‌ها و خطاها

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:45-60` — `exception_handler` — نمایش مستقیم پیام خطا به کاربر
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      return JSONResponse(
          status_code=500,
          content={"detail": str(exc)}  # نشت اطلاعات خطا
      )
  ```
- `backend/app/routers/auth.py:70-75` — `login` — لاگ کردن exception بدون sanitization
  ```python
  except Exception as e:
      logger.error(f"Login failed: {e}")  # ممکن است حاوی password باشد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + structlog + Python logging

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر 20) — محل تنظیم سطح لاگ
- `backend/app/database.py` (سطر 15) — نیازمند لاگینگ امن

## 🌐 نقشهٔ وابستگی‌ها
تمامی endpointها از این exception handler استفاده می‌کنند. نشت اطلاعات می‌تواند به مهاجم کمک کند.

## 🔍 Context و وضعیت فعلی
در backend/app/main.py و backend/app/routers/*.py، استثناها و خطاها بدون sanitization به کاربر نمایش داده می‌شوند. همچنین لاگ‌ها حاوی اطلاعات حساس مانند رمز عبور و توکن‌ها هستند. این موضوع می‌تواند منجر به نشت اطلاعات محرمانه شود. در محیط production، خطاها باید generic باشند و جزئیات فنی در لاگ‌های داخلی ثبت شوند.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] در production، خطاهای 500 پیام generic نمایش دهند
- [ ] لاگ‌ها حاوی password یا token نباشند
- [ ] exception handler تمام استثناها را catch کند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد یک exception handler سفارشی که در production خطاهای generic برگرداند.
2. استفاده از structlog یا loguru برای لاگینگ امن.
3. فیلتر کردن فیلدهای حساس (password, token, secret) از لاگ‌ها.
4. تنظیم سطح لاگ به INFO در production و DEBUG در development.
5. اضافه کردن middleware برای catch all exceptions.

## 💡 نمونه‌های قبل/بعد
**قبل: نشت اطلاعات**

_قبل:_
```
content={"detail": str(exc)}
```

_بعد:_
```
content={"detail": "Internal server error"}  # در production
```

**قبل: لاگ بدون فیلتر**

_قبل:_
```
logger.error(f"Login failed: {e}")
```

_بعد:_
```
logger.error("Login failed", exc_info=True, extra={"user_id": user_id})
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/auth/login" -d '{"email":"test","password":"test"}' -v 2>&1 | grep -i "error\|exception"`
- `python -c "from backend.app.main import app; print('OK' if app.exception_handlers else 'NO HANDLER')"`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر در نحوه نمایش خطاها ممکن است debugging را برای توسعه‌دهندگان سخت‌تر کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 10 از 16
  id: 9bd29880-cb84-4bd4-bbe9-3e8afc316f09
  عنوان اصلی: Address conditional inconsistency anti-pattern
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/utils/security.py

📋 acceptance_criteria کامل:
  - ریشه anti-pattern تشخیص داده شد [verify_method=static] [verify_plan={"grep_patterns": ["if payload\\.get\\('iss'\\)", "if payload\\.get\\('aud'\\)"], "files_hint": ["backend/app/utils/security.py"]}]
  - یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["verify_access_token"], "files_hint": ["backend/app/utils/security.py"]}]
  - تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_security.py::test_verify_access_token_edge_cases", "timeout_seconds": 60}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
Anti-pattern: Conditional inconsistency

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/utils/security.py:130`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/config.py` — `security.py` این فایل را import می‌کند
- `backend/app/database.py` — `security.py` این فایل را import می‌کند
- `backend/app/models/user.py` — `security.py` این فایل را import می‌کند
- `backend/tests/conftest.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_auth.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_models.py` — این فایل `security.py` را import می‌کند (caller)

## 🔍 Context و وضعیت فعلی
در تابع verify_access_token، اعتبارسنجی issuer و audience فقط در صورت وجود (if payload.get('iss')) انجام می‌شود. این باعث می‌شود توکن‌های بدون این فیلدها (توکن‌های قدیمی) بدون بررسی issuer/audience قبول شوند، در حالی که توکن‌های جدید با این فیلدها بررسی می‌شوند. این ناهماهنگی می‌تواند امنیت را به خطر بیندازد.

📁 file: backend/app/utils/security.py (line 130)

🎯 پیشنهاد: این الگو معمولاً منطق سیستم را در شرایط لبه می‌شکند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] ریشه anti-pattern تشخیص داده شد
- [ ] یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- [ ] تست edge case نوشته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. بازنگری منطق در این نقطه و اضافه‌کردن guard/comment مناسب.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/utils/security.py`
- `ruff check backend/app/utils/security.py`
- `pytest -x`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug_fix
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 11 از 16
  id: 524a0f64-4f74-4967-a4f6-aceb7381c494
  عنوان اصلی: جلوگیری از نشت اطلاعات permission در frontend
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["AUTH_DISABLED", "permission", "role", "token"], "files_hint": ["frontend/src/lib/auth.tsx", "frontend/src/app/login/page.tsx"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align"], "files_hint": ["frontend/src/lib/auth.tsx", "frontend/src/app/login/page.tsx"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/pull_request_template.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] نشت اطلاعات permission در frontend

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در frontend/src/lib/auth.tsx، حالت AUTH_DISABLED برای توسعه وجود دارد. اگر این حالت فعال باشد، ممکن است permission info (مانند نقش کاربر یا توکن) به صورت ناخواسته در console یا network requests لو رود. همچنین در login page (frontend/src/app/login/page.tsx)، پیام‌های toast خطا ممکن است جزئیات فنی (مانند 'Invalid token' یا 'Permission denied') را فاش کنند.

## 💥 پیامد (impact)
مهاجم می‌تواند از طریق خطاهای verbose، ساختار permission system را شناسایی کرده و حملات targeted انجام دهد. در حالت AUTH_DISABLED، ممکن است کاربران بدون احراز هویت به منابع دسترسی پیدا کنند.

## 🛠 پیشنهاد رفع اولیه
در frontend/src/lib/auth.tsx، حالت AUTH_DISABLED را فقط در محیط development و با لاگ‌گیری محدود فعال کنید. در login page، پیام‌های خطا را generic نگه دارید (مثلاً 'Login failed' به جای 'Permission denied for role X').

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی AUTH_DISABLED در auth.tsx — بررسی و مستندسازی وضعیت AUTH_DISABLED در auth.tsx
  - بررسی و مستندسازی پیام‌های خطا در login page — بررسی و مستندسازی پیام‌های خطا در login page
  - بررسی و مستندسازی permission system backend — بررسی و مستندسازی permission system backend
  - محدود کردن AUTH_DISABLED به محیط development — محدود کردن AUTH_DISABLED به محیط development
  - حذف نشت permission info در console و network requests — حذف نشت permission info در console و network requests
  - Generic کردن پیام‌های خطا در login page — Generic کردن پیام‌های خطا در login page
  - اضافه کردن لاگ‌گیری امنیتی برای AUTH_DISABLED — اضافه کردن لاگ‌گیری امنیتی برای AUTH_DISABLED
  - نوشتن unit tests برای auth.tsx — نوشتن unit tests برای auth.tsx
  - نوشتن integration tests برای login flow — نوشتن integration tests برای login flow
  - مستندسازی تغییرات و به‌روزرسانی README — مستندسازی تغییرات و به‌روزرسانی README

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 12 از 16
  id: 1a8ebba4-e348-4398-87c9-784b145ae828
  عنوان اصلی: همگام‌سازی مدیریت session بک‌اند و فرانت‌اند
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["AsyncSession", "localStorage", "cookies"], "files_hint": ["backend/app/database.py", "frontend/src/lib/auth.tsx"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["session.*expire", "token.*revoke", "sync.*session"], "files_hint": ["backend/app/database.py", "frontend/src/lib/auth.tsx"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["coherence", "session", "decision"], "files_hint": ["PR_DESCRIPTION.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم coherence بین backend و frontend در مدیریت session

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

backend از AsyncSession برای دیتابیس استفاده می‌کند (backend/app/database.py)، اما frontend (frontend/src/lib/auth.tsx) session را به صورت دستی با localStorage یا cookies مدیریت می‌کند. هیچ مکانیزم sync برای انقضای session یا revoke token بین دو سمت وجود ندارد.

## 💥 پیامد (impact)
اگر session در backend منقضی شود (مثلاً timeout)، frontend همچنان کاربر را لاگین نشان می‌دهد تا زمانی که refresh page انجام شود. این باعث inconsistency و خطاهای 401 ناگهانی می‌شود.

## 🛠 پیشنهاد رفع اولیه
یک endpoint برای بررسی اعتبار token در backend اضافه کنید (مثلاً /auth/verify). frontend باید به صورت دوره‌ای (مثلاً هر 5 دقیقه) این endpoint را صدا بزند و در صورت invalid بودن token، کاربر را logout کند.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی وضعیت فعلی backend و frontend برای مدیریت session و token — مستندسازی کامل فرض‌های ناسازگار دو بخش (AsyncSession vs localStorage) انجام نشده.
  - ایجاد endpoint /auth/verify در backend برای بررسی اعتبار token — ایجاد endpoint /auth/verify در backend برای بررسی اعتبار token.
  - اضافه کردن تابع periodic token verification در frontend (auth.tsx) — اضافه کردن تابع periodic token verification در frontend (auth.tsx).
  - نوشتن تست‌های integration برای سناریوی end-to-end انقضای session — تست‌های integration برای سناریوی end-to-end انقضای session کامل نشده.
  - بررسی و مستندسازی coherence issue و اصلاحات انجام‌شده در کامیت message — نوشتن PR description جامع برای توضیح coherence issue.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 13 از 16
  id: 8366b1f5-8f1f-4476-b35d-5cca83ea025b
  عنوان اصلی: پیاده‌سازی اعتبارسنجی ورودی‌های لاگین
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["username", "password", "validation", "minLength", "maxLength", "sanitize", "escape"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/tests/test_auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "validation", "sanitize", "escape"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/app/auth.py", "backend/tests/test_auth.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/test_auth.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": ["pull_request_description.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم validation در frontend برای ورودی‌های login

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در frontend/src/app/login/page.tsx، ورودی‌های username و password بدون validation (مانند حداقل طول، نوع کاراکتر) به backend ارسال می‌شوند. backend نیز در مستندات test (backend/tests/test_auth.py) validation خاصی نشان نمی‌دهد.

## 💥 پیامد (impact)
حملات injection (مانند SQL injection یا XSS) از طریق فیلدهای لاگین امکان‌پذیر است. همچنین کاربران می‌توانند usernameهای خالی یا بسیار طولانی ارسال کنند که باعث crash یا رفتار غیرمنتظره شود.

## 🛠 پیشنهاد رفع اولیه
در frontend، validation سمت کلاینت (مثلاً username حداقل 3 کاراکتر، password حداقل 8 کاراکتر) اضافه کنید. در backend، validation سمت سرور با کتابخانه‌ای مانند pydantic یا marshmallow انجام دهید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی وضعیت فعلی فایل‌های مرتبط با validation در frontend و backend — بررسی کامل فایل‌های مرتبط با validation در frontend و backend انجام نشده
  - اضافه کردن validation سمت کلاینت برای فیلد username در فرم لاگین — validation سمت کلاینت برای username اضافه نشده
  - اضافه کردن validation سمت کلاینت برای فیلد password در فرم لاگین — validation سمت کلاینت برای password اضافه نشده
  - اضافه کردن مدل Pydantic برای validation درخواست لاگین در backend — مدل Pydantic LoginRequest در backend ایجاد نشده
  - به‌روزرسانی endpoint لاگین در backend برای استفاده از مدل Pydantic — endpoint لاگین از مدل Pydantic استفاده نمی‌کند
  - نوشتن تست واحد برای مدل Pydantic LoginRequest — تست واحد برای مدل Pydantic LoginRequest نوشته نشده
  - نوشتن تست واحد برای validation سمت کلاینت (اختیاری اما توصیه شده) — تست واحد برای validation سمت کلاینت نوشته نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 14 از 16
  id: bc3f557f-9e02-4c09-9e3f-ff795c54fba5
  عنوان اصلی: پیکربندی HTTPS، HSTS و CORS
  اولویت اصلی: medium
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py

📋 acceptance_criteria کامل:
  - HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد [verify_method=static] [verify_plan={"grep_patterns": ["Strict-Transport-Security", "max-age=31536000"], "files_hint": ["backend/app/main.py"]}]
  - CORS فقط دامنه‌های مجاز را اجازه دهد [verify_method=static] [verify_plan={"grep_patterns": ["CORSMiddleware", "allow_origins"], "files_hint": ["backend/app/main.py"]}]
  - در production، HTTP به HTTPS redirect شود [verify_method=static] [verify_plan={"grep_patterns": ["redirect.*http", "RedirectMiddleware", "HTTP.*HTTPS"], "files_hint": ["backend/app/main.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم استفاده از HTTPS و HSTS headers

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:1-20` — `app` — فقدان کامل middlewareهای امنیتی
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  
  app = FastAPI(title="ALLIN1 API")
  
  # CORS middleware وجود ندارد
  # Security headers middleware وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + CORSMiddleware + TrustedHostMiddleware

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر 10) — محل اضافه کردن تنظیمات CORS و HTTPS
- `render.yaml` (سطر 5) — تنظیمات deployment برای HTTPS

## 🌐 نقشهٔ وابستگی‌ها
این middlewareها بر تمام درخواست‌های HTTP تأثیر می‌گذارند و امنیت ارتباط را تضمین می‌کنند.

## 🔍 Context و وضعیت فعلی
در backend/app/main.py هیچ middleware برای强制 HTTPS یا اضافه کردن HSTS headers وجود ندارد. همچنین CORS middleware پیکربندی نشده است. این موضوع باعث می‌شود ارتباط بین کلاینت و سرور رمزنگاری نشود و حملات man-in-the-middle ممکن باشد. برای یک سیستم بانکی، این یک نقص امنیتی جدی است.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد
- [ ] CORS فقط دامنه‌های مجاز را اجازه دهد
- [ ] در production، HTTP به HTTPS redirect شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. اضافه کردن middleware برای redirect HTTP به HTTPS.
2. اضافه کردن HSTS header با max-age=31536000.
3. پیکربندی CORS با لیست سفید دامنه‌های مجاز.
4. استفاده از SSL/TLS certificate در production.
5. اضافه کردن Security Headers (X-Content-Type-Options, X-Frame-Options, CSP).

## 💡 نمونه‌های قبل/بعد
**قبل: بدون middleware**

_قبل:_
```
app = FastAPI()
# هیچ middleware امنیتی اضافه نشده
```

_بعد:_
```
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -I http://localhost:8000/ | grep -i "strict-transport-security\|content-security-policy"`
- `curl -I https://yourdomain.com/ | grep -i "strict-transport-security"`

## ⚠️ ریسک‌ها و موارد احتیاط
تنظیمات نادرست CORS می‌تواند دسترسی frontend را قطع کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: medium
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 15 از 16
  id: 7182df34-8ad1-495b-8e65-f2f03773b735
  عنوان اصلی: افزودن قابلیت Refresh و Blacklist توکن
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد [verify_method=api_response] [verify_plan={"method": "POST", "path": "/auth/logout", "headers": {"Authorization": "Bearer <valid_token>"}, "json_body": null, "expected_status": 200, "required_fields": [], "json_contains": null}]
  - endpoint /auth/refresh وجود داشته باشد و کار کند [verify_method=api_response] [verify_plan={"method": "POST", "path": "/auth/refresh", "headers": {"Authorization": "Bearer <expired_token>"}, "json_body": null, "expected_status": 200, "required_fields": ["access_token"], "json_contains": nul]
  - توکن‌های revoked در middleware بررسی شوند [verify_method=static] [verify_plan={"grep_patterns": ["blacklist", "revoked", "check_blacklist"], "files_hint": ["backend/app/middleware.py", "backend/app/routers/auth.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم مدیریت صحیح Session و Token Expiry

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:80-100` — `logout` — logout واقعی پیاده‌سازی نشده
  ```python
  @router.post("/auth/logout")
  async def logout(token: str = Depends(oauth2_scheme)):
      # هیچ عملی انجام نمی‌شود
      return {"message": "Logged out"}
  ```
- `backend/app/routers/auth.py:100-120` — `refresh_token` — فقدان refresh token
  ```python
  # endpoint refresh_token وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + JWT + Redis

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/database_manager.py` (سطر 30) — برای ذخیره توکن‌های revoked در Redis
- `backend/app/main.py` (سطر 25) — برای اضافه کردن blacklist check در middleware

## 🌐 نقشهٔ وابستگی‌ها
این ماژول مدیریت session کاربران را بر عهده دارد. عدم وجود logout واقعی امنیت را کاهش می‌دهد.

## 🔍 Context و وضعیت فعلی
در backend/app/routers/auth.py، توکن‌های JWT expiry دارند اما مکانیزم refresh token پیاده‌سازی نشده است. همچنین توکن‌های revoked در بلاک‌لیست ذخیره نمی‌شوند و logout واقعی وجود ندارد. کاربران نمی‌توانند session خود را ببندند و توکن‌ها تا زمان expiry معتبر می‌مانند. این موضوع امنیت session را کاهش می‌دهد.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد
- [ ] endpoint /auth/refresh وجود داشته باشد و کار کند
- [ ] توکن‌های revoked در middleware بررسی شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. پیاده‌سازی refresh token با عمر 7 روز.
2. ایجاد endpoint /auth/refresh.
3. ذخیره توکن‌های revoked در Redis با TTL.
4. پیاده‌سازی logout واقعی با invalidate کردن توکن.
5. اضافه کردن blacklist check در middleware احراز هویت.

## 💡 نمونه‌های قبل/بعد
**قبل: logout بدون عملیات**

_قبل:_
```
@router.post("/auth/logout")
async def logout(token: str):
    return {"message": "Logged out"}
```

_بعد:_
```
@router.post("/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    await redis.set(f"blacklist:{token}", "revoked", ex=3600)
    return {"message": "Logged out successfully"}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/auth/logout" -H "Authorization: Bearer <token>"`
- `curl -X POST "http://localhost:8000/auth/refresh" -d '{"refresh_token":"..."}'`

## ⚠️ ریسک‌ها و موارد احتیاط
اضافه کردن Redis dependency ممکن است پیچیدگی deployment را افزایش دهد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 16 از 16
  id: d5caf9d0-81a5-491a-99e4-bfeee0b2acda
  عنوان اصلی: مدیریت خطاهای دیتابیس در auth pipeline
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["retry", "fallback", "connection.*error", "timeout", "retry_decorator"], "files_hint": ["backend/app/database.py", "backend/app/auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground.truth", "align", "retry.*mechanism", "fallback.*implement"], "files_hint": ["backend/app/database.py", "backend/app/auth.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["why.*decision", "rationale", "reason.*chosen"], "files_hint": ["PR description"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم مدیریت خطاهای دیتابیس در auth pipeline

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در backend/app/database.py، اتصال به دیتابیس با SSL و pool size مدیریت می‌شود، اما هیچ fallback یا retry mechanism برای خطاهای اتصال (مانند timeout یا connection reset) وجود ندارد. این می‌تواند باعث failure در عملیات‌های auth شود.

## 💥 پیامد (impact)
اگر دیتابیس به طور موقت در دسترس نباشد، کاربران نمی‌توانند لاگین یا ثبت‌نام کنند و خطای 500 دریافت می‌کنند. این downtime غیرضروری است.

## 🛠 پیشنهاد رفع اولیه
یک retry decorator برای session creation اضافه کنید (مثلاً 3 بار تلاش با exponential backoff). همچنین یک health check endpoint برای دیتابیس ایجاد کنید تا frontend بتواند وضعیت را به کاربر نشان دهد.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی اتصال دیتابیس در auth pipeline — بررسی و مستندسازی کامل وضعیت فعلی اتصال دیتابیس در auth pipeline
  - ایجاد retry decorator برای session creation با exponential backoff — ایجاد retry decorator برای session creation با exponential backoff
  - ایجاد health check endpoint برای دیتابیس در backend — ایجاد health check endpoint برای دیتابیس (GET /health/db)
  - اتصال health check endpoint به frontend برای نمایش وضعیت دیتابیس — اتصال health check endpoint به frontend برای نمایش وضعیت دیتابیس
  - نوشتن تست‌های واحد برای retry decorator — نوشتن تست‌های واحد برای retry decorator
  - نوشتن تست‌های integration برای health check endpoint — نوشتن تست‌های integration برای health check endpoint
  - نوشتن تست‌های end-to-end برای سناریوی قطع دیتابیس در auth — نوشتن تست‌های end-to-end برای سناریوی قطع دیتابیس در auth

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 56ab7fb9-d9b6-4cab-a0a3-98e3970018e9, 62de5589-02b3-4084-8051-a0047f6735a9, 42cbcd99-7b21-4491-816e-cad31d6791cf, ea641ffd-df5b-46e4-8d2f-9f1586208457, ae87a6ca-2f66-469b-b263-79b1785240b3, 84bedb2d-3590-4311-ab28-4c105d6d8f4c, 568f1abe-58ef-40bc-ba40-b9fa76d4ab1a, 258b7c7d-6e73-44a0-a1b7-8b7c59a77df2, a4ea3f65-5f4e-47a2-b85d-e2740ed0bd38, 9bd29880-cb84-4bd4-bbe9-3e8afc316f09, 524a0f64-4f74-4967-a4f6-aceb7381c494, 1a8ebba4-e348-4398-87c9-784b145ae828, 8366b1f5-8f1f-4476-b35d-5cca83ea025b, bc3f557f-9e02-4c09-9e3f-ff795c54fba5, 7182df34-8ad1-495b-8e65-f2f03773b735, d5caf9d0-81a5-491a-99e4-bfeee0b2acda`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Prompt

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

🔗 **وابستگی‌ها و همگام‌سازی (بسیار حیاتی — هرگز skip نکن):**

این بخش از همهٔ بخش‌های دیگرِ این یادداشت **مهم‌تر** است. اگر نقض شود،
نتیجهٔ کار ممکن است مشروع به‌نظر برسد ولی در عمل بخش‌های دیگر سیستم را عقب
بیندازد، broken reference تولید کند، یا منجر به data corruption شود.

پیش از و حین تغییر، تمام وابستگی‌ها را در **چهار جهت** به‌طور **کامل و
بدون هیچ خلاصه‌سازی** شناسایی و همگام کن:

**۱. وابستگی‌های upstream (این تسک به چه چیزهایی متکی است):**
- چه فایل‌ها، توابع، کلاس‌ها، API endpoint ها، schema های دیتابیس،
  env vars، یا config هایی که این تسک نیاز دارد؟
- آیا قرار است چیزی را ویرایش/حذف کنی که جای دیگر (signature، رفتار،
  return type، side effect) از آن انتظار خاصی می‌رود؟
- اگر dependency جدیدی اضافه می‌کنی، آیا با dependencyهای موجود تداخل
  دارد (نسخه، compat، lock file)؟

**۲. وابستگی‌های downstream (چه چیزهایی به این تسک متکی‌اند):**
- چه فایل‌ها، توابع، تست‌ها، migrations، docs، یا UI component هایی از
  کدی که داری ویرایش/اضافه/حذف می‌کنی **استفاده می‌کنند**؟
- با grep و reference search **همه‌ی** call sites، importها، subclassها،
  reference های مستقیم و غیرمستقیم را پیدا کن — نه فقط چند مورد اصلی.
- خصوصاً برای حذف یا rename: هیچ broken reference نباید باقی بماند.

**۳. وابستگی‌های cross-tier (بسیار مهم — هرگز فقط یک لایه را نبین):**

تسک شما ممکن است از backend، frontend، database، worker، یا هر tier
دیگری شروع شده باشد. ولی تغییرات تقریباً همیشه روی tier های دیگر هم
اثر می‌گذارند. **مستقل از اینکه تسک از کدام tier است**، این چک‌های دو
طرفه را همیشه انجام بده:

🔁 **اگر backend را تغییر دادی** (API، service، model، route):
  → frontend: کدام component/page/hook این endpoint یا data shape را
    مصرف می‌کند؟ type definition، state shape، error handling، loading
    state، form validation، URL routing همگی باید همگام شوند.
  → mobile/SDK/client library (اگر پروژه دارد): همان داستان frontend.
  → database: آیا migration لازم است؟ آیا rollback امن است؟
  → background workers: آیا event producer/consumer ها تحت تأثیرند؟
  → rate limit، auth، CORS، CSP: آیا رفتار جدید پشتیبانی می‌شود؟

🔁 **اگر frontend را تغییر دادی** (component، form، state، route):
  → backend: آیا endpoint جدید/تغییریافته لازم است؟ آیا data shape ای
    که ارسال می‌شود با schema سرور سازگار است؟
  → backend validation: آیا برای ورودی‌های جدید UI کافی است؟
  → permissions/RBAC: آیا feature جدید نیاز به role check جدید دارد؟
  → analytics/tracking: آیا event های جدید باید در backend log شوند؟
  → SEO/SSR: آیا تغییر route نیاز به sitemap/meta tags جدید دارد؟

🔁 **اگر database/migration را تغییر دادی**:
  → backend models (ORM، Pydantic، dataclasses) همگی به‌روزند؟
  → query های raw SQL یا ORM queries با schema جدید سازگارند؟
  → seed data، fixtures، factory functions تست‌ها به‌روزند؟
  → frontend: آیا data shape جدید در UI به‌درستی render می‌شود؟
  → rollback migration نوشته شده و امن است؟

🔁 **اگر API contract یا event schema را تغییر دادی** (REST، GraphQL،
   WebSocket، gRPC، Kafka، …):
  → OpenAPI/GraphQL schema/proto file آپدیت شد؟
  → همه‌ی consumer ها (client، subscriber، webhook، external API
    user) با version جدید سازگارند؟
  → backward compatibility حفظ شده یا migration path روشن است؟
  → versioning header/path اگر breaking change است؟

🔁 **اگر infrastructure یا config را تغییر دادی** (Dockerfile، CI، Render
   config، env، secrets):
  → README setup/installation section به‌روزه؟
  → `.env.example` با env vars جدید آپدیت شد؟
  → deploy script یا CI workflow هم تغییر کرد؟
  → docs/architecture یا diagram های infrastructure به‌روزند؟

⚠️ **هرگز فقط یک tier را تغییر نده و فرض کنی بقیه خودکار همگام می‌شوند.**
   حتی برای تغییرات به‌ظاهر «کوچک»، چک کن.

**۴. وابستگی‌های جانبی (artifacts که همیشه چک شوند):**

تغییرات کد همیشه روی این artifact ها اثر دارند. **همه را** بررسی و
به‌روز کن — مستندات اولویت **بالا** دارد چون فراموش‌شدنی‌ترین است.

  📝 **مستندات** (همیشه چک کن — حتی برای تغییر کوچک کد):
    - README.md (شرح، setup، نمونه‌های استفاده، badge ها)
    - CHANGELOG.md / RELEASE_NOTES.md
    - docs/ folder (architecture، API reference، user guides، runbooks)
    - inline docstrings/کامنت‌های توابع و کلاس‌های تغییریافته
    - OpenAPI/Swagger annotations، JSDoc/TSDoc
    - architecture diagrams (اگر component اضافه/حذف شد)
    - migration guides (اگر breaking change است)

  🌍 **مستندات کاربر**:
    - i18n files و translation keys
    - UI labels، tooltip ها، help text، error messages
    - in-app onboarding (اگر flow جدید است)

  🧪 **تست‌ها**:
    - unit tests (همه‌ی فایل‌های مرتبط — حتی اگر «بی‌ربط» به‌نظر می‌رسد)
    - integration tests
    - e2e tests (Playwright/Cypress/Selenium)
    - snapshot tests (اگر UI تغییر کرد)
    - contract tests (Pact یا مشابه)
    - performance benchmarks (اگر behavior performance-sensitive تغییر کرد)

  🧬 **type definitions و contracts**:
    - .d.ts files
    - Pydantic models، dataclasses
    - Protobuf/Avro/Thrift schemas
    - GraphQL schema definitions
    - JSON Schemas

  🏗 **infrastructure و config**:
    - Dockerfile، docker-compose.yml
    - Kubernetes manifests
    - Render/Vercel/Netlify config
    - GitHub Actions / GitLab CI workflows
    - environment templates (.env.example، .env.sample)
    - feature flags (LaunchDarkly، GrowthBook، config)

  📊 **monitoring و observability**:
    - logging keys (اگر اضافه/حذف شد، log parser ها هم به‌روز شوند)
    - metric names (Prometheus، Datadog)
    - tracing spans
    - alert rules و dashboards
    - error tracking (Sentry rules، groupings)

  🔐 **security**:
    - auth rules (rate limit، CORS، CSP، HSTS)
    - permissions/RBAC config
    - secrets rotation policies
    - audit log events (اگر action جدید اضافه شد)

  💾 **caches و serialization**:
    - cache keys و TTL (اگر data shape یا lifecycle تغییر کرد)
    - serializer formats (Redis، session storage)
    - browser storage (localStorage، IndexedDB schemas)

**قانون مطلق همگام‌سازی:**
- هر چیزی که در (۱)، (۲)، (۳)، یا (۴) شناسایی شد، در **همان workflow
  این تسک** همگام و به‌روز شود. هرگز برای بعد رها نکن.
- اگر یک فایل/تست/docs نسبت به تغییر شما عقب بماند، در بهترین حالت bug،
  در بدترین حالت مشکل امنیتی یا data corruption تولید می‌کند.
- تغییرات همگام‌سازی می‌توانند در commit جداگانه باشند (در همان task)،
  ولی نباید skip شوند یا به «refactor آینده» سپرده شوند.

**هرگز این جمله‌ها قابل قبول نیست:**
- ❌ «بعداً پیداش می‌کنم»
- ❌ «احتمالاً جای دیگه‌ای استفاده نمی‌شه»
- ❌ «این یه refactor جداگانه‌ست — out of scope»
- ❌ «فقط فایل‌های اصلی رو بررسی کردم»
- ❌ «حدس می‌زنم چیزی بهش وابسته نیست»
- ❌ «دامنه‌ی وابستگی‌ها رو خلاصه کردم» — هرگز خلاصه نکن
- ❌ «این task فقط backend است؛ frontend مشکل خودش» — هرگز
- ❌ «این task فقط frontend است؛ backend از قبل کار می‌کند» — هرگز ثابت نکرده
- ❌ «مستندات بعداً به‌روز می‌شن» — همیشه same-task همگام شوند
- ❌ «testها رو نگاه نکردم چون فقط یه تغییر کوچیک بود»

**در commit message یا PR description**، دامنهٔ وابستگی‌های شناسایی‌شده و
همگام‌شده را به‌طور explicit و **per-tier** بنویس. مثال:
```
Dependencies synced:
- upstream: User model schema, auth middleware
- downstream: 3 API endpoints, 5 frontend components, 12 tests
- cross-tier (backend → frontend): UserProfile.tsx, useUser.ts hook,
  api-types.ts (TS definitions)
- cross-tier (backend → infra): .env.example added NEW_AUTH_SCOPES
- side artifacts: OpenAPI spec, README API section, i18n keys for
  new errors, Sentry alert rule for new error code
```
اگر هیچ وابستگی پیدا نکردی در هر کدام از چهار جهت، صریحاً بنویس:
«بررسی شد — هیچ وابستگی upstream / downstream / cross-tier (backend↔
frontend↔db↔infra) / side شناسایی نشد» تا مشخص باشد بررسی **انجام شده**
نه اینکه فراموش شده.

📋 **مدیریت TO-DO برای اقدامات دستی کاربر (همیشه چک کن):**

⚠️ **هشدار بحرانی — قاعدهٔ ضد-فرار:** TO-DO فقط برای کارهایی است که
**واقعاً غیرممکن** برای agent است (نیاز به انسان مطلق)، نه برای کارهایی
که «بزرگ‌اند»، «وقت می‌برند»، یا «نیازمند fixture/setup» هستند. اگر یک
agent در یک سشن بیش از **۲۰٪ از تسک‌ها** را با TO-DO ببندد، یعنی از کار
فرار می‌کند — این الگو در سشن‌های قبلی **مشاهده** شده و الان ممنوع است.

✅ **فقط برای این موارد TO-DO بساز** (لیست بسته — هرچه خارج این لیست
ممنوع است):

  ۱. **Credential/secret که فقط کاربر دارد**:
     - تنظیم API key واقعی در پنل ادمین خارجی (Render، AWS، Stripe، …)
     - تأیید OAuth client روی console آن سرویس
     - paste کردن webhook secret که فقط بعد از ساخت در dashboard ظاهر می‌شود

  ۲. **Account/billing روی سرویس خارجی که کاربر باید عضو شود**:
     - ساخت account جدید روی Stripe/SendGrid/Twilio/Google Cloud
     - تأیید verification شماره یا ID
     - فعال‌سازی subscription پولی

  ۳. **داده/asset خصوصی که فقط کاربر دارد**:
     - آپلود لوگو/تصویر/فونت برند
     - paste کردن داده‌ای که در محل کار کاربر است
     - import داده‌ای که فقط روی device کاربر است

  ۴. **تصمیم سلیقه‌ای/حقوقی/کسب‌وکار**:
     - انتخاب رنگ‌بندی نهایی یا تم
     - متن دقیق Terms of Service / Privacy Policy
     - تعرفهٔ قیمت‌گذاری
     - نام نهایی برند یا دامنه

⛔ **هرگز TO-DO نکن برای** (لیست سیاه — هر چیزی که در این لیست است
**قابل اجرا** توسط agent است، حتی اگر بزرگ یا چندبخشی باشد):

  ❌ UI component / page / dashboard (هر فریم‌ورک: React, Vue, Angular,
     Svelte، حتی اگر معماری بزرگ دارد) — می‌توانی stub اولیه + state
     management + layout + استایل بسازی
  ❌ "نیازمند Google Drive / Stripe / Twilio API" — می‌توانی **client
     stub** با abstraction layer بسازی که با env var واقعی plug-in شود؛
     کد integration یعنی پیاده‌سازی، نه TO-DO
  ❌ "feature بزرگ، چند روز کار می‌برد" — اندازه دلیل defer نیست؛ کوچک
     شروع کن، iterate کن، در همین سشن کامل کن
  ❌ Celery / background worker / scheduler — یک task ساده + register
     می‌توانی بسازی
  ❌ Migration / model / schema — حتی اگر فیلد جدید نیاز دارد، اضافه کن
  ❌ REST endpoint / GraphQL resolver / WebSocket route — هرگز TO-DO
  ❌ test (unit/integration/e2e) — همیشه قابل نوشتن
  ❌ Documentation / README / API docs — همیشه قابل نوشتن
  ❌ Config file / .env.example / Dockerfile / CI workflow — همیشه قابل
     نوشتن
  ❌ "می‌توانستی .tsx ولی repo .jsx است" — از .jsx استفاده کن، TO-DO نکن
  ❌ "نیازمند فیلد X در مدل دیگر" — اضافه کن فیلد را، TO-DO نکن
  ❌ "تصمیم admin-vs-user-scoped" — پرامپت اولیه scope را معلوم کرده،
     یا با محتاطانه‌ترین تفسیر پیش برو
  ❌ "credential در production هنوز ست نیست" — این TO-DO ساده برای
     تنظیم env var است (مورد ۱ بالا)، نه دلیل برای defer کردن کد
  ❌ "نیازمند verification از کاربر" — اگر اقدام واقعی غیرممکن نیست،
     پیش برو
  ❌ هر چیزی که در یک کامنت `# TODO` معمولی نوشته می‌شد — این فایل
     TO-DO نیست، کامنت inline است

🔬 **قاعدهٔ «حداقل تلاش» قبل از TO-DO**: قبل از TO-DO کردن یک AC، **اثبات
کن** که قابل انجام نیست:

  ۱. آیا می‌توانم یک stub/placeholder بسازم که با env واقعی plug-in شود؟
     → اگر بله، بساز و TO-DO نکن
  ۲. آیا می‌توانم برای این بخش یک test (حتی mock-based) بنویسم؟
     → اگر بله، بنویس و TO-DO نکن
  ۳. آیا می‌توانم abstraction/interface را تعریف کنم، حتی اگر backend
     واقعی نیست؟ → اگر بله، تعریف کن و TO-DO نکن
  ۴. آیا فقط یک حالت سلیقه‌ای/decision کاربر در میان است؟
     → فقط آن یک decision را TO-DO کن، نه کل feature را

اگر یکی از این چهار راه‌حل ممکن بود ولی به TO-DO رفتی، **اعتبار شما از
بین می‌رود**.

📊 **آستانهٔ TO-DO per session**: در یک حلقهٔ اجرای N تسک، اگر بیشتر از
**۲۰٪** تسک‌ها فایل TO-DO ساختی، خودت در گزارش پایانی صریحاً اعلام کن:

  "⚠️ نسبت TO-DO من {K}/{N} = {%} است که از آستانهٔ ۲۰٪ بالاتر است.
   احتمالاً برخی از این TO-DO ها قابل اجرا بودند ولی من فرار کردم.
   لیست TO-DO ها را کاربر باید بازبینی کند که آیا واقعاً Manual-required
   بودند یا agent ضعیف کار کرده."

**یادآوری همیشگی:** اگر در آینده قابلیت‌های شما گسترش پیدا کرد و توانستید
یکی از موارد لیست سفید را خودکار انجام دهید (مثلاً managed credential
injection، یا integration پولی automate شود)، انجام دهید و TO-DO نسازید.
لیست سفید بسته است ولی **بسته از پایین** (می‌تواند کوچک‌تر شود اگر
قابلیت‌ها رشد کنند، ولی هرگز بزرگ‌تر نشود برای فرار).

**اگر هیچ بخش Manual-required نبود (تمام تسک Auto-capable است)**:
  → فایل TO-DO **نساز**. فولدر TO-DO/ باید پاک و معنادار بماند.
  → اگر برای این task از قبل `TO-DO/todo-task-{task_id_first_8}.md` بود
     (یعنی در run قبلی نیاز به دخالت کاربر بود ولی الان نه): فایل قدیمی
     را پاک کن و entry را از `TO-DO/_index.json` حذف کن.

**اگر بخش Manual-required دارد** (همه‌جانبه یا hybrid):
  1. فولدر TO-DO/ را در ریشه ریپو ایجاد کن اگر نیست
  2. فایل `TO-DO/todo-task-{task_id_first_8}.md` بساز با front-matter
     شامل: task_id, task_title, execution_priority, created_at,
     updated_at, status: "pending"
     و در بدنه: «چرا این فایل ساخته شد»، «وضعیت بخش‌های خودکار»
     (commit ها reference)، «کارهایی که باید انجام دهی» با اولویت
     بالا/متوسط/پایین به ترتیب، «وقتی این کارها را تمام کردی»
  3. `TO-DO/_index.json` را با **merge** آپدیت کن (نه overwrite):
     - فایل موجود را بخوان
     - entry های orphan (فایلشان پاک شده) را حذف کن
     - entry این task را اضافه/replace کن
     - بر اساس execution_priority صعودی مرتب کن
     - ساختار: `{"version":1, "generated_at": ISO, "total": N, "items": [...]}`
  4. این تغییرات TO-DO را در **همان commit کد** شامل کن (نه commit جداگانه)

⛔ **ممنوعات مطلق TO-DO**:
  ❌ ساختن TO-DO برای کاری که می‌توانستی خودت انجام دهی (شلوغی فولدر)
  ❌ overwrite کردن `TO-DO/_index.json` بدون merge (data loss)
  ❌ نگه‌داشتن entry هایی که فایل‌شان پاک شده (broken reference)
  ❌ فراموش کردن نوشتن «خروجی مورد انتظار» در هر آیتم TO-DO

این بخش الزامی است. حتی اگر فکر می‌کنی "این تسک کاملاً auto است و نیازی
به TO-DO نیست"، صریحاً در commit message یا report بنویس:
"بررسی شد — این تسک هیچ بخش Manual-required ندارد، TO-DO ساخته نشد."

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

🔁 **Commit + Push فوری per-task (بسیار مهم برای جریان کار صحیح):**

پس از اتمام پیاده‌سازی این تسک، **بلافاصله** commit کن و **همان موقع**
به default branch (main/master) push کن. سپس به تسک بعدی برو.

✓ چرا این قانون حیاتی است:
  - تسک‌های بعدی ممکن است به فایل‌ها/تغییراتی که این تسک ایجاد کرده
    نیاز داشته باشند. اگر push نکنی، `git pull` بعدی آن‌ها را نمی‌بیند.
  - جمع‌کردن تغییرات چند تسک منجر به conflict های بزرگ می‌شود.
  - اگر در میانه fail کنی، task های push شده ضایع نمی‌شوند.

⛔ ممنوع: "همه task ها را تمام می‌کنم بعد یک‌جا push می‌زنم"
⛔ ممنوع: branch جدا برای task — مستقیم به default branch
⛔ ممنوع: task بعدی بدون push کامل task قبلی

---

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
  - تمامی تست‌های احراز هویت با موفقیت پاس شوند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع آسیب‌پذیری بحرانی JWT با الگوریتم none و کلید ضعیف

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:1-50` — `create_access_token` — کلید ثابت و ضعیف، عدم بررسی الگوریتم none
  ```python
  from jose import jwt
  SECRET_KEY = "your-secret-key"
  ALGORITHM = "HS256"
  def create_access_token(data: dict):
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(minutes=30)
      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
      return encoded_jwt
  ```
- `backend/app/main.py:20-40` — `verify_token` — عدم استفاده از options برای امنیت بیشتر
  ```python
  def verify_token(token: str = Depends(oauth2_scheme)):
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          return payload
      except JWTError:
          raise HTTPException(status_code=401)
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + python-jose + JWT + OAuth2

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/.env.example` (سطر 5) — شامل کلید پیش‌فرض ضعیف
- `backend/app/config.py` (سطر 10) — محل بارگذاری تنظیمات JWT

## 🌐 نقشهٔ وابستگی‌ها
سیستم احراز هویت کل پروژه به این ماژول وابسته است. تمام endpointهای محافظت‌شده از این middleware استفاده می‌کنند.

## 🔍 Context و وضعیت فعلی
در فایل backend/app/routers/auth.py از کتابخانه python-jose با الگوریتم HS256 و یک کلید ثابت و ضعیف ('your-secret-key' در .env.example) استفاده شده است. این پیکربندی امکان حملات signature bypass (CVE-2022-23529) و brute-force را فراهم می‌کند. همچنین middleware احراز هویت در backend/app/main.py بررسی نمی‌کند که آیا توکن با الگوریتم 'none' امضا شده است یا خیر. این آسیب‌پذیری به مهاجم اجازه می‌دهد توکن‌های جعلی با دسترسی ادمین تولید کند.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] توکن با الگوریتم none توسط middleware رد شود
- [ ] کلید JWT از متغیر محیطی خوانده شود و در کد هاردکد نباشد
- [ ] تمامی تست‌های احراز هویت با موفقیت پاس شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. کلید JWT را با یک کلید 256 بیتی تصادفی از متغیر محیطی JWT_SECRET_KEY جایگزین کنید.
2. در تنظیمات JWT، پارامتر 'options' را با {'verify_signature': True, 'require': ['exp', 'iat']} تنظیم کنید.
3. الگوریتم‌های مجاز را به ['HS256'] محدود کنید.
4. از کتابخانه 'authlib' یا 'PyJWT' به جای python-jose استفاده کنید که امن‌تر است.
5. middleware احراز هویت را برای رد توکن‌های با الگوریتم none به‌روزرسانی کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: کلید ثابت در کد**

_قبل:_
```
SECRET_KEY = "your-secret-key"
```

_بعد:_
```
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
```

**قبل: decode بدون options**

_قبل:_
```
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

_بعد:_
```
payload = jwt.decode(token, SECRET_KEY, options={"verify_signature": True, "require": ["exp", "iat"]}, algorithms=["HS256"])
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `python -c "from jose import jwt; token = jwt.encode({'sub':'admin'}, '', algorithm='none'); print('VULNERABLE' if jwt.decode(token, '', options={'verify_signature': False}) else 'FIXED')"`
- `pytest tests/test_auth.py -v -k "test_jwt_security"`

## ⚠️ ریسک‌ها و موارد احتیاط
پس از تغییر کلید، تمام توکن‌های قبلی نامعتبر می‌شوند و کاربران باید دوباره لاگین کنند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: critical
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 16
  id: 62de5589-02b3-4084-8051-a0047f6735a9
  عنوان اصلی: حذف AUTH_DISABLED و الزام احراز هویت
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/utils/security.py

📋 acceptance_criteria کامل:
  - بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/customers", "headers": null, "json_body": null, "expected_status": 401, "required_fields": [], "json_contains": null}]
  - تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود [verify_method=static] [verify_plan={"grep_patterns": ["AUTH_DISABLED"], "files_hint": ["backend/app/utils/security.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
AUTH_DISABLED=true باعث دور زدن کامل احراز هویت می‌شود

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/utils/security.py:193-219` — `get_current_user` — بلاک شرطی که احراز هویت را کاملاً دور می‌زند
  ```python
  async def get_current_user(
      db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
  ) -> "User":
      if settings.AUTH_DISABLED:
          result = await db.execute(select(User).where(User.username == "demo"))
          user = result.scalar_one_or_none()
          if user is None:
              user = User(
                  username="demo",
                  email="demo@example.com",
                  hashed_password=hash_password("demo"),
                  full_name="Demo User",
                  is_active=True,
              )
              db.add(user)
              await db.commit()
              await db.refresh(user)
          return user
  ```
- `backend/app/utils/security.py:243-269` — `get_optional_current_user` — همان رفتار در تابع دوم
  ```python
  async def get_optional_current_user(
      db: AsyncSession = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
  ) -> Optional["User"]:
      if settings.AUTH_DISABLED:
          result = await db.execute(select(User).where(User.username == "demo"))
          user = result.scalar_one_or_none()
          if user is None:
              user = User(
                  username="demo",
                  ...
              )
              db.add(user)
              await db.commit()
              await db.refresh(user)
          return user
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + JWT + SQLAlchemy async session

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/config.py` (سطر 1) — محل تعریف settings.AUTH_DISABLED
- `docker-compose.prod.yml` (سطر 1) — محل احتمالی تنظیم متغیر محیطی
- `render.yaml` (سطر 1) — محل احتمالی تنظیم متغیر محیطی
- `backend/app/database.py` — `security.py` این فایل را import می‌کند
- `backend/app/models/user.py` — `security.py` این فایل را import می‌کند
- `backend/tests/conftest.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_auth.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_models.py` — این فایل `security.py` را import می‌کند (caller)

## 🌐 نقشهٔ وابستگی‌ها
این تابع توسط تمام روترهای backend (auth, customers, facilities, stats) از طریق Depends استفاده می‌شود.

## 🔍 Context و وضعیت فعلی
در فایل backend/app/utils/security.py، خط 204، اگر settings.AUTH_DISABLED برابر True باشد، تابع get_current_user بدون بررسی توکن، کاربر demo را برمی‌گرداند. این یعنی هر درخواستی بدون نیاز به توکن معتبر می‌تواند به endpointهای محافظت‌شده دسترسی پیدا کند. این یک backdoor عمدی است که در محیط production نباید وجود داشته باشد. همچنین در خط 254 همین فایل، تابع get_optional_current_user نیز همین رفتار را دارد.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند
- [ ] تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱. متغیر محیطی AUTH_DISABLED را از settings حذف کنید یا مقدار پیش‌فرض آن را False قرار دهید. ۲. در docker-compose.prod.yml و render.yaml این متغیر را حذف کنید. ۳. یک middleware اضافه کنید که در محیط production اگر AUTH_DISABLED=True بود، اخطار لاگ بدهد و از اجرا جلوگیری کند.

## 💡 نمونه‌های قبل/بعد
**حذف شرط AUTH_DISABLED**

_قبل:_
```
if settings.AUTH_DISABLED:
    return demo_user
# ادامه کد
```

_بعد:_
```
# حذف کامل بلاک if settings.AUTH_DISABLED
# ادامه کد
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 16
  id: 42cbcd99-7b21-4491-816e-cad31d6791cf
  عنوان اصلی: افزودن تست‌های خطای احراز هویت در auth.py
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["lint", "flake8", "pylint", "ruff"], "files_hint": ["backend/"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["mypy", "pyright", "type: ignore"], "files_hint": ["backend/"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
فایل backend/app/routers/auth.py فاقد تست برای سناریوهای خطای احراز هویت است

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
فایل backend/tests/test_auth.py وجود دارد اما تست‌های آن سناریوهای بحرانی مانند تلاش‌های مکرر لاگین (rate limiting)، توکن منقضی، و توکن نامعتبر را پوشش نمی‌دهد. با توجه به اینکه frontend/src/app/login/page.tsx محدودیت 5 تلاش لاگین را پیاده‌سازی کرده، backend نیز باید این محدودیت را اع

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
_(مجری بر اساس Context و معیارهای پذیرش، مراحل را تعیین کند)_

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 4 از 16
  id: ea641ffd-df5b-46e4-8d2f-9f1586208457
  عنوان اصلی: [منطق] پیاده‌سازی rate limiting لاگین
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["login attempts", "rate limit", "rate_limit", "brute force"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/tests/test_auth.py", "backend/app/auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["rate_limit", "RateLimiter", "throttle", "redis"], "files_hint": ["backend/app/auth.py", "backend/app/middleware.py", "backend/app/rate_limiter.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/test_auth.py::test_login_rate_limit", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی"}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] نبود rate limiting در login endpoint

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در frontend/src/app/login/page.tsx، شمارنده login attempts وجود دارد، اما این شمارنده فقط در سمت کلاینت است و قابل bypass توسط مهاجم است. backend (backend/tests/test_auth.py) هیچ محدودیتی برای تعداد تلاش‌های لاگین ندارد.

## 💥 پیامد (impact)
حملات brute-force به راحتی قابل انجام است. مهاجم می‌تواند هزاران درخواست لاگین در ثانیه ارسال کند تا رمز عبور را حدس بزند.

## 🛠 پیشنهاد رفع اولیه
در backend، یک rate limiter (مثلاً با redis یا in-memory) برای endpoint لاگین پیاده‌سازی کنید. بعد از 5 تلاش ناموفق، IP را برای 15 دقیقه مسدود کنید. شمارنده frontend را فقط برای UI feedback نگه دارید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی ناسازگاری منطقی بین شمارنده کلاینت و عدم محدودیت سرور — بررسی و مستندسازی ناسازگاری منطقی بین شمارنده کلاینت و عدم محدودیت سرور انجام نشده
  - پیاده‌سازی rate limiter سمت سرور برای endpoint لاگین با محدودیت ۵ تلاش ناموفق و مسدودیت ۱۵ دقیقه‌ای — rate limiter سمت سرور برای endpoint لاگین پیاده‌سازی نشده
  - اصلاح شمارنده frontend به UI feedback-only و حذف منطق محدودیت سمت کلاینت — شمارنده frontend به UI feedback-only تبدیل نشده
  - نوشتن تست‌های unit و integration برای rate limiter backend — تست‌های unit و integration برای rate limiter نوشته نشده
  - به‌روزرسانی مستندات و معیارهای پذیرش نهایی — مستندات و معیارهای پذیرش نهایی به‌روزرسانی نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 5 از 16
  id: ae87a6ca-2f66-469b-b263-79b1785240b3
  عنوان اصلی: پیاده‌سازی permission check در auth pipeline
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["permission", "authorization", "role", "access control"], "files_hint": ["backend/auth/pipeline.py", "backend/auth/README.md", "docs/auth.md"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "permission check", "authorization"], "files_hint": ["backend/auth/pipeline.py", "backend/auth/README.md"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why", "rationale"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md", "docs/decisions.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم وجود permission check در auth pipeline

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در مستندات ارائه شده، هیچ اشاره‌ای به مکانیزم permission یا authorization در pipeline احراز هویت نشده است. تمام مسیرهای mutation (مانند تغییر رمز عبور، ثبت‌نام، لاگین) بدون بررسی سطح دسترسی (role-based یا resource-based) اجرا می‌شوند. این یک شکاف امنیتی جدی است.

## 💥 پیامد (impact)
هر کاربر احراز هویت شده می‌تواند به عملیات‌های حساس مانند تغییر رمز عبور سایر کاربران یا دسترسی به منابع غیرمجاز دست یابد. این نقض اصل least privilege است.

## 🛠 پیشنهاد رفع اولیه
یک middleware یا decorator برای بررسی permission در endpoints اضافه کنید. مثلاً در backend/tests/test_auth.py و backend/app/database.py، قبل از هر mutation، سطح دسترسی کاربر را با token یا role چک کنید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی endpoint لاگین و اعمال permission در صورت نیاز
  - بررسی و رفع coherence issues در pipeline auth

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی permission در auth pipeline — مستندسازی کامل فرض‌های دو طرف ناسازگاری انجام نشده
  - طراحی مدل داده‌ای Role و Permission در database — مدل‌های Role و Permission در database ایجاد نشده
  - پیاده‌سازی decorator require_permission در backend — decorator require_permission پیاده‌سازی نشده
  - پیاده‌سازی تابع get_user_permissions از token — تابع get_user_permissions پیاده‌سازی نشده
  - اعمال decorator require_permission بر روی endpoint تغییر رمز عبور — decorator بر روی endpoint تغییر رمز اعمال نشده
  - اعمال decorator require_permission بر روی endpoint ثبت‌نام کاربر جدید — decorator بر روی endpoint ثبت‌نام اعمال نشده
  - اضافه کردن seed data برای roles و permissions در migration — seed data برای roles و permissions اضافه نشده
  - نوشتن unit tests برای decorator require_permission — unit tests برای decorator require_permission نوشته نشده
  - نوشتن integration tests برای permission در endpoints auth — integration tests برای permission در endpoints auth نوشته نشده
  - به‌روزرسانی مستندات API با permission requirements — مستندات API با permission requirements به‌روزرسانی نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 6 از 16
  id: 84bedb2d-3590-4311-ab28-4c105d6d8f4c
  عنوان اصلی: [منطق] پیاده‌سازی بررسی مالکیت برای به‌روزرسانی پروفایل و رمز
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/integration/test_auth_pipeline.py::test_profile_update_and_password_change_secure", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم بررسی ownership در profile update و password change

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در تست‌ها (test_auth.py) به endpoints 'profile update' و 'password change' اشاره شده، اما هیچ مکانیزمی برای اطمینان از اینکه کاربر فقط پروفایل خودش را به‌روزرسانی می‌کند (ownership check) دیده نمی‌شود.

## 💥 پیامد (impact)
یک کاربر می‌تواند با تغییر userId در درخواست، پروفایل یا رمز عبور کاربران دیگر را تغییر دهد (IDOR vulnerability).

## 🛠 پیشنهاد رفع اولیه
در endpointهای مربوطه، userId را از توکن احراز هویت استخراج کنید و با userId درخواست مقایسه کنید. اگر مطابقت نداشت، خطای 403 برگردانید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - شناسایی و مستندسازی فرض‌های ناسازگار در pipeline auth — بررسی کامل کدهای pipeline auth برای شناسایی فرض‌های ناسازگار در استخراج userId
  - تعیین ground truth و align کردن طرف دیگر (رفع IDOR vulnerability) — پیاده‌سازی ownership check با استخراج userId از JWT و بازگرداندن خطای 403
  - نوشتن integration test برای pipeline auth با پوشش ownership check — نوشتن integration test برای سناریوهای مجاز/غیرمجاز در به‌روزرسانی پروفایل و تغییر رمز

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 7 از 16
  id: 568f1abe-58ef-40bc-ba40-b9fa76d4ab1a
  عنوان اصلی: رفع عدم اعتبارسنجی ورودی در Pydantic models
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/schemas/__init__.py, backend/app/schemas/facility.py

📋 acceptance_criteria کامل:
  - ورودی‌های نامعتبر با خطای 422 رد شوند [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/facilities", "headers": null, "json_body": {"name": "", "phone": "invalid", "national_code": "123", "email": "not-an-email", "capacity": -1}, "expected_status": 422, "]
  - تمامی فیلدهای متنی محدودیت طول داشته باشند [verify_method=static] [verify_plan={"grep_patterns": ["max_length", "min_length", "String.*max_length"], "files_hint": ["backend/app/schemas/__init__.py", "backend/app/schemas/facility.py"]}]
  - الگوهای regex برای فیلدهای حساس اعمال شده باشد [verify_method=static] [verify_plan={"grep_patterns": ["regex", "pattern", "Field.*regex", "constr.*regex"], "files_hint": ["backend/app/schemas/__init__.py", "backend/app/schemas/facility.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم اعتبارسنجی ورودی در Pydantic models

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/schemas/__init__.py:10-30` — `CustomerCreate` — فیلدها بدون validation
  ```python
  class CustomerCreate(BaseModel):
      name: str
      phone: str
      national_id: str
      email: str
      address: str
  ```
- `backend/app/schemas/facility.py:5-20` — `FacilityCreate` — عدم محدودیت برای amount و type
  ```python
  class FacilityCreate(BaseModel):
      amount: float
      type: str
      description: str
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + Pydantic v2

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/customers.py` (سطر 15) — استفاده از schema بدون validation
- `backend/app/routers/facilities.py` (سطر 12) — استفاده از schema بدون validation

## 🌐 نقشهٔ وابستگی‌ها
تمام endpointهای POST/PUT از این schemaها استفاده می‌کنند. عدم validation باعث ورود داده‌های فاسد می‌شود.

## 🔍 Context و وضعیت فعلی
در backend/app/schemas/__init__.py و فایل‌های schemas مربوطه، بسیاری از فیلدها بدون اعتبارسنجی مناسب تعریف شده‌اند. مثلاً فیلدهای شماره تلفن، کد ملی، ایمیل و مقادیر عددی بدون validation pattern یا محدودیت طول هستند. این موضوع باعث می‌شود داده‌های نامعتبر وارد دیتابیس شوند و همچنین امکان حملات XSS از طریق فیلدهای متنی فراهم شود.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] ورودی‌های نامعتبر با خطای 422 رد شوند
- [ ] تمامی فیلدهای متنی محدودیت طول داشته باشند
- [ ] الگوهای regex برای فیلدهای حساس اعمال شده باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. به تمام فیلدهای متنی validatorهای مناسب اضافه کنید.
2. از Pydantic's Field با constraints استفاده کنید.
3. برای فیلدهای حساس (تلفن، کد ملی) از regex pattern استفاده کنید.
4. محدودیت طول برای تمام فیلدهای متنی اعمال کنید.
5. از html.escape یا Markup برای جلوگیری از XSS استفاده کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: بدون validation**

_قبل:_
```
phone: str
```

_بعد:_
```
phone: str = Field(..., pattern=r'^09\d{9}$', min_length=11, max_length=11)
```

**قبل: بدون محدودیت**

_قبل:_
```
amount: float
```

_بعد:_
```
amount: float = Field(..., gt=0, le=1_000_000_000)
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/customers" -H "Content-Type: application/json" -d '{"phone":"123"}'`
- `pytest tests/test_schemas.py -v`

## ⚠️ ریسک‌ها و موارد احتیاط
validationهای سختگیرانه ممکن است داده‌های معتبر قدیمی را رد کنند، نیاز به بررسی backward compatibility دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 8 از 16
  id: 258b7c7d-6e73-44a0-a1b7-8b7c59a77df2
  عنوان اصلی: پیاده‌سازی Rate Limiting و Brute Force Protection
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": null, "json_body": {"username": "test@example.com", "password": "wrong"}, "expected_status": 429, "required_fields": [], "json_contains": null}]
  - پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": null, "json_body": {"username": "test@example.com", "password": "wrong"}, "expected_status": 423, "required_fields": [], "json_contains": null}]
  - تمامی تلاش‌ها در Redis لاگ شوند [verify_method=static] [verify_plan={"grep_patterns": ["redis", "Redis", "r.set", "r.get", "r.expire", "r.incr"], "files_hint": ["backend/app/routers/auth.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم مدیریت Rate Limiting و Brute Force Protection

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:50-80` — `login` — بدون rate limiting و account lockout
  ```python
  @router.post("/auth/login")
  async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
      user = db.query(User).filter(User.email == credentials.email).first()
      if not user or not verify_password(credentials.password, user.hashed_password):
          raise HTTPException(status_code=401, detail="Invalid credentials")
      return {"access_token": create_access_token({"sub": user.id})}
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + Redis + slowapi

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر 15) — محل اضافه کردن تنظیمات rate limit
- `backend/app/database.py` (سطر 20) — برای ذخیره تلاش‌های ناموفق در Redis

## 🌐 نقشهٔ وابستگی‌ها
این ماژول امنیت احراز هویت را تأمین می‌کند. بدون rate limiting، کل سیستم در معرض brute force است.

## 🔍 Context و وضعیت فعلی
در backend/app/routers/auth.py هیچ محدودیت نرخی (rate limiting) برای endpointهای لاگین و ثبت‌نام وجود ندارد. این موضوع امکان حملات brute force برای حدس رمز عبور را فراهم می‌کند. همچنین هیچ مکانیزمی برای قفل کردن حساب پس از تلاش‌های ناموفق وجود ندارد. با توجه به ماهیت بانکی پروژه، این یک آسیب‌پذیری بحرانی است.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد
- [ ] پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود
- [ ] تمامی تلاش‌ها در Redis لاگ شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. از middleware rate limiting مانند slowapi یا fastapi-limiter استفاده کنید.
2. محدودیت 5 تلاش در دقیقه برای endpoint لاگین اعمال کنید.
3. پس از 10 تلاش ناموفق، حساب کاربر را به مدت 30 دقیقه قفل کنید.
4. لاگ تمام تلاش‌های ناموفق را در Redis ذخیره کنید.
5. اعلان ایمیلی برای تلاش‌های مشکوک ارسال کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: بدون محدودیت**

_قبل:_
```
@router.post("/auth/login")
async def login(...):
```

_بعد:_
```
@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `for i in {1..10}; do curl -X POST "http://localhost:8000/auth/login" -d '{"email":"test@test.com","password":"wrong"}'; done`
- `pytest tests/test_auth.py -v -k "test_rate_limiting"`

## ⚠️ ریسک‌ها و موارد احتیاط
rate limiting ممکن است کاربران واقعی را تحت تأثیر قرار دهد، نیاز به تنظیم دقیق محدودیت‌ها دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 9 از 16
  id: a4ea3f65-5f4e-47a2-b85d-e2740ed0bd38
  عنوان اصلی: رفع نشت اطلاعات حساس در لاگ‌ها و خطاها
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py, backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - در production، خطاهای 500 پیام generic نمایش دهند [verify_method=static] [verify_plan={"grep_patterns": ["def.*exception_handler.*500", "HTTPException.*500.*detail.*generic"], "files_hint": ["backend/app/main.py"]}]
  - لاگ‌ها حاوی password یا token نباشند [verify_method=static] [verify_plan={"grep_patterns": ["logging\\.(info|debug|error|warning)\\(.*password", "logging\\.(info|debug|error|warning)\\(.*token", "logger\\.(info|debug|error|warning)\\(.*password", "logger\\.(info|debug|erro]
  - exception handler تمام استثناها را catch کند [verify_method=static] [verify_plan={"grep_patterns": ["@app\\.exception_handler\\(Exception\\)", "def.*exception_handler.*Exception"], "files_hint": ["backend/app/main.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع نشت اطلاعات حساس در لاگ‌ها و خطاها

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:45-60` — `exception_handler` — نمایش مستقیم پیام خطا به کاربر
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      return JSONResponse(
          status_code=500,
          content={"detail": str(exc)}  # نشت اطلاعات خطا
      )
  ```
- `backend/app/routers/auth.py:70-75` — `login` — لاگ کردن exception بدون sanitization
  ```python
  except Exception as e:
      logger.error(f"Login failed: {e}")  # ممکن است حاوی password باشد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + structlog + Python logging

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر 20) — محل تنظیم سطح لاگ
- `backend/app/database.py` (سطر 15) — نیازمند لاگینگ امن

## 🌐 نقشهٔ وابستگی‌ها
تمامی endpointها از این exception handler استفاده می‌کنند. نشت اطلاعات می‌تواند به مهاجم کمک کند.

## 🔍 Context و وضعیت فعلی
در backend/app/main.py و backend/app/routers/*.py، استثناها و خطاها بدون sanitization به کاربر نمایش داده می‌شوند. همچنین لاگ‌ها حاوی اطلاعات حساس مانند رمز عبور و توکن‌ها هستند. این موضوع می‌تواند منجر به نشت اطلاعات محرمانه شود. در محیط production، خطاها باید generic باشند و جزئیات فنی در لاگ‌های داخلی ثبت شوند.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] در production، خطاهای 500 پیام generic نمایش دهند
- [ ] لاگ‌ها حاوی password یا token نباشند
- [ ] exception handler تمام استثناها را catch کند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد یک exception handler سفارشی که در production خطاهای generic برگرداند.
2. استفاده از structlog یا loguru برای لاگینگ امن.
3. فیلتر کردن فیلدهای حساس (password, token, secret) از لاگ‌ها.
4. تنظیم سطح لاگ به INFO در production و DEBUG در development.
5. اضافه کردن middleware برای catch all exceptions.

## 💡 نمونه‌های قبل/بعد
**قبل: نشت اطلاعات**

_قبل:_
```
content={"detail": str(exc)}
```

_بعد:_
```
content={"detail": "Internal server error"}  # در production
```

**قبل: لاگ بدون فیلتر**

_قبل:_
```
logger.error(f"Login failed: {e}")
```

_بعد:_
```
logger.error("Login failed", exc_info=True, extra={"user_id": user_id})
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/auth/login" -d '{"email":"test","password":"test"}' -v 2>&1 | grep -i "error\|exception"`
- `python -c "from backend.app.main import app; print('OK' if app.exception_handlers else 'NO HANDLER')"`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر در نحوه نمایش خطاها ممکن است debugging را برای توسعه‌دهندگان سخت‌تر کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 10 از 16
  id: 9bd29880-cb84-4bd4-bbe9-3e8afc316f09
  عنوان اصلی: Address conditional inconsistency anti-pattern
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/utils/security.py

📋 acceptance_criteria کامل:
  - ریشه anti-pattern تشخیص داده شد [verify_method=static] [verify_plan={"grep_patterns": ["if payload\\.get\\('iss'\\)", "if payload\\.get\\('aud'\\)"], "files_hint": ["backend/app/utils/security.py"]}]
  - یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["verify_access_token"], "files_hint": ["backend/app/utils/security.py"]}]
  - تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_security.py::test_verify_access_token_edge_cases", "timeout_seconds": 60}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
Anti-pattern: Conditional inconsistency

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/utils/security.py:130`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/config.py` — `security.py` این فایل را import می‌کند
- `backend/app/database.py` — `security.py` این فایل را import می‌کند
- `backend/app/models/user.py` — `security.py` این فایل را import می‌کند
- `backend/tests/conftest.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_auth.py` — این فایل `security.py` را import می‌کند (caller)
- `backend/tests/test_models.py` — این فایل `security.py` را import می‌کند (caller)

## 🔍 Context و وضعیت فعلی
در تابع verify_access_token، اعتبارسنجی issuer و audience فقط در صورت وجود (if payload.get('iss')) انجام می‌شود. این باعث می‌شود توکن‌های بدون این فیلدها (توکن‌های قدیمی) بدون بررسی issuer/audience قبول شوند، در حالی که توکن‌های جدید با این فیلدها بررسی می‌شوند. این ناهماهنگی می‌تواند امنیت را به خطر بیندازد.

📁 file: backend/app/utils/security.py (line 130)

🎯 پیشنهاد: این الگو معمولاً منطق سیستم را در شرایط لبه می‌شکند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] ریشه anti-pattern تشخیص داده شد
- [ ] یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- [ ] تست edge case نوشته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. بازنگری منطق در این نقطه و اضافه‌کردن guard/comment مناسب.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/utils/security.py`
- `ruff check backend/app/utils/security.py`
- `pytest -x`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug_fix
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 11 از 16
  id: 524a0f64-4f74-4967-a4f6-aceb7381c494
  عنوان اصلی: جلوگیری از نشت اطلاعات permission در frontend
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["AUTH_DISABLED", "permission", "role", "token"], "files_hint": ["frontend/src/lib/auth.tsx", "frontend/src/app/login/page.tsx"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align"], "files_hint": ["frontend/src/lib/auth.tsx", "frontend/src/app/login/page.tsx"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/pull_request_template.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] نشت اطلاعات permission در frontend

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در frontend/src/lib/auth.tsx، حالت AUTH_DISABLED برای توسعه وجود دارد. اگر این حالت فعال باشد، ممکن است permission info (مانند نقش کاربر یا توکن) به صورت ناخواسته در console یا network requests لو رود. همچنین در login page (frontend/src/app/login/page.tsx)، پیام‌های toast خطا ممکن است جزئیات فنی (مانند 'Invalid token' یا 'Permission denied') را فاش کنند.

## 💥 پیامد (impact)
مهاجم می‌تواند از طریق خطاهای verbose، ساختار permission system را شناسایی کرده و حملات targeted انجام دهد. در حالت AUTH_DISABLED، ممکن است کاربران بدون احراز هویت به منابع دسترسی پیدا کنند.

## 🛠 پیشنهاد رفع اولیه
در frontend/src/lib/auth.tsx، حالت AUTH_DISABLED را فقط در محیط development و با لاگ‌گیری محدود فعال کنید. در login page، پیام‌های خطا را generic نگه دارید (مثلاً 'Login failed' به جای 'Permission denied for role X').

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی AUTH_DISABLED در auth.tsx — بررسی و مستندسازی وضعیت AUTH_DISABLED در auth.tsx
  - بررسی و مستندسازی پیام‌های خطا در login page — بررسی و مستندسازی پیام‌های خطا در login page
  - بررسی و مستندسازی permission system backend — بررسی و مستندسازی permission system backend
  - محدود کردن AUTH_DISABLED به محیط development — محدود کردن AUTH_DISABLED به محیط development
  - حذف نشت permission info در console و network requests — حذف نشت permission info در console و network requests
  - Generic کردن پیام‌های خطا در login page — Generic کردن پیام‌های خطا در login page
  - اضافه کردن لاگ‌گیری امنیتی برای AUTH_DISABLED — اضافه کردن لاگ‌گیری امنیتی برای AUTH_DISABLED
  - نوشتن unit tests برای auth.tsx — نوشتن unit tests برای auth.tsx
  - نوشتن integration tests برای login flow — نوشتن integration tests برای login flow
  - مستندسازی تغییرات و به‌روزرسانی README — مستندسازی تغییرات و به‌روزرسانی README

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 12 از 16
  id: 1a8ebba4-e348-4398-87c9-784b145ae828
  عنوان اصلی: همگام‌سازی مدیریت session بک‌اند و فرانت‌اند
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["AsyncSession", "localStorage", "cookies"], "files_hint": ["backend/app/database.py", "frontend/src/lib/auth.tsx"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["session.*expire", "token.*revoke", "sync.*session"], "files_hint": ["backend/app/database.py", "frontend/src/lib/auth.tsx"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["coherence", "session", "decision"], "files_hint": ["PR_DESCRIPTION.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم coherence بین backend و frontend در مدیریت session

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

backend از AsyncSession برای دیتابیس استفاده می‌کند (backend/app/database.py)، اما frontend (frontend/src/lib/auth.tsx) session را به صورت دستی با localStorage یا cookies مدیریت می‌کند. هیچ مکانیزم sync برای انقضای session یا revoke token بین دو سمت وجود ندارد.

## 💥 پیامد (impact)
اگر session در backend منقضی شود (مثلاً timeout)، frontend همچنان کاربر را لاگین نشان می‌دهد تا زمانی که refresh page انجام شود. این باعث inconsistency و خطاهای 401 ناگهانی می‌شود.

## 🛠 پیشنهاد رفع اولیه
یک endpoint برای بررسی اعتبار token در backend اضافه کنید (مثلاً /auth/verify). frontend باید به صورت دوره‌ای (مثلاً هر 5 دقیقه) این endpoint را صدا بزند و در صورت invalid بودن token، کاربر را logout کند.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی وضعیت فعلی backend و frontend برای مدیریت session و token — مستندسازی کامل فرض‌های ناسازگار دو بخش (AsyncSession vs localStorage) انجام نشده.
  - ایجاد endpoint /auth/verify در backend برای بررسی اعتبار token — ایجاد endpoint /auth/verify در backend برای بررسی اعتبار token.
  - اضافه کردن تابع periodic token verification در frontend (auth.tsx) — اضافه کردن تابع periodic token verification در frontend (auth.tsx).
  - نوشتن تست‌های integration برای سناریوی end-to-end انقضای session — تست‌های integration برای سناریوی end-to-end انقضای session کامل نشده.
  - بررسی و مستندسازی coherence issue و اصلاحات انجام‌شده در کامیت message — نوشتن PR description جامع برای توضیح coherence issue.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 13 از 16
  id: 8366b1f5-8f1f-4476-b35d-5cca83ea025b
  عنوان اصلی: پیاده‌سازی اعتبارسنجی ورودی‌های لاگین
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["username", "password", "validation", "minLength", "maxLength", "sanitize", "escape"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/tests/test_auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "validation", "sanitize", "escape"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/app/auth.py", "backend/tests/test_auth.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/test_auth.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": ["pull_request_description.md"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم validation در frontend برای ورودی‌های login

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در frontend/src/app/login/page.tsx، ورودی‌های username و password بدون validation (مانند حداقل طول، نوع کاراکتر) به backend ارسال می‌شوند. backend نیز در مستندات test (backend/tests/test_auth.py) validation خاصی نشان نمی‌دهد.

## 💥 پیامد (impact)
حملات injection (مانند SQL injection یا XSS) از طریق فیلدهای لاگین امکان‌پذیر است. همچنین کاربران می‌توانند usernameهای خالی یا بسیار طولانی ارسال کنند که باعث crash یا رفتار غیرمنتظره شود.

## 🛠 پیشنهاد رفع اولیه
در frontend، validation سمت کلاینت (مثلاً username حداقل 3 کاراکتر، password حداقل 8 کاراکتر) اضافه کنید. در backend، validation سمت سرور با کتابخانه‌ای مانند pydantic یا marshmallow انجام دهید.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی وضعیت فعلی فایل‌های مرتبط با validation در frontend و backend — بررسی کامل فایل‌های مرتبط با validation در frontend و backend انجام نشده
  - اضافه کردن validation سمت کلاینت برای فیلد username در فرم لاگین — validation سمت کلاینت برای username اضافه نشده
  - اضافه کردن validation سمت کلاینت برای فیلد password در فرم لاگین — validation سمت کلاینت برای password اضافه نشده
  - اضافه کردن مدل Pydantic برای validation درخواست لاگین در backend — مدل Pydantic LoginRequest در backend ایجاد نشده
  - به‌روزرسانی endpoint لاگین در backend برای استفاده از مدل Pydantic — endpoint لاگین از مدل Pydantic استفاده نمی‌کند
  - نوشتن تست واحد برای مدل Pydantic LoginRequest — تست واحد برای مدل Pydantic LoginRequest نوشته نشده
  - نوشتن تست واحد برای validation سمت کلاینت (اختیاری اما توصیه شده) — تست واحد برای validation سمت کلاینت نوشته نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 14 از 16
  id: bc3f557f-9e02-4c09-9e3f-ff795c54fba5
  عنوان اصلی: پیکربندی HTTPS، HSTS و CORS
  اولویت اصلی: medium
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py

📋 acceptance_criteria کامل:
  - HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد [verify_method=static] [verify_plan={"grep_patterns": ["Strict-Transport-Security", "max-age=31536000"], "files_hint": ["backend/app/main.py"]}]
  - CORS فقط دامنه‌های مجاز را اجازه دهد [verify_method=static] [verify_plan={"grep_patterns": ["CORSMiddleware", "allow_origins"], "files_hint": ["backend/app/main.py"]}]
  - در production، HTTP به HTTPS redirect شود [verify_method=static] [verify_plan={"grep_patterns": ["redirect.*http", "RedirectMiddleware", "HTTP.*HTTPS"], "files_hint": ["backend/app/main.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم استفاده از HTTPS و HSTS headers

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:1-20` — `app` — فقدان کامل middlewareهای امنیتی
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  
  app = FastAPI(title="ALLIN1 API")
  
  # CORS middleware وجود ندارد
  # Security headers middleware وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + CORSMiddleware + TrustedHostMiddleware

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر 10) — محل اضافه کردن تنظیمات CORS و HTTPS
- `render.yaml` (سطر 5) — تنظیمات deployment برای HTTPS

## 🌐 نقشهٔ وابستگی‌ها
این middlewareها بر تمام درخواست‌های HTTP تأثیر می‌گذارند و امنیت ارتباط را تضمین می‌کنند.

## 🔍 Context و وضعیت فعلی
در backend/app/main.py هیچ middleware برای强制 HTTPS یا اضافه کردن HSTS headers وجود ندارد. همچنین CORS middleware پیکربندی نشده است. این موضوع باعث می‌شود ارتباط بین کلاینت و سرور رمزنگاری نشود و حملات man-in-the-middle ممکن باشد. برای یک سیستم بانکی، این یک نقص امنیتی جدی است.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد
- [ ] CORS فقط دامنه‌های مجاز را اجازه دهد
- [ ] در production، HTTP به HTTPS redirect شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. اضافه کردن middleware برای redirect HTTP به HTTPS.
2. اضافه کردن HSTS header با max-age=31536000.
3. پیکربندی CORS با لیست سفید دامنه‌های مجاز.
4. استفاده از SSL/TLS certificate در production.
5. اضافه کردن Security Headers (X-Content-Type-Options, X-Frame-Options, CSP).

## 💡 نمونه‌های قبل/بعد
**قبل: بدون middleware**

_قبل:_
```
app = FastAPI()
# هیچ middleware امنیتی اضافه نشده
```

_بعد:_
```
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -I http://localhost:8000/ | grep -i "strict-transport-security\|content-security-policy"`
- `curl -I https://yourdomain.com/ | grep -i "strict-transport-security"`

## ⚠️ ریسک‌ها و موارد احتیاط
تنظیمات نادرست CORS می‌تواند دسترسی frontend را قطع کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: medium
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 15 از 16
  id: 7182df34-8ad1-495b-8e65-f2f03773b735
  عنوان اصلی: افزودن قابلیت Refresh و Blacklist توکن
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد [verify_method=api_response] [verify_plan={"method": "POST", "path": "/auth/logout", "headers": {"Authorization": "Bearer <valid_token>"}, "json_body": null, "expected_status": 200, "required_fields": [], "json_contains": null}]
  - endpoint /auth/refresh وجود داشته باشد و کار کند [verify_method=api_response] [verify_plan={"method": "POST", "path": "/auth/refresh", "headers": {"Authorization": "Bearer <expired_token>"}, "json_body": null, "expected_status": 200, "required_fields": ["access_token"], "json_contains": nul]
  - توکن‌های revoked در middleware بررسی شوند [verify_method=static] [verify_plan={"grep_patterns": ["blacklist", "revoked", "check_blacklist"], "files_hint": ["backend/app/middleware.py", "backend/app/routers/auth.py"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف
رفع عدم مدیریت صحیح Session و Token Expiry

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:80-100` — `logout` — logout واقعی پیاده‌سازی نشده
  ```python
  @router.post("/auth/logout")
  async def logout(token: str = Depends(oauth2_scheme)):
      # هیچ عملی انجام نمی‌شود
      return {"message": "Logged out"}
  ```
- `backend/app/routers/auth.py:100-120` — `refresh_token` — فقدان refresh token
  ```python
  # endpoint refresh_token وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + JWT + Redis

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/database_manager.py` (سطر 30) — برای ذخیره توکن‌های revoked در Redis
- `backend/app/main.py` (سطر 25) — برای اضافه کردن blacklist check در middleware

## 🌐 نقشهٔ وابستگی‌ها
این ماژول مدیریت session کاربران را بر عهده دارد. عدم وجود logout واقعی امنیت را کاهش می‌دهد.

## 🔍 Context و وضعیت فعلی
در backend/app/routers/auth.py، توکن‌های JWT expiry دارند اما مکانیزم refresh token پیاده‌سازی نشده است. همچنین توکن‌های revoked در بلاک‌لیست ذخیره نمی‌شوند و logout واقعی وجود ندارد. کاربران نمی‌توانند session خود را ببندند و توکن‌ها تا زمان expiry معتبر می‌مانند. این موضوع امنیت session را کاهش می‌دهد.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد
- [ ] endpoint /auth/refresh وجود داشته باشد و کار کند
- [ ] توکن‌های revoked در middleware بررسی شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. پیاده‌سازی refresh token با عمر 7 روز.
2. ایجاد endpoint /auth/refresh.
3. ذخیره توکن‌های revoked در Redis با TTL.
4. پیاده‌سازی logout واقعی با invalidate کردن توکن.
5. اضافه کردن blacklist check در middleware احراز هویت.

## 💡 نمونه‌های قبل/بعد
**قبل: logout بدون عملیات**

_قبل:_
```
@router.post("/auth/logout")
async def logout(token: str):
    return {"message": "Logged out"}
```

_بعد:_
```
@router.post("/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    await redis.set(f"blacklist:{token}", "revoked", ex=3600)
    return {"message": "Logged out successfully"}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/auth/logout" -H "Authorization: Bearer <token>"`
- `curl -X POST "http://localhost:8000/auth/refresh" -d '{"refresh_token":"..."}'`

## ⚠️ ریسک‌ها و موارد احتیاط
اضافه کردن Redis dependency ممکن است پیچیدگی deployment را افزایش دهد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 16 از 16
  id: d5caf9d0-81a5-491a-99e4-bfeee0b2acda
  عنوان اصلی: مدیریت خطاهای دیتابیس در auth pipeline
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["retry", "fallback", "connection.*error", "timeout", "retry_decorator"], "files_hint": ["backend/app/database.py", "backend/app/auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground.truth", "align", "retry.*mechanism", "fallback.*implement"], "files_hint": ["backend/app/database.py", "backend/app/auth.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["why.*decision", "rationale", "reason.*chosen"], "files_hint": ["PR description"]}]

📝 idea_prompt اصلی (بدون تغییر و بدون خلاصه‌سازی):
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

---


## 🎯 هدف (خلاصه ساختاریافته)
[منطق] عدم مدیریت خطاهای دیتابیس در auth pipeline

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در pipeline auth است — همه فایل‌های این pipeline مرتبط هستند.

## 🔍 Context و وضعیت فعلی
## 📋 شرح ناسازگاری
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در backend/app/database.py، اتصال به دیتابیس با SSL و pool size مدیریت می‌شود، اما هیچ fallback یا retry mechanism برای خطاهای اتصال (مانند timeout یا connection reset) وجود ندارد. این می‌تواند باعث failure در عملیات‌های auth شود.

## 💥 پیامد (impact)
اگر دیتابیس به طور موقت در دسترس نباشد، کاربران نمی‌توانند لاگین یا ثبت‌نام کنند و خطای 500 دریافت می‌کنند. این downtime غیرضروری است.

## 🛠 پیشنهاد رفع اولیه
یک retry decorator برای session creation اضافه کنید (مثلاً 3 بار تلاش با exponential backoff). همچنین یک health check endpoint برای دیتابیس ایجاد کنید تا frontend بتواند وضعیت را به کاربر نشان دهد.

## 🤔 چرا مهم است
coherence issue یعنی دو بخش کد فرض‌های ناسازگار دارند — معمولاً نشانه‌ی refactor ناتمام یا feature flag rot است. این کلاس bug ها در test معمولی پیدا نمی‌شوند چون unit test ها در silo اجرا می‌شوند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
گام ۲: تصمیم بگیر کدام طرف ground truth است — معمولاً business logic مهم‌تر است.
گام ۳: طرف دیگر را با ground truth align کن.
گام ۴: integration test برای این pipeline بنویس تا regression جلوگیری شود.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run test`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: medium
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی اتصال دیتابیس در auth pipeline — بررسی و مستندسازی کامل وضعیت فعلی اتصال دیتابیس در auth pipeline
  - ایجاد retry decorator برای session creation با exponential backoff — ایجاد retry decorator برای session creation با exponential backoff
  - ایجاد health check endpoint برای دیتابیس در backend — ایجاد health check endpoint برای دیتابیس (GET /health/db)
  - اتصال health check endpoint به frontend برای نمایش وضعیت دیتابیس — اتصال health check endpoint به frontend برای نمایش وضعیت دیتابیس
  - نوشتن تست‌های واحد برای retry decorator — نوشتن تست‌های واحد برای retry decorator
  - نوشتن تست‌های integration برای health check endpoint — نوشتن تست‌های integration برای health check endpoint
  - نوشتن تست‌های end-to-end برای سناریوی قطع دیتابیس در auth — نوشتن تست‌های end-to-end برای سناریوی قطع دیتابیس در auth

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 56ab7fb9-d9b6-4cab-a0a3-98e3970018e9, 62de5589-02b3-4084-8051-a0047f6735a9, 42cbcd99-7b21-4491-816e-cad31d6791cf, ea641ffd-df5b-46e4-8d2f-9f1586208457, ae87a6ca-2f66-469b-b263-79b1785240b3, 84bedb2d-3590-4311-ab28-4c105d6d8f4c, 568f1abe-58ef-40bc-ba40-b9fa76d4ab1a, 258b7c7d-6e73-44a0-a1b7-8b7c59a77df2, a4ea3f65-5f4e-47a2-b85d-e2740ed0bd38, 9bd29880-cb84-4bd4-bbe9-3e8afc316f09, 524a0f64-4f74-4967-a4f6-aceb7381c494, 1a8ebba4-e348-4398-87c9-784b145ae828, 8366b1f5-8f1f-4476-b35d-5cca83ea025b, bc3f557f-9e02-4c09-9e3f-ff795c54fba5, 7182df34-8ad1-495b-8e65-f2f03773b735, d5caf9d0-81a5-491a-99e4-bfeee0b2acda`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. ورودی‌های نامعتبر با خطای 422 رد شوند _(verify: api_response)_
2. تمامی فیلدهای متنی محدودیت طول داشته باشند _(verify: static)_
3. الگوهای regex برای فیلدهای حساس اعمال شده باشد _(verify: static)_
4. پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد _(verify: api_response)_
5. پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود _(verify: api_response)_
6. تمامی تلاش‌ها در Redis لاگ شوند _(verify: static)_
7. توکن با الگوریتم none توسط middleware رد شود _(verify: api_response)_
8. کلید JWT از متغیر محیطی خوانده شود و در کد هاردکد نباشد _(verify: static)_
9. تمامی تست‌های احراز هویت با موفقیت پاس شوند _(verify: backend_test)_
10. در production، خطاهای 500 پیام generic نمایش دهند _(verify: static)_
11. لاگ‌ها حاوی password یا token نباشند _(verify: static)_
12. exception handler تمام استثناها را catch کند _(verify: static)_
13. بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند _(verify: api_response)_
14. تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود _(verify: static)_
15. HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد _(verify: static)_
16. CORS فقط دامنه‌های مجاز را اجازه دهد _(verify: static)_
17. در production، HTTP به HTTPS redirect شود _(verify: static)_
18. پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد _(verify: api_response)_
19. endpoint /auth/refresh وجود داشته باشد و کار کند _(verify: api_response)_
20. توکن‌های revoked در middleware بررسی شوند _(verify: static)_
21. اعمال تغییر بدون شکستن تست‌های موجود _(verify: backend_test)_
22. linter بدون warning عبور می‌کند _(verify: static)_
23. type-check موفق است _(verify: static)_
24. هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد _(verify: static)_
25. ground truth تعیین شد و طرف دیگر align شد _(verify: static)_
26. integration test برای pipeline `auth` بدون شکست عبور می‌کند _(verify: backend_test)_
27. PR description توضیح می‌دهد چرا این تصمیم گرفته شد _(verify: manual_only)_
28. ریشه anti-pattern تشخیص داده شد _(verify: static)_
29. یا کد اصلاح شد، یا کامنت توجیهی اضافه شد _(verify: static)_
30. تست edge case نوشته شد _(verify: backend_test)_

## Task Steps

### Step 1: یادداشت مهم برای مدل اجراکننده — بررسی مستقل پیش از تغییر
**Status:** `pending` (0%)
**Scope:** این بخش یک یادداشت هشداردهنده است که به مدل اجراکننده یادآوری می‌کند پرامپت ممکن است ناقص یا اشتباه باشد. وظیفه مدل اجراکننده این است که پیش از هر تغییر، ساختار repo، فایل‌های ذکرشده و وابستگی‌ها را مستقل بررسی کند. این بخش شامل هیچ مرحله اجرایی نیست و صرفاً یک راهنمای رفتاری است.
— [merged] این بخش یک یادداشت هشداردهنده است که به مدل اجراکننده یادآوری می‌کند پرامپت ممکن است ناقص یا اشتباه باشد. شامل دستورالعمل‌هایی برای بررسی مستقل repo، فایل‌ها و وابستگی‌ها، و مسئولیت‌پذیری در قبال تصمیم‌گیری. همچنین شامل قواعدی برای انجام کار طولانی در چند کامیت متوالی. این بخش هیچ تغییر اجرایی مشخصی را تعریف نمی‌کند و صرفاً یک راهنمای رفتاری است.
— [merged] این بخش یک یادداشت هشداردهنده است که به مدل اجراکننده یادآوری می‌کند پرامپت ممکن است ناقص یا اشتباه باشد. شامل دستورالعمل‌هایی برای بررسی مستقل ساختار repo، فایل‌ها و وابستگی‌ها، و مسئولیت‌پذیری در قبال تصمیمات. همچنین دستورالعمل‌هایی برای انجام کارهای طولانی در چند کامیت متوالی با ترتیب منطقی و ارائه checklist در PR description. این بخش هیچ تغییر اجرایی مشخصی را تعریف نمی‌کند.
— [merged] این بخش یک یادداشت هشداردهنده برای مدل اجراکننده است و شامل هیچ دستور اجرایی یا تغییر کد نیست. هدف آن یادآوری مسئولیت مدل برای بررسی مستقل ساختار repo، فایل‌ها و وابستگی‌ها پیش از هرگونه تغییر است. همچنین تأکید دارد که پرامپت ممکن است حاوی اشتباه باشد و مدل نباید صرفاً به آن استناد کند. این بخش هیچ مرحله اجرایی ندارد و صرفاً یک راهنمای رفتاری برای مدل است.
— [merged] این بخش یک یادداشت هشداردهنده است که به مدل اجراکننده یادآوری می‌کند که پرامپت ممکن است ناقص یا اشتباه باشد. وظیفه مدل اجراکننده این است که پیش از هر تغییری، ساختار repo، فایل‌های ذکرشده و وابستگی‌ها را مستقل بررسی کند. این بخش شامل هیچ دستور اجرایی مستقیم نیست، بلکه یک راهنمای رفتاری برای مدل است. هیچ مرحله اجرایی از این بخش استخراج نمی‌شود.
— [merged] این بخش یک یادداشت هشداردهنده است که به مدل اجراکننده یادآوری می‌کند پرامپت ممکن است ناقص یا اشتباه باشد. وظیفه مدل اجراکننده این است که پیش از هر تغییری، ساختار repo، فایل‌های ذکرشده و وابستگی‌ها را مستقل بررسی کند. این بخش شامل هیچ دستور اجرایی مستقیم نیست، بلکه یک راهنمای رفتاری برای مدل است. اگر معیارهای پذیرش مبهم بودند، مدل باید بهترین تفسیر را انتخاب کرده و در commit message توضیح دهد. همچنین اگر کار طولانی است، نباید خلاصه شود و باید در چندین کامیت متوالی با ترتیب منطقی انجام شود.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.
```

### Step 2: رفع آسیب‌پذیری بحرانی JWT با الگوریتم none و کلید ضعیف
**Status:** `pending` (0%)
**Scope:** این بخش شامل اصلاح دو فایل اصلی backend/app/routers/auth.py و backend/app/main.py است. در auth.py باید کلید ثابت و ضعیف با یک کلید امن از متغیر محیطی جایگزین شود و الگوریتم‌های مجاز محدود شوند. در main.py باید تابع verify_token با گزینه‌های امنیتی (options) برای جلوگیری از پذیرش الگوریتم none به‌روزرسانی شود. همچنین فایل‌های backend/.env.example و backend/app/config.py برای پشتیبانی از کلید امن جدید به‌روز می‌شوند. این بخش شامل تغییرات در سایر فایل‌ها یا تست‌ها نیست.
**Excerpt:**
```
رفع آسیب‌پذیری بحرانی JWT با الگوریتم none و کلید ضعیف

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:1-50` — `create_access_token` — کلید ثابت و ضعیف، عدم بررسی الگوریتم none
  ```python
  from jose import jwt
  SECRET_KEY = "your-secret-key"
  ALGORITHM = "HS256"
  def create_access_token(data: dict):
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(minutes=30)
      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
      return encoded_jwt
  ```
- `backend/app/main.py:20-40` — `verify_token` — عدم استفاده از options برای امنیت بیشتر
  ```python
  def verify_token(token: str = Depends(oauth2_scheme)):
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          return payload
      except JWTError:
          raise HTTPException(status_code=401)
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + python-jose + JWT + OAuth2

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/.env.example` (سطر 5) — شامل کلید پیش‌فرض ضعیف
- `backend/app/config.py` (سطر 10) — محل بارگذاری تنظیمات JWT

## 🌐 نقشهٔ وابستگی‌ها
سیستم احراز هویت کل پروژه به این ماژول وابسته است. تمام endpointهای محافظت‌شده از این middleware استفاده می‌کنند.

## 🔍 Context و وضعیت فعلی
در فایل backend/app/routers/auth.py از کتابخانه python-jose با الگوریتم HS256 و یک کلید ثابت و ضعیف ('your-secret-key' در .env.example) استفاده شده است. این پیکربندی امکان حملات signature bypass (CVE-2022-23529) و brute-force را فراهم می‌کند. همچنین middleware احراز هویت در backend/app/main.py بررسی نمی‌کند که آیا توکن با الگوریتم 'none' امضا شده است یا خیر. این آسیب‌پذیری به مهاجم اجازه می‌دهد توکن‌های جعلی با دسترسی ادمین تولید کند.
```

### Step 3: تقویت امنیت JWT: جایگزینی کلید هاردکد، محدودیت الگوریتم و به‌روزرسانی middleware
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی کامل معیارهای پذیرش امنیتی JWT است: خواندن کلید از متغیر محیطی، محدود کردن الگوریتم به HS256، فعال‌سازی بررسی امضا و فیلدهای اجباری (exp, iat)، جایگزینی کتابخانه python-jose با PyJWT/authlib، و به‌روزرسانی middleware برای رد توکن‌های با الگوریتم none. تمامی فایل‌های backend مرتبط (config, security, auth, middleware) تحت تأثیر قرار می‌گیرند. تست‌ها و linter باید پاس شوند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] توکن با الگوریتم none توسط middleware رد شود
- [ ] کلید JWT از متغیر محیطی خوانده شود و در کد هاردکد نباشد
- [ ] تمامی تست‌های احراز هویت با موفقیت پاس شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. کلید JWT را با یک کلید 256 بیتی تصادفی از متغیر محیطی JWT_SECRET_KEY جایگزین کنید.
2. در تنظیمات JWT، پارامتر 'options' را با {'verify_signature': True, 'require': ['exp', 'iat']} تنظیم کنید.
3. الگوریتم‌های مجاز را به ['HS256'] محدود کنید.
4. از کتابخانه 'authlib' یا 'PyJWT' به جای python-jose استفاده کنید که امن‌تر است.
5. middleware احراز هویت را برای رد توکن‌های با الگوریتم none به‌روزرسانی کنید.
```

### Step 4: تقویت امنیت کلید JWT و اعتبارسنجی توکن‌ها با استفاده از متغیر محیطی و options امن
**Status:** `pending` (0%)
**Scope:** این مرحله شامل دو تغییر امنیتی در کد backend است: (1) جایگزینی کلید ثابت JWT_SECRET_KEY با مقدار پویا از متغیر محیطی یا تولید تصادفی امن، (2) افزودن options اجباری به تابع jwt.decode برای فعال‌سازی verify_signature و الزام وجود فیلدهای exp و iat. این تغییرات در فایل‌های backend/app/config.py و backend/app/utils/security.py یا هر فایلی که حاوی SECRET_KEY و jwt.decode است اعمال می‌شود. خارج از scope: تغییر frontend، تست‌ها، یا سایر بخش‌های احراز هویت.
**Excerpt:**
```
**قبل: کلید ثابت در کد**
_قبل:_
```
SECRET_KEY = "your-secret-key"
```
_بعد:_
```
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
```

**قبل: decode بدون options**
_قبل:_
```
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```
_بعد:_
```
payload = jwt.decode(token, SECRET_KEY, options={"verify_signature": True, "require": ["exp", "iat"]}, algorithms=["HS256"])
```
```

### Step 5: اجرای دستورات اعتبارسنجی امنیت JWT و تست‌های مربوطه
**Status:** `pending` (0%)
**Scope:** این بخش شامل اجرای دو دستور مشخص است: (1) یک دستور پایتون برای تست آسیب‌پذیری کتابخانه `python-jose` در برابر حملات الگوریتم none، و (2) اجرای تست‌های pytest مربوط به امنیت JWT در فایل `tests/test_auth.py`. این یک مرحله اجرایی و اعتبارسنجی است، نه طراحی یا پیاده‌سازی. خروجی این دستورات باید بررسی شود تا از عدم وجود آسیب‌پذیری اطمینان حاصل گردد.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `python -c "from jose import jwt; token = jwt.encode({'sub':'admin'}, '', algorithm='none'); print('VULNERABLE' if jwt.decode(token, '', options={'verify_signature': False}) else 'FIXED')"`
- `pytest tests/test_auth.py -v -k "test_jwt_security"`
```

### Step 6: حذف AUTH_DISABLED و الزام احراز هویت برای endpoint /api/customers
**Status:** `pending` (0%)
**Scope:** این مرحله شامل حذف کامل متغیر AUTH_DISABLED از فایل backend/app/utils/security.py و اطمینان از عدم وجود یا نادیده گرفته شدن آن در settings است. همچنین باید endpoint /api/customers بدون توکن JWT معتبر خطای 401 برگرداند. سایر endpointها و تغییرات امنیتی دیگر در این مرحله پوشش داده نمی‌شوند.
**Excerpt:**
```
تسک 2 از 16
  id: 62de5589-02b3-4084-8051-a0047f6735a9
  عنوان اصلی: حذف AUTH_DISABLED و الزام احراز هویت
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/utils/security.py

📋 acceptance_criteria کامل:
  - بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند [verify_method=api_response] [verify_plan={"method": "GET", "path": "/api/customers", "headers": null, "json_body": null, "expected_status": 401, "required_fields": [], "json_contains": null}]
  - تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود [verify_method=static] [verify_plan={"grep_patterns": ["AUTH_DISABLED"], "files_hint": ["backend/app/utils/security.py"]}]
```

### Step 7: بررسی اولیه خودکار و هشدارهای پیش از اجرا برای بخش امنیت و احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش یک یادداشت مهم و هشداردهنده برای مدل اجراکننده است. شامل دستورالعمل‌هایی برای بررسی وجود پیاده‌سازی قبلی، مسئولیت مدل در قبال بررسی مستقل repo، و نحوه برخورد با معیارهای مبهم است. این بخش هیچ کار اجرایی مشخصی را تعریف نمی‌کند و صرفاً یک راهنمای رفتاری برای مدل است. خارج از scope: پیاده‌سازی هرگونه قابلیت امنیتی، تغییر کد، یا تعریف معماری.
— [merged] این بخش یک یادداشت مهم و هشداردهنده برای مدل اجراکننده است. شامل دستورالعمل‌هایی برای بررسی وجود پیاده‌سازی قبلی، عدم بازسازی موارد موجود، و مسئولیت مدل در قبال بررسی مستقل repo و تفسیر صحیح معیارهای پذیرش است. این بخش خود یک مرحله اجرایی نیست، بلکه یک راهنما برای نحوه اجرای سایر مراحل است.
— [merged] این بخش یک یادداشت مهم و دستورالعمل برای مدل اجراکننده است. شامل هشدار در مورد احتمال خطا در پرامپت، احتمال پیاده‌سازی قبلی، مسئولیت مدل برای بررسی مستقل repo، و دستورالعمل‌هایی برای اجرای کامل و عدم خلاصه‌سازی است. این بخش خود یک مرحله اجرایی نیست، بلکه یک مجموعه از قواعد و هشدارها برای اجرای صحیح مراحل بعدی است. خروجی این بخش باید یک مرحله 'بررسی و آماده‌سازی' باشد که مدل اجراکننده را ملزم به انجام یکسری بررسی‌های اولیه می‌کند.
— [merged] این بخش یک یادداشت هشداردهنده (⚠️) است که به مدل اجراکننده دستور می‌دهد پیش از هر تغییری، وجود پیاده‌سازی‌های قبلی را بررسی کند، از بازسازی موارد موجود خودداری کند، و در صورت ابهام بر اساس قضاوت خود عمل نماید. این بخش شامل هیچ دستور اجرایی مستقیم برای تغییر کد نیست، بلکه یک راهنمای متدولوژیک برای کل فرآیند است. خروجی این بخش باید یک مرحله اجرایی با محتوای 'بررسی و تحلیل' باشد، نه تغییر کد.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 8: حذف backdoor AUTH_DISABLED از توابع get_current_user و get_optional_current_user
**Status:** `pending` (0%)
**Scope:** این مرحله شامل حذف کامل بلاک شرطی `if settings.AUTH_DISABLED` از دو تابع در فایل `backend/app/utils/security.py` است. همچنین شامل حذف import مربوط به `settings` در صورت عدم استفاده دیگر، و حذف متغیر `AUTH_DISABLED` از فایل `backend/app/config.py` و فایل‌های محیطی (`docker-compose.prod.yml`, `render.yaml`) می‌شود. خارج از scope: تغییر منطق احراز هویت JWT، تغییر مدل User، یا تغییر endpointها.
**Excerpt:**
```
در فایل backend/app/utils/security.py، خط 204، اگر settings.AUTH_DISABLED برابر True باشد، تابع get_current_user بدون بررسی توکن، کاربر demo را برمی‌گرداند. این یعنی هر درخواستی بدون نیاز به توکن معتبر می‌تواند به endpointهای محافظت‌شده دسترسی پیدا کند. این یک backdoor عمدی است که در محیط production نباید وجود داشته باشد. همچنین در خط 254 همین فایل، تابع get_optional_current_user نیز همین رفتار را دارد.
```

### Step 9: حذف یا غیرفعال‌سازی شرطی متغیر AUTH_DISABLED و افزودن middleware مسدودکننده در production
**Status:** `pending` (0%)
**Scope:** این مرحله شامل حذف کامل متغیر AUTH_DISABLED از settings یا تنظیم پیش‌فرض آن به False، پاک‌سازی آن از docker-compose.prod.yml و render.yaml، و افزودن middleware در backend/app/main.py است که در محیط production در صورت True بودن AUTH_DISABLED از اجرا جلوگیری کرده و اخطار لاگ دهد. خارج از scope: تغییرات در frontend، تست‌های auth، یا هرگونه تغییر در منطق JWT.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] بدون توکن JWT معتبر، endpoint /api/customers خطای 401 برگرداند
- [ ] تنظیم AUTH_DISABLED در settings وجود نداشته باشد یا نادیده گرفته شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱. متغیر محیطی AUTH_DISABLED را از settings حذف کنید یا مقدار پیش‌فرض آن را False قرار دهید. ۲. در docker-compose.prod.yml و render.yaml این متغیر را حذف کنید. ۳. یک middleware اضافه کنید که در محیط production اگر AUTH_DISABLED=True بود، اخطار لاگ بدهد و از اجرا جلوگیری کند.
```

### Step 10: حذف شرط AUTH_DISABLED از کد احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش شامل حذف کامل بلاک شرطی `if settings.AUTH_DISABLED` از تمام فایل‌های backend است. خارج از scope: تغییر منطق احراز هویت اصلی، تغییر تنظیمات، یا تغییر frontend. نکته حیاتی: پس از حذف، هیچ مسیر بازگشتی برای حالت 'دمو' یا 'غیرفعال' وجود نخواهد داشت و احراز هویت همیشه فعال است.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**حذف شرط AUTH_DISABLED**

_قبل:_
```
if settings.AUTH_DISABLED:
    return demo_user
# ادامه کد
```

_بعد:_
```
# حذف کامل بلاک if settings.AUTH_DISABLED
# ادامه کد
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 11: افزودن تست‌های خطای احراز هویت در auth.py
**Status:** `pending` (0%)
**Scope:** این بخش شامل تسک 3 از 16 است که به افزودن تست‌های خطای احراز هویت در فایل auth.py مربوط می‌شود. acceptance_criteria شامل: عدم شکستن تست‌های موجود (تأیید با اجرای تست‌های tests/test_auth.py)، عبور linter بدون warning (بررسی با flake8/pylint/ruff در backend/)، و موفقیت type-check (بررسی با mypy/pyright در backend/). هیچ مرحله‌ای قبلاً انجام نشده و این تسک مستقل است. فایل‌های دخیل مشخص نیستند اما فایل‌های مرتبط شامل backend/app/routers/auth.py و tests/test_auth.py هستند.
**Excerpt:**
```
تسک 3 از 16
  id: 42cbcd99-7b21-4491-816e-cad31d6791cf
  عنوان اصلی: افزودن تست‌های خطای احراز هویت در auth.py
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["lint", "flake8", "pylint", "ruff"], "files_hint": ["backend/"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["mypy", "pyright", "type: ignore"], "files_hint": ["backend/"]}]
```

### Step 12: بررسی اولیه خودکار و جلوگیری از پیاده‌سازی مجدد قابلیت‌های موجود
**Status:** `pending` (0%)
**Scope:** این بخش یک یادداشت مهم برای مدل اجراکننده است و شامل هیچ وظیفه اجرایی مستقیمی نیست. هدف آن هشدار درباره احتمال وجود پیاده‌سازی قبلی، تشویق به بررسی مستقل repo، و تعیین مسئولیت مدل اجراکننده برای تصمیم‌گیری آگاهانه است. این بخش هیچ کد یا تغییری را مشخص نمی‌کند و صرفاً یک راهنمای رفتاری برای اجراکننده است. خروجی این بخش باید یک `skip` باشد زیرا هیچ مرحله اجرایی در آن وجود ندارد.
— [merged] این بخش یک یادداشت مهم برای مدل اجراکننده است و شامل دستورالعمل‌های پیش از اجرا می‌باشد. محتوای آن دستور می‌دهد که پیش از هرگونه تغییر، ساختار repo، فایل‌های ذکرشده و وابستگی‌ها به صورت مستقل بررسی شوند تا از پیاده‌سازی مجدد قابلیت‌های موجود جلوگیری شود. این بخش هیچ کد یا تغییری در repo ایجاد نمی‌کند، بلکه یک مرحله تحلیلی و بررسی است. scope این بخش شامل: بررسی وجود فایل‌ها، توابع، کلاس‌ها و قابلیت‌های مرتبط با امنیت و احراز هویت در مسیرهای مشخص شده است.
— [merged] این بخش یک یادداشت مهم برای مدل اجراکننده است و شامل هیچ وظیفه اجرایی مستقیمی نیست. هدف آن اطمینان از این است که قبل از هرگونه تغییر، وضعیت فعلی repo (فایل‌ها، کلاس‌ها، توابع) به‌طور مستقل بررسی شود تا از پیاده‌سازی مجدد یا ناقص جلوگیری شود. این بخش شامل: (1) بررسی وجود قبلی قابلیت‌ها با grep/search، (2) عدم بازسازی فایل/تابع موجود، (3) اصلاح موارد ناقص/اشتباه، (4) ثبت کامیت no-op در صورت کامل بودن. خارج از scope: اجرای مستقیم هیچ تغییر کدی نیست.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.
```

### Step 13: افزودن تست‌های سناریوهای خطای احراز هویت به tests/test_auth.py
**Status:** `pending` (0%)
**Scope:** این مرحله صرفاً به افزودن تست‌های واحد (unit tests) برای سناریوهای خطای احراز هویت در فایل tests/test_auth.py می‌پردازد. سناریوهای تحت پوشش شامل: تلاش‌های مکرر لاگین (rate limiting)، توکن منقضی، و توکن نامعتبر است. پیاده‌سازی واقعی rate limiting در backend (مثلاً در middleware یا endpoint لاگین) بخشی از این مرحله نیست و باید در مرحله‌ای جداگانه انجام شود. این مرحله فرض می‌کند که منطق rate limiting قبلاً در backend پیاده‌سازی شده و صرفاً تست آن اضافه می‌شود.
**Excerpt:**
```
فایل backend/app/routers/auth.py فاقد تست برای سناریوهای خطای احراز هویت است

فایل tests/test_auth.py وجود دارد اما تست‌های آن سناریوهای بحرانی مانند تلاش‌های مکرر لاگین (rate limiting)، توکن منقضی، و توکن نامعتبر را پوشش نمی‌دهد. با توجه به اینکه frontend/src/app/login/page.tsx محدودیت 5 تلاش لاگین را پیاده‌سازی کرده، backend نیز باید این محدودیت را اعمال کند.
```

### Step 14: تبدیل معیارهای پذیرش و مراحل اجرایی به یک مرحله اجرایی واحد
**Status:** `pending` (0%)
**Scope:** این بخش شامل تعریف معیارهای پذیرش (AC) و مراحل اجرایی پیشنهادی برای یک مرحله از پروژه تقویت امنیت و احراز هویت است. هدف، تبدیل این بخش به یک مرحله اجرایی واحد است که شامل اعمال تغییرات کد، عبور از تست‌ها، linter و type-check می‌شود. نکته حیاتی: این مرحله نباید تست‌های موجود را بشکند و باید رفتار قابل مشاهده را تضمین کند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
_(مجری بر اساس Context و معیارهای پذیرش، مراحل را تعیین کند)_

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 15: پیاده‌سازی rate limiting لاگین با شناسایی ناسازگاری‌ها و مستندسازی فرض‌ها
**Status:** `pending` (0%)
**Scope:** این مرحله شامل پیاده‌سازی کامل مکانیزم rate limiting برای endpoint لاگین است. شامل: شناسایی و مستندسازی ناسازگاری‌های بین frontend و backend در مورد محدودیت نرخ، تعیین ground truth و align کردن طرف دیگر، پیاده‌سازی RateLimiter با پشتیبانی Redis، افزودن middleware یا decorator برای throttle درخواست‌های لاگین، و نوشتن integration test برای pipeline احراز هویت. خارج از scope: سایر endpointها، rate limiting برای APIهای عمومی، یا پیاده‌سازی Captcha.
**Excerpt:**
```
📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["login attempts", "rate limit", "rate_limit", "brute force"], "files_hint": ["frontend/src/app/login/page.tsx", "tests/test_auth.py", "backend/app/routers/auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["rate_limit", "RateLimiter", "throttle", "redis"], "files_hint": ["backend/app/routers/auth.py", "backend/app/middleware.py", "backend/app/rate_limiter.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py::test_login_rate_limit", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی"}]
```

### Step 16: پیاده‌سازی Rate Limiting برای Endpoint لاگین در بک‌اند
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن مکانیزم rate limiting (مبتنی بر IP) به endpoint لاگین در بک‌اند FastAPI است. محدودیت: ۵ تلاش ناموفق در ۱۵ دقیقه. پیاده‌سازی می‌تواند با استفاده از Redis یا یک دیکشنری in-memory (برای سادگی) انجام شود. شمارنده سمت کلاینت (frontend) فقط برای نمایش UI باقی می‌ماند و تغییری نمی‌کند. فایل‌های تحت تأثیر: backend/app/routers/auth.py (اضافه کردن منطق rate limit)، backend/app/config.py (اضافه کردن تنظیمات rate limit)، backend/app/utils/security.py (اضافه کردن تابع یا کلاس rate limiter). تست‌ها در tests/test_auth.py باید به‌روزرسانی شوند تا رفتار rate limiting را پوشش دهند.
**Excerpt:**
```
در backend، یک rate limiter (مثلاً با redis یا in-memory) برای endpoint لاگین پیاده‌سازی کنید. بعد از 5 تلاش ناموفق، IP را برای 15 دقیقه مسدود کنید. شمارنده frontend را فقط برای UI feedback نگه دارید.

## 💥 پیامد (impact)
حملات brute-force به راحتی قابل انجام است. مهاجم می‌تواند هزاران درخواست لاگین در ثانیه ارسال کند تا رمز عبور را حدس بزند.

## 🛠 پیشنهاد رفع اولیه
در backend، یک rate limiter (مثلاً با redis یا in-memory) برای endpoint لاگین پیاده‌سازی کنید. بعد از 5 تلاش ناموفق، IP را برای 15 دقیقه مسدود کنید. شمارنده frontend را فقط برای UI feedback نگه دارید.
```

### Step 17: تعریف معیارهای پذیرش رفتار-محور برای رفع ناسازگاری در pipeline احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش معیارهای پذیرش (AC) را برای فرآیند شناسایی و رفع ناسازگاری بین دو طرف (مثلاً backend و frontend یا دو ماژول) در pipeline auth تعریف می‌کند. شامل مستندسازی فرض‌ها، تعیین ground truth، عبور integration test، توضیح PR، و عبور تست‌ها/linter/type-check است. خارج از scope: پیاده‌سازی خود ناسازگاری یا تغییر در منطق auth.
— [merged] این بخش معیارهای پذیرش (AC) را برای فرآیند شناسایی و رفع ناسازگاری بین دو طرف (مثلاً backend و frontend یا دو ماژول) در pipeline احراز هویت تعریف می‌کند. شامل مستندسازی فرض‌ها، تعیین ground truth، اجرای تست‌های یکپارچه‌سازی، و اطمینان از عبور تمام تست‌ها و linting است. خارج از scope: پیاده‌سازی کد جدید یا تغییر معماری.
— [merged] این بخش معیارهای پذیرش (AC) را برای فرآیند شناسایی و رفع ناسازگاری بین دو طرف (احتمالاً backend و frontend یا دو ماژول) در pipeline احراز هویت تعریف می‌کند. شامل مستندسازی فرضیات، تعیین ground truth، عبور integration test، توضیح PR، و عبور تست‌های واحد، linter و type-check است. خارج از scope: پیاده‌سازی کد، طراحی معماری، یا انتخاب کتابخانه خاص.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
```

### Step 18: پیاده‌سازی permission check در auth pipeline
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی مکانیزم بررسی مجوز (permission check) در پایپلاین احراز هویت است. شامل شناسایی و مستندسازی ناسازگاری‌های منطقی بین فرض‌های سمت کلاینت و سرور، تعیین ground truth، نوشتن integration test برای پایپلاین auth، و توضیح تصمیمات در PR description می‌شود. خارج از scope: پیاده‌سازی rate limiter، اصلاح شمارنده frontend، و تست‌های rate limiter.
**Excerpt:**
```
تسک 5 از 16
  id: ae87a6ca-2f66-469b-b263-79b1785240b3
  عنوان اصلی: پیاده‌سازی permission check در auth pipeline
  اولویت اصلی: critical
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["permission", "authorization", "role", "access control"], "files_hint": ["backend/auth/pipeline.py", "backend/auth/README.md", "docs/auth.md"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "permission check", "authorization"], "files_hint": ["backend/auth/pipeline.py", "backend/auth/README.md"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why", "rationale"], "files_hint": [".github/PULL_REQUEST_TEMPLATE.md", "docs/decisions.md"]}]
```

### Step 19: افزودن middleware بررسی permission به pipeline احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش به افزودن مکانیزم بررسی سطح دسترسی (permission check) در pipeline احراز هویت سیستم می‌پردازد. شامل تمام endpoints مربوط به mutation‌ها (تغییر رمز عبور، ثبت‌نام، لاگین) می‌شود. خارج از scope این بخش: پیاده‌سازی کامل role-based access control (RBAC) یا resource-based authorization. نکته حیاتی: این بخش صرفاً به شناسایی شکاف امنیتی و پیشنهاد رفع اولیه اشاره دارد و نیاز به پیاده‌سازی کامل middleware یا decorator دارد.
**Excerpt:**
```
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در مستندات ارائه شده، هیچ اشاره‌ای به مکانیزم permission یا authorization در pipeline احراز هویت نشده است. تمام مسیرهای mutation (مانند تغییر رمز عبور، ثبت‌نام، لاگین) بدون بررسی سطح دسترسی (role-based یا resource-based) اجرا می‌شوند. این یک شکاف امنیتی جدی است.

هر کاربر احراز هویت شده می‌تواند به عملیات‌های حساس مانند تغییر رمز عبور سایر کاربران یا دسترسی به منابع غیرمجاز دست یابد. این نقض اصل least privilege است.

یک middleware یا decorator برای بررسی permission در endpoints اضافه کنید. مثلاً در tests/test_auth.py و backend/app/database.py، قبل از هر mutation، سطح دسترسی کاربر را با token یا role چک کنید.
```

### Step 20: تعریف معیارهای پذیرش رفتار-محور برای یکپارچه‌سازی احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش معیارهای پذیرش (AC) را برای مرحله‌ای از پروژه تعریف می‌کند که هدف آن رفع ناسازگاری‌ها و هم‌ترازسازی فرض‌های دو طرف (احتمالاً backend و frontend) در pipeline احراز هویت است. شامل مستندسازی ناسازگاری‌ها، تعیین ground truth، عبور تست‌های یکپارچه‌سازی auth، توضیح PR، و عبور از تست‌ها، linter و type-check می‌شود. خارج از این scope: پیاده‌سازی منطق جدید احراز هویت یا تغییر APIها.
— [merged] این بخش معیارهای پذیرش (AC) را برای مرحله‌ای تعریف می‌کند که در آن ناسازگاری‌های بین دو طرف (احتمالاً backend و frontend یا دو ماژول) شناسایی و مستند می‌شود، ground truth تعیین می‌گردد، و یکپارچه‌سازی pipeline احراز هویت (auth) از طریق تست‌های یکپارچه‌سازی (integration test) تأیید می‌شود. همچنین شامل الزامات مربوط به عبور تست‌ها، linter و type-check است. خارج از این scope: پیاده‌سازی جزئیات فنی یا کدنویسی مستقیم.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
```

### Step 21: [منطق] پیاده‌سازی بررسی مالکیت برای به‌روزرسانی پروفایل و رمز
**Status:** `pending` (0%)
**Scope:** این بخش شامل شناسایی و مستندسازی ناسازگاری‌های دو طرف (احتمالاً frontend و backend یا دو سرویس) در فرآیند به‌روزرسانی پروفایل و رمز عبور است. هدف تعیین ground truth و align کردن طرف دیگر است. این تسک صرفاً به مستندسازی و تحلیل منطقی می‌پردازد و شامل پیاده‌سازی کد نمی‌شود. خروجی نهایی باید یک PR description باشد که تصمیمات اتخاذ شده را توضیح دهد.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: critical
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  - بررسی endpoint لاگین و اعمال permission در صورت نیاز
  - بررسی و رفع coherence issues در pipeline auth

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی و مستندسازی وضعیت فعلی permission در auth pipeline — مستندسازی کامل فرض‌های دو طرف ناسازگاری انجام نشده
  - طراحی مدل داده‌ای Role و Permission در database — مدل‌های Role و Permission در database ایجاد نشده
  - پیاده‌سازی decorator require_permission در backend — decorator require_permission پیاده‌سازی نشده
  - پیاده‌سازی تابع get_user_permissions از token — تابع get_user_permissions پیاده‌سازی نشده
  - اعمال decorator require_permission بر روی endpoint تغییر رمز عبور — decorator بر روی endpoint تغییر رمز اعمال نشده
  - اعمال decorator require_permission بر روی endpoint ثبت‌نام کاربر جدید — decorator بر روی endpoint ثبت‌نام اعمال نشده
  - اضافه کردن seed data برای roles و permissions در migration — seed data برای roles و permissions اضافه نشده
  - نوشتن unit tests برای decorator require_permission — unit tests برای decorator require_permission نوشته نشده
  - نوشتن integration tests برای permission در endpoints auth — integration tests برای permission در endpoints auth نوشته نشده
  - به‌روزرسانی مستندات API با permission requirements — مستندات API با permission requirements به‌روزرسانی نشده

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 6 از 16
  id: 84bedb2d-3590-4311-ab28-4c105d6d8f4c
  عنوان اصلی: [منطق] پیاده‌سازی بررسی مالکیت برای به‌روزرسانی پروفایل و رمز
  اولویت اصلی: critical
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py::test_profile_update_and_password_change_secure", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی", "grep_patterns": [], "files_hint": []}]
```

### Step 22: بررسی اولیه خودکار و تشخیص پیاده‌سازی‌های قبلی پیش از اجرا
**Status:** `pending` (0%)
**Scope:** این بخش یک یادداشت هشداردهنده برای مدل اجراکننده است و شامل هیچ دستور اجرایی مستقیمی نیست. وظیفه آن الزام مدل به بررسی مستقل مخزن، جستجوی پیاده‌سازی‌های موجود، و جلوگیری از بازسازی موارد از پیش موجود است. این بخش هیچ کد یا تغییری را مشخص نمی‌کند، بلکه فرآیند اجرا را شرطی می‌کند.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 23: اعمال بررسی مالکیت (ownership check) در endpointهای به‌روزرسانی پروفایل و تغییر رمز عبور
**Status:** `pending` (0%)
**Scope:** این مرحله شامل اصلاح endpointهای مربوط به 'profile update' و 'password change' در فایل backend/app/routers/auth.py است. userId باید از توکن JWT استخراج شده و با userId موجود در بدنه درخواست مقایسه شود. در صورت عدم تطابق، پاسخ 403 Forbidden برگردانده شود. تست‌های موجود در tests/test_auth.py باید به‌روزرسانی شوند تا این رفتار جدید را پوشش دهند. این مرحله شامل تغییرات در frontend یا سایر فایل‌های backend نمی‌شود.
**Excerpt:**
```
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در تست‌ها (test_auth.py) به endpoints 'profile update' و 'password change' اشاره شده، اما هیچ مکانیزمی برای اطمینان از اینکه کاربر فقط پروفایل خودش را به‌روزرسانی می‌کند (ownership check) دیده نمی‌شود.

یک کاربر می‌تواند با تغییر userId در درخواست، پروفایل یا رمز عبور کاربران دیگر را تغییر دهد (IDOR vulnerability).

در endpointهای مربوطه، userId را از توکن احراز هویت استخراج کنید و با userId درخواست مقایسه کنید. اگر مطابقت نداشت، خطای 403 برگردانید.
```

### Step 24: رفع عدم اعتبارسنجی ورودی در Pydantic models برای facility
**Status:** `pending` (0%)
**Scope:** این بخش شامل اعتبارسنجی ورودی‌های مربوط به مدل‌های Pydantic در فایل‌های backend/app/schemas/__init__.py و backend/app/schemas/facility.py است. هدف، افزودن محدودیت‌های طول (max_length/min_length) برای فیلدهای متنی، اعمال الگوهای regex برای فیلدهای حساس (مانند تلفن، کد ملی، ایمیل)، و اطمینان از بازگشت خطای 422 برای ورودی‌های نامعتبر (مانند نام خالی، تلفن نامعتبر، ظرفیت منفی) است. این بخش شامل تغییرات در منطق business یا endpointها نیست و صرفاً بر لایه اعتبارسنجی مدل تمرکز دارد.
**Excerpt:**
```
📋 acceptance_criteria کامل:
  - ورودی‌های نامعتبر با خطای 422 رد شوند [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/facilities", "headers": null, "json_body": {"name": "", "phone": "invalid", "national_code": "123", "email": "not-an-email", "capacity": -1}, "expected_status": 422, "]
  - تمامی فیلدهای متنی محدودیت طول داشته باشند [verify_method=static] [verify_plan={"grep_patterns": ["max_length", "min_length", "String.*max_length"], "files_hint": ["backend/app/schemas/__init__.py", "backend/app/schemas/facility.py"]}]
  - الگوهای regex برای فیلدهای حساس اعمال شده باشد [verify_method=static] [verify_plan={"grep_patterns": ["regex", "pattern", "Field.*regex", "constr.*regex"], "files_hint": ["backend/app/schemas/__init__.py", "backend/app/schemas/facility.py"]}]
```

### Step 25: افزودن اعتبارسنجی ورودی به Pydantic models برای CustomerCreate و FacilityCreate
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن validatorهای Pydantic v2 به مدل‌های CustomerCreate و FacilityCreate است. فیلدهای name، phone، national_id، email، address در CustomerCreate و فیلدهای amount، type، description در FacilityCreate باید با الگوهای regex، محدودیت طول و نوع داده مناسب اعتبارسنجی شوند. این مرحله شامل تغییر در فایل‌های backend/app/schemas/__init__.py و backend/app/schemas/facility.py است. تغییرات در routerها یا endpointها جزو این مرحله نیست.
**Excerpt:**
```
## 🎯 هدف
رفع عدم اعتبارسنجی ورودی در Pydantic models

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/schemas/__init__.py:10-30` — `CustomerCreate` — فیلدها بدون validation
  ```python
  class CustomerCreate(BaseModel):
      name: str
      phone: str
      national_id: str
      email: str
      address: str
  ```
- `backend/app/schemas/facility.py:5-20` — `FacilityCreate` — عدم محدودیت برای amount و type
  ```python
  class FacilityCreate(BaseModel):
      amount: float
      type: str
      description: str
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + Pydantic v2

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/customers.py` (سطر 15) — استفاده از schema بدون validation
- `backend/app/routers/facilities.py` (سطر 12) — استفاده از schema بدون validation

## 🌐 نقشهٔ وابستگی‌ها
تمام endpointهای POST/PUT از این schemaها استفاده می‌کنند. عدم validation باعث ورود داده‌های فاسد می‌شود.

## 🔍 Context و وضعیت فعلی
در backend/app/schemas/__init__.py و فایل‌های schemas مربوطه، بسیاری از فیلدها بدون اعتبارسنجی مناسب تعریف شده‌اند. مثلاً فیلدهای شماره تلفن، کد ملی، ایمیل و مقادیر عددی بدون validation pattern یا محدودیت طول هستند. این موضوع باعث می‌شود داده‌های نامعتبر وارد دیتابیس شوند و همچنین امکان حملات XSS از طریق فیلدهای متنی فراهم شود.
```

### Step 26: اعتبارسنجی ورودی‌ها و اعمال محدودیت‌های طول و الگوهای Regex برای فیلدهای حساس
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن validatorهای Pydantic به تمام فیلدهای متنی مدل‌های کاربر (User model) و ورودی‌های API (مانند لاگین و ثبت‌نام) است. محدودیت طول (min_length, max_length) برای همه فیلدهای متنی اعمال می‌شود. برای فیلدهای حساس مانند تلفن و کد ملی، الگوی regex دقیق تعریف می‌شود. همچنین برای جلوگیری از XSS، از html.escape یا Markup در خروجی‌های متنی استفاده می‌شود. فایل‌های تحت تأثیر: backend/app/models/user.py و backend/app/routers/auth.py. خارج از scope: تغییرات در frontend، تست‌های end-to-end، یا تغییرات در دیتابیس.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] ورودی‌های نامعتبر با خطای 422 رد شوند
- [ ] تمامی فیلدهای متنی محدودیت طول داشته باشند
- [ ] الگوهای regex برای فیلدهای حساس اعمال شده باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. به تمام فیلدهای متنی validatorهای مناسب اضافه کنید.
2. از Pydantic's Field با constraints استفاده کنید.
3. برای فیلدهای حساس (تلفن، کد ملی) از regex pattern استفاده کنید.
4. محدودیت طول برای تمام فیلدهای متنی اعمال کنید.
5. از html.escape یا Markup برای جلوگیری از XSS استفاده کنید.
```

### Step 27: افزودن اعتبارسنجی (Validation) به فیلدهای مدل‌های Pydantic
**Status:** `pending` (0%)
**Scope:** این بخش شامل افزودن اعتبارسنجی (مثل pattern، min_length، max_length، gt، le) به فیلدهای مدل‌های Pydantic در فایل‌های backend است. تمرکز بر روی فیلدهای `phone` و `amount` در نمونه‌های قبل/بعد است. خارج از scope: تغییرات در frontend، تست‌ها، یا منطق احراز هویت.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**قبل: بدون validation**

_قبل:_
```
phone: str
```

_بعد:_
```
phone: str = Field(..., pattern=r'^09\d{9}$', min_length=11, max_length=11)
```

**قبل: بدون محدودیت**

_قبل:_
```
amount: float
```

_بعد:_
```
amount: float = Field(..., gt=0, le=1_000_000_000)
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 28: پیاده‌سازی Rate Limiting و Brute Force Protection در مسیر لاگین
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی محدودیت نرخ (rate limiting) و محافظت در برابر حملات brute force در endpoint لاگین است. پس از 5 تلاش ناموفق در دقیقه، خطای 429 (Too Many Requests) و پس از 10 تلاش ناموفق، خطای 423 (Locked) به مدت 30 دقیقه برگردانده می‌شود. تمام تلاش‌ها در Redis لاگ می‌شوند. این بخش فقط فایل backend/app/routers/auth.py را درگیر می‌کند و نیاز به بررسی backward compatibility با داده‌های معتبر قدیمی دارد.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
validationهای سختگیرانه ممکن است داده‌های معتبر قدیمی را رد کنند، نیاز به بررسی backward compatibility دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: small

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 8 از 16
  id: 258b7c7d-6e73-44a0-a1b7-8b7c59a77df2
  عنوان اصلی: پیاده‌سازی Rate Limiting و Brute Force Protection
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": null, "json_body": {"username": "test@example.com", "password": "wrong"}, "expected_status": 429, "required_fields": [], "json_contains": null}]
  - پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود [verify_method=api_response] [verify_plan={"method": "POST", "path": "/api/auth/login", "headers": null, "json_body": {"username": "test@example.com", "password": "wrong"}, "expected_status": 423, "required_fields": [], "json_contains": null}]
  - تمامی تلاش‌ها در Redis لاگ شوند [verify_method=static] [verify_plan={"grep_patterns": ["redis", "Redis", "r.set", "r.get", "r.expire", "r.incr"], "files_hint": ["backend/app/routers/auth.py"]}]
```

### Step 29: پیاده‌سازی Rate Limiting و Brute Force Protection برای endpoint لاگین
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن محدودیت نرخ (rate limiting) با استفاده از slowapi و Redis برای endpoint `/auth/login` و پیاده‌سازی مکانیزم قفل حساب (account lockout) پس از تلاش‌های ناموفق است. محدوده شامل فایل‌های `backend/app/routers/auth.py`، `backend/app/config.py` و `backend/app/database.py` می‌شود. خارج از محدوده: endpoint ثبت‌نام، سایر endpointها، و frontend.
**Excerpt:**
```
در backend/app/routers/auth.py هیچ محدودیت نرخی (rate limiting) برای endpointهای لاگین و ثبت‌نام وجود ندارد. این موضوع امکان حملات brute force برای حدس رمز عبور را فراهم می‌کند. همچنین هیچ مکانیزمی برای قفل کردن حساب پس از تلاش‌های ناموفق وجود ندارد. با توجه به ماهیت بانکی پروژه، این یک آسیب‌پذیری بحرانی است.

موقعیت دقیق:
- `backend/app/routers/auth.py:50-80` — `login` — بدون rate limiting و account lockout
- `backend/app/config.py` (سطر 15) — محل اضافه کردن تنظیمات rate limit
- `backend/app/database.py` (سطر 20) — برای ذخیره تلاش‌های ناموفق در Redis
```

### Step 30: پیاده‌سازی محدودیت نرخ و قفل حساب با لاگ‌گیری Redis
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی کامل محدودیت نرخ (rate limiting) برای endpoint لاگین، قفل خودکار حساب پس از ۱۰ تلاش ناموفق، و لاگ‌گیری تمام تلاش‌ها در Redis است. فایل‌های backend/app/routers/auth.py و backend/app/config.py و backend/app/utils/security.py تحت تأثیر قرار می‌گیرند. تست‌های مربوطه در tests/test_auth.py باید به‌روزرسانی شوند. بخش اعلان ایمیلی (آیتم ۵) در این مرحله پیاده‌سازی نمی‌شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] پس از 5 تلاش ناموفق در دقیقه، خطای 429 برگردد
- [ ] پس از 10 تلاش ناموفق، حساب به مدت 30 دقیقه قفل شود
- [ ] تمامی تلاش‌ها در Redis لاگ شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. از middleware rate limiting مانند slowapi یا fastapi-limiter استفاده کنید.
2. محدودیت 5 تلاش در دقیقه برای endpoint لاگین اعمال کنید.
3. پس از 10 تلاش ناموفق، حساب کاربر را به مدت 30 دقیقه قفل کنید.
4. لاگ تمام تلاش‌های ناموفق را در Redis ذخیره کنید.
5. اعلان ایمیلی برای تلاش‌های مشکوک ارسال کنید.
```

### Step 31: افزودن محدودیت نرخ (Rate Limiting) به endpoint لاگین
**Status:** `pending` (0%)
**Scope:** این بخش شامل افزودن دکوراتور `@limiter.limit("5/minute")` به endpoint `POST /auth/login` در فایل `backend/app/routers/auth.py` است. خارج از scope: پیاده‌سازی خود `limiter`، تنظیمات آن در `config.py`، یا تغییرات در frontend. نکته حیاتی: فرض بر این است که شی `limiter` از قبل در ماژول `routers/auth.py` import شده و قابل استفاده است.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**قبل: بدون محدودیت**

_قبل:_
```
@router.post("/auth/login")
async def login(...):
```

_بعد:_
```
@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 32: اجرای دستورات اعتبارسنجی نرخ محدودیت (Rate Limiting) لاگین
**Status:** `pending` (0%)
**Scope:** این بخش شامل اجرای دو دستور مشخص است: (1) ارسال ۱۰ درخواست لاگین با رمز عبور اشتباه به endpoint `/auth/login` برای تست محدودیت نرخ، و (2) اجرای تست واحد `test_rate_limiting` در فایل `tests/test_auth.py`. این بخش صرفاً اجرای دستورات داده شده است و شامل پیاده‌سازی یا تغییر کد نمی‌شود. نکته حیاتی: فرض بر این است که سرویس در `localhost:8000` در حال اجراست و محیط تست (pytest) پیکربندی شده است.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `for i in {1..10}; do curl -X POST "http://localhost:8000/auth/login" -d '{"email":"test@test.com","password":"wrong"}'; done`
- `pytest tests/test_auth.py -v -k "test_rate_limiting"`
```

### Step 33: رفع نشت اطلاعات حساس در لاگ‌ها و خطاها
**Status:** `pending` (0%)
**Scope:** این مرحله شامل پیاده‌سازی exception handler سراسری برای بازگرداندن پیام‌های generic در خطاهای 500، حذف password و token از لاگ‌ها، و catch کردن تمام استثناها در backend/app/main.py است. فایل‌های backend/app/routers/auth.py نیز برای اطمینان از عدم لاگ‌کردن اطلاعات حساس بررسی می‌شوند. خارج از scope: rate limiting (که در بخش دیگری پوشش داده می‌شود) و تغییرات در frontend.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
rate limiting ممکن است کاربران واقعی را تحت تأثیر قرار دهد، نیاز به تنظیم دقیق محدودیت‌ها دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: high
- تخمین زمان: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 9 از 16
  id: a4ea3f65-5f4e-47a2-b85d-e2740ed0bd38
  عنوان اصلی: رفع نشت اطلاعات حساس در لاگ‌ها و خطاها
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py, backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - در production، خطاهای 500 پیام generic نمایش دهند [verify_method=static] [verify_plan={"grep_patterns": ["def.*exception_handler.*500", "HTTPException.*500.*detail.*generic"], "files_hint": ["backend/app/main.py"]}]
  - لاگ‌ها حاوی password یا token نباشند [verify_method=static] [verify_plan={"grep_patterns": ["logging\\.(info|debug|error|warning)\\(.*password", "logging\\.(info|debug|error|warning)\\(.*token", "logger\\.(info|debug|error|warning)\\(.*password", "logger\\.(info|debug|erro]
  - exception handler تمام استثناها را catch کند [verify_method=static] [verify_plan={"grep_patterns": ["@app\\.exception_handler\\(Exception\\)", "def.*exception_handler.*Exception"], "files_hint": ["backend/app/main.py"]}]
```

### Step 34: رفع نشت اطلاعات حساس در لاگ‌ها و خطاهای عمومی و لاگین
**Status:** `pending` (0%)
**Scope:** این بخش شامل دو تغییر مجزاست: (1) جایگزینی exception handler عمومی در backend/app/main.py برای نمایش پیام generic به کاربر به جای str(exc). (2) sanitize کردن لاگ خطا در endpoint لاگین (backend/app/routers/auth.py) تا password در logger.error ثبت نشود. خارج از scope: سایر endpointها، سایر لاگ‌ها، و تغییرات در config یا database. نکته حیاتی: در محیط production خطاها باید generic باشند و جزئیات فنی فقط در لاگ‌های داخلی ثبت شوند.
**Excerpt:**
```
## 🎯 هدف
رفع نشت اطلاعات حساس در لاگ‌ها و خطاها

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:45-60` — `exception_handler` — نمایش مستقیم پیام خطا به کاربر
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      return JSONResponse(
          status_code=500,
          content={"detail": str(exc)}  # نشت اطلاعات خطا
      )
  ```
- `backend/app/routers/auth.py:70-75` — `login` — لاگ کردن exception بدون sanitization
  ```python
  except Exception as e:
      logger.error(f"Login failed: {e}")  # ممکن است حاوی password باشد
  ```
```

### Step 35: پیاده‌سازی مدیریت خطاهای امن و لاگینگ امن در production
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی exception handler سفارشی برای برگرداندن پیام‌های generic در production، فیلتر کردن فیلدهای حساس (password, token, secret) از لاگ‌ها، تنظیم سطح لاگ بر اساس محیط، و اضافه کردن middleware برای catch all exceptions است. خارج از scope: تغییرات در routing، احراز هویت، یا تست‌های موجود. نکته حیاتی: باید از structlog یا loguru استفاده شود و لاگ‌ها در production سطح INFO داشته باشند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] در production، خطاهای 500 پیام generic نمایش دهند
- [ ] لاگ‌ها حاوی password یا token نباشند
- [ ] exception handler تمام استثناها را catch کند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد یک exception handler سفارشی که در production خطاهای generic برگرداند.
2. استفاده از structlog یا loguru برای لاگینگ امن.
3. فیلتر کردن فیلدهای حساس (password, token, secret) از لاگ‌ها.
4. تنظیم سطح لاگ به INFO در production و DEBUG در development.
5. اضافه کردن middleware برای catch all exceptions.
```

### Step 36: جلوگیری از نشت اطلاعات حساس در خطاها و لاگ‌ها
**Status:** `pending` (0%)
**Scope:** این مرحله شامل دو تغییر مجزاست: (1) جایگزینی پیام خطای دقیق با پیام عمومی در پاسخ‌های API برای جلوگیری از نشت اطلاعات داخلی، (2) اصلاح لاگ‌ها برای حذف جزئیات حساس (مانند پیام خطای کامل) و استفاده از exc_info و فیلدهای امن. خارج از scope: تغییرات در احراز هویت، مجوزدهی، یا سایر بخش‌های امنیتی. نکته حیاتی: تغییرات باید فقط در production اعمال شوند یا با flag محیطی کنترل شوند.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**قبل: نشت اطلاعات**

_قبل:_
```
content={"detail": str(exc)}
```

_بعد:_
```
content={"detail": "Internal server error"}  # در production
```

**قبل: لاگ بدون فیلتر**

_قبل:_
```
logger.error(f"Login failed: {e}")
```

_بعد:_
```
logger.error("Login failed", exc_info=True, extra={"user_id": user_id})
```
```

### Step 37: اجرای دستورات اعتبارسنجی لاگین و بررسی exception handlers
**Status:** `pending` (0%)
**Scope:** این بخش شامل دو دستور اعتبارسنجی است: (1) تست لاگین با curl با داده‌های نامعتبر و بررسی خطاها، (2) بررسی وجود exception handlers در اپلیکیشن FastAPI. این مرحله صرفاً اجرای این دو دستور و مشاهده خروجی است. هیچ تغییری در کد ایجاد نمی‌کند.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `curl -X POST "http://localhost:8000/auth/login" -d '{"email":"test","password":"test"}' -v 2>&1 | grep -i "error\|exception"`
- `python -c "from backend.app.main import app; print('OK' if app.exception_handlers else 'NO HANDLER')"`
```

### Step 38: رفع anti-pattern ناهماهنگی شرطی در تابع verify_access_token
**Status:** `pending` (0%)
**Scope:** این مرحله به بررسی و رفع anti-pattern ناهماهنگی شرطی (conditional inconsistency) در تابع verify_access_token در فایل backend/app/utils/security.py می‌پردازد. شامل تشخیص ریشه مشکل، اصلاح کد یا افزودن کامنت توجیهی، و نوشتن تست edge case است. هیچ فایل دیگری تحت تأثیر قرار نمی‌گیرد.
**Excerpt:**
```
تسک 10 از 16
  id: 9bd29880-cb84-4bd4-bbe9-3e8afc316f09
  عنوان اصلی: Address conditional inconsistency anti-pattern
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/utils/security.py

📋 acceptance_criteria کامل:
  - ریشه anti-pattern تشخیص داده شد [verify_method=static] [verify_plan={"grep_patterns": ["if payload\.get\('iss'\)", "if payload\.get\('aud'\)"], "files_hint": ["backend/app/utils/security.py"]}]
  - یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["verify_access_token"], "files_hint": ["backend/app/utils/security.py"]}]
  - تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_security.py::test_verify_access_token_edge_cases", "timeout_seconds": 60}]
```

### Step 39: رفع ناهماهنگی شرطی در اعتبارسنجی issuer و audience توکن دسترسی
**Status:** `pending` (0%)
**Scope:** این مرحله صرفاً به رفع anti-pattern 'Conditional inconsistency' در تابع verify_access_token در فایل backend/app/utils/security.py می‌پردازد. هدف، اجباری کردن اعتبارسنجی issuer و audience برای همه توکن‌ها (چه جدید و چه قدیمی) است. تغییرات فقط در خط 130 و منطق اطراف آن اعمال می‌شود. فایل‌های config.py، database.py، models/user.py، و تست‌ها تحت تأثیر قرار نمی‌گیرند مگر اینکه import یا فراخوانی تغییر کند.
**Excerpt:**
```
در تابع verify_access_token، اعتبارسنجی issuer و audience فقط در صورت وجود (if payload.get('iss')) انجام می‌شود. این باعث می‌شود توکن‌های بدون این فیلدها (توکن‌های قدیمی) بدون بررسی issuer/audience قبول شوند، در حالی که توکن‌های جدید با این فیلدها بررسی می‌شوند. این ناهماهنگی می‌تواند امنیت را به خطر بیندازد.

📁 file: backend/app/utils/security.py (line 130)

🎯 پیشنهاد: این الگو معمولاً منطق سیستم را در شرایط لبه می‌شکند.
```

### Step 40: تشخیص و رفع anti-pattern در احراز هویت با تست edge case و عبور از CI/CD
**Status:** `pending` (0%)
**Scope:** این مرحله شامل بازنگری منطق احراز هویت در backend/app/main.py و backend/app/routers/auth.py (و فایل‌های مرتبط) برای تشخیص anti-pattern رایج (مانند hardcoded secret, missing guard, insecure default) است. خروجی شامل اصلاح کد یا افزودن کامنت توجیهی، نوشتن تست edge case در tests/test_auth.py، و اطمینان از عبور تمام تست‌ها، linter و type-check است. خارج از scope: تغییرات در frontend یا config غیرمرتبط با امنیت.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] ریشه anti-pattern تشخیص داده شد
- [ ] یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- [ ] تست edge case نوشته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. بازنگری منطق در این نقطه و اضافه‌کردن guard/comment مناسب.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 41: جلوگیری از نشت اطلاعات permission در frontend
**Status:** `pending` (0%)
**Scope:** این مرحله شامل شناسایی و مستندسازی ناسازگاری‌های مربوط به نشت اطلاعات permission در frontend، تعیین ground truth و align کردن طرف دیگر، اجرای integration test برای pipeline auth، و توضیح تصمیمات در PR description است. فایل‌های دخیل شامل frontend/src/lib/auth.tsx و frontend/src/app/login/page.tsx هستند. نکته حیاتی: این مرحله نیازمند بررسی دقیق متغیرهای AUTH_DISABLED، permission، role و token در frontend است.
**Excerpt:**
```
تسک 11 از 16
  id: 524a0f64-4f74-4967-a4f6-aceb7381c494
  عنوان اصلی: جلوگیری از نشت اطلاعات permission در frontend
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["AUTH_DISABLED", "permission", "role", "token"], "files_hint": ["frontend/src/lib/auth.tsx", "frontend/src/app/login/page.tsx"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align"], "files_hint": ["frontend/src/lib/auth.tsx", "frontend/src/app/login/page.tsx"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": [".github/pull_request_template.md"]}]
```

### Step 42: بررسی اولیه خودکار repo و جلوگیری از پیاده‌سازی مجدد
**Status:** `pending` (0%)
**Scope:** این بخش یک یادداشت هشداردهنده برای مدل اجراکننده است و شامل هیچ دستور اجرایی مستقیمی نیست. وظیفه آن است که قبل از هرگونه تغییر، مدل را ملزم به بررسی مستقل repo، شناسایی پیاده‌سازی‌های موجود، و جلوگیری از بازنویسی یا ساخت دوباره کدهای از پیش موجود کند. این بخش هیچ مرحله اجرایی جدیدی تعریف نمی‌کند و صرفاً یک دستورالعمل روش‌شناسی است.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

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
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 43: رفع نشت اطلاعات permission در frontend با محدودسازی حالت AUTH_DISABLED و generic کردن پیام‌های خطا
**Status:** `pending` (0%)
**Scope:** این مرحله شامل اصلاح دو فایل frontend است: (1) frontend/src/lib/auth.tsx برای محدودسازی حالت AUTH_DISABLED به محیط development و لاگ‌گیری محدود، (2) frontend/src/app/login/page.tsx برای جایگزینی پیام‌های خطای فنی با پیام‌های generic. خارج از scope: تغییرات backend، تست‌های unit، یا هر فایل دیگر.
**Excerpt:**
```
در frontend/src/lib/auth.tsx، حالت AUTH_DISABLED برای توسعه وجود دارد. اگر این حالت فعال باشد، ممکن است permission info (مانند نقش کاربر یا توکن) به صورت ناخواسته در console یا network requests لو رود. همچنین در login page (frontend/src/app/login/page.tsx)، پیام‌های toast خطا ممکن است جزئیات فنی (مانند 'Invalid token' یا 'Permission denied') را فاش کنند. ... در frontend/src/lib/auth.tsx، حالت AUTH_DISABLED را فقط در محیط development و با لاگ‌گیری محدود فعال کنید. در login page، پیام‌های خطا را generic نگه دارید (مثلاً 'Login failed' به جای 'Permission denied for role X').
```

### Step 44: همگام‌سازی مدیریت session بک‌اند و فرانت‌اند
**Status:** `pending` (0%)
**Scope:** این بخش شامل شناسایی ناسازگاری‌های موجود در مدیریت session بین بک‌اند (AsyncSession) و فرانت‌اند (localStorage/cookies) است. هدف مستندسازی فرضیات هر دو طرف، تعیین ground truth و align کردن طرف دیگر است. همچنین شامل نوشتن integration test برای pipeline احراز هویت و مستندسازی تصمیمات در PR description می‌شود. موارد خارج از scope: تغییرات در AUTH_DISABLED، پیام‌های خطا، permission system و unit tests.
**Excerpt:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 12 از 16
  id: 1a8ebba4-e348-4398-87c9-784b145ae828
  عنوان اصلی: همگام‌سازی مدیریت session بک‌اند و فرانت‌اند
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["AsyncSession", "localStorage", "cookies"], "files_hint": ["backend/app/database.py", "frontend/src/lib/auth.tsx"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["session.*expire", "token.*revoke", "sync.*session"], "files_hint": ["backend/app/database.py", "frontend/src/lib/auth.tsx"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py::test_integration", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["coherence", "session", "decision"], "files_hint": ["PR_DESCRIPTION.md"]}]
```

### Step 45: افزودن endpoint بررسی اعتبار token و sync دوره‌ای session بین backend و frontend
**Status:** `pending` (0%)
**Scope:** این مرحله شامل ایجاد endpoint جدید /auth/verify در backend (احتمالاً در backend/app/routers/auth.py) و پیاده‌سازی فراخوانی دوره‌ای آن از frontend (frontend/src/lib/auth.tsx) است. خارج از scope: تغییر مکانیزم ذخیره‌سازی session در frontend، پیاده‌سازی revoke token، یا تغییر ساختار دیتابیس. نکته حیاتی: endpoint باید token جاری را از هدر Authorization یا cookie بخواند و بدون نیاز به دیتابیس (با استفاده از JWT decode) اعتبار آن را بررسی کند.
**Excerpt:**
```
یک endpoint برای بررسی اعتبار token در backend اضافه کنید (مثلاً /auth/verify). frontend باید به صورت دوره‌ای (مثلاً هر 5 دقیقه) این endpoint را صدا بزند و در صورت invalid بودن token، کاربر را logout کند.
```

### Step 46: اعتبارسنجی ورودی‌های لاگین (Login Input Validation)
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی اعتبارسنجی ورودی‌های لاگین (username و password) در هر دو سمت frontend و backend است. هدف اصلی شناسایی و مستندسازی ناسازگاری‌های فرضی بین دو سمت (مانند AsyncSession در backend و localStorage در frontend) و ایجاد یک ground truth مشترک است. همچنین شامل نوشتن تست‌های integration برای pipeline auth و مستندسازی تصمیمات در PR description می‌شود. موارد خارج از scope: تغییرات در session management یا token verification که در تسک‌های دیگر پوشش داده می‌شوند.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
تغییر یک طرف ممکن است downstream consumers را break کند. حتماً قبل از merge، همه caller های هر دو طرف را بررسی کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: logic_audit
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  - بررسی وضعیت فعلی backend و frontend برای مدیریت session و token — مستندسازی کامل فرض‌های ناسازگار دو بخش (AsyncSession vs localStorage) انجام نشده.
  - ایجاد endpoint /auth/verify در backend برای بررسی اعتبار token — ایجاد endpoint /auth/verify در backend برای بررسی اعتبار token.
  - اضافه کردن تابع periodic token verification در frontend (auth.tsx) — اضافه کردن تابع periodic token verification در frontend (auth.tsx).
  - نوشتن تست‌های integration برای سناریوی end-to-end انقضای session — تست‌های integration برای سناریوی end-to-end انقضای session کامل نشده.
  - بررسی و مستندسازی coherence issue و اصلاحات انجام‌شده در کامیت message — نوشتن PR description جامع برای توضیح coherence issue.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 13 از 16
  id: 8366b1f5-8f1f-4476-b35d-5cca83ea025b
  عنوان اصلی: پیاده‌سازی اعتبارسنجی ورودی‌های لاگین
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["username", "password", "validation", "minLength", "maxLength", "sanitize", "escape"], "files_hint": ["frontend/src/app/login/page.tsx", "tests/test_auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground truth", "align", "validation", "sanitize", "escape"], "files_hint": ["frontend/src/app/login/page.tsx", "backend/app/routers/auth.py", "tests/test_auth.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth.py", "timeout_seconds": 60}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["PR description", "decision", "why"], "files_hint": ["pull_request_description.md"]}]
```

### Step 47: افزودن اعتبارسنجی ورودی‌های لاگین در فرانت‌اند و بک‌اند
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن اعتبارسنجی سمت کلاینت در فایل frontend/src/app/login/page.tsx و اعتبارسنجی سمت سرور در فایل backend/app/routers/auth.py (یا backend/app/routers/auth.py) با استفاده از Pydantic است. خارج از scope این مرحله: پیاده‌سازی ضد SQL injection یا XSS به صورت جداگانه (فقط validation اولیه)، تغییرات در دیتابیس یا مدل‌ها، و تست‌های واحد جدید (فقط validation منطبق بر نیاز). نکته حیاتی: validation سمت کلاینت صرفاً برای UX است و امنیت اصلی باید در backend تضمین شود.
**Excerpt:**
```
در frontend/src/app/login/page.tsx، ورودی‌های username و password بدون validation (مانند حداقل طول، نوع کاراکتر) به backend ارسال می‌شوند. backend نیز در مستندات test (tests/test_auth.py) validation خاصی نشان نمی‌دهد.

## 💥 پیامد (impact)
حملات injection (مانند SQL injection یا XSS) از طریق فیلدهای لاگین امکان‌پذیر است. همچنین کاربران می‌توانند usernameهای خالی یا بسیار طولانی ارسال کنند که باعث crash یا رفتار غیرمنتظره شود.

## 🛠 پیشنهاد رفع اولیه
در frontend، validation سمت کلاینت (مثلاً username حداقل 3 کاراکتر، password حداقل 8 کاراکتر) اضافه کنید. در backend، validation سمت سرور با کتابخانه‌ای مانند pydantic یا marshmallow انجام دهید.
```

### Step 48: تکمیل معیارهای پذیرش رفتار-محور برای pipeline احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش شامل ۷ معیار پذیرش (AC) برای تضمین کیفیت و یکپارچگی pipeline احراز هویت است. محدوده شامل مستندسازی ناسازگاری‌ها، تعیین ground truth، عبور تست‌های یکپارچه‌سازی، توضیح PR، عبور تست‌ها، linter و type-check می‌باشد. خارج از محدوده: پیاده‌سازی منطق احراز هویت یا تغییر در کد اصلی.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
```

### Step 49: پیکربندی HTTPS، HSTS و CORS در backend/app/main.py
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیکربندی امنیتی در فایل backend/app/main.py است: افزودن هدر HSTS با max-age=31536000، تنظیم CORS برای محدود کردن دامنه‌های مجاز، و در محیط production فعال‌سازی ریدایرکت HTTP به HTTPS. سایر فایل‌ها یا بخش‌های دیگر پروژه در این مرحله تغییر نمی‌کنند.
**Excerpt:**
```
تسک 14 از 16
  id: bc3f557f-9e02-4c09-9e3f-ff795c54fba5
  عنوان اصلی: پیکربندی HTTPS، HSTS و CORS
  اولویت اصلی: medium
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/main.py

📋 acceptance_criteria کامل:
  - HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد [verify_method=static] [verify_plan={"grep_patterns": ["Strict-Transport-Security", "max-age=31536000"], "files_hint": ["backend/app/main.py"]}]
  - CORS فقط دامنه‌های مجاز را اجازه دهد [verify_method=static] [verify_plan={"grep_patterns": ["CORSMiddleware", "allow_origins"], "files_hint": ["backend/app/main.py"]}]
  - در production، HTTP به HTTPS redirect شود [verify_method=static] [verify_plan={"grep_patterns": ["redirect.*http", "RedirectMiddleware", "HTTP.*HTTPS"], "files_hint": ["backend/app/main.py"]}]
```

### Step 50: افزودن middlewareهای امنیتی HTTPS و HSTS به برنامه FastAPI
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن middlewareهای امنیتی برای اجبار HTTPS و تنظیم هدرهای HSTS در فایل backend/app/main.py است. همچنین پیکربندی CORS middleware و TrustedHostMiddleware را پوشش می‌دهد. خارج از این مرحله: تغییرات در config.py، تنظیمات deployment در render.yaml، و تست‌های مربوطه.
**Excerpt:**
```
## 🎯 هدف
رفع عدم استفاده از HTTPS و HSTS headers

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:1-20` — `app` — فقدان کامل middlewareهای امنیتی
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  
  app = FastAPI(title="ALLIN1 API")
  
  # CORS middleware وجود ندارد
  # Security headers middleware وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + CORSMiddleware + TrustedHostMiddleware

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/config.py` (سطر 10) — محل اضافه کردن تنظیمات CORS و HTTPS
- `render.yaml` (سطر 5) — تنظیمات deployment برای HTTPS

## 🌐 نقشهٔ وابستگی‌ها
این middlewareها بر تمام درخواست‌های HTTP تأثیر می‌گذارند و امنیت ارتباط را تضمین می‌کنند.

## 🔍 Context و وضعیت فعلی
در backend/app/main.py هیچ middleware برای强制 HTTPS یا اضافه کردن HSTS headers وجود ندارد. همچنین CORS middleware پیکربندی نشده است. این موضوع باعث می‌شود ارتباط بین کلاینت و سرور رمزنگاری نشود و حملات man-in-the-middle ممکن باشد. برای یک سیستم بانکی، این یک نقص امنیتی جدی است.
```

### Step 51: پیاده‌سازی معیارهای پذیرش امنیتی شامل HSTS، CORS، ریدایرکت HTTPS و هدرهای امنیتی
**Status:** `pending` (0%)
**Scope:** این بخش شامل پیاده‌سازی کامل معیارهای پذیرش امنیتی (HSTS، CORS، ریدایرکت HTTP به HTTPS در production، و هدرهای امنیتی اضافی) است. همچنین شامل اطمینان از عبور تست‌ها، linter و type-check می‌شود. خارج از scope: پیاده‌سازی احراز هویت، مجوزدهی، یا سایر بخش‌های امنیتی که در این بخش ذکر نشده‌اند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] HSTS header با max-age=31536000 در پاسخ‌ها وجود داشته باشد
- [ ] CORS فقط دامنه‌های مجاز را اجازه دهد
- [ ] در production، HTTP به HTTPS redirect شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. اضافه کردن middleware برای redirect HTTP به HTTPS.
2. اضافه کردن HSTS header با max-age=31536000.
3. پیکربندی CORS با لیست سفید دامنه‌های مجاز.
4. استفاده از SSL/TLS certificate در production.
5. اضافه کردن Security Headers (X-Content-Type-Options, X-Frame-Options, CSP).
```

### Step 52: افزودن middlewareهای امنیتی CORS و TrustedHost به برنامه FastAPI
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن دو middleware امنیتی (CORSMiddleware و TrustedHostMiddleware) به نمونه اصلی برنامه FastAPI در فایل main.py است. محدود به تغییرات در backend/app/main.py می‌باشد و شامل پیاده‌سازی منطق احراز هویت یا سایر middlewareها نمی‌شود. نکته حیاتی: مقادیر allow_origins و allowed_hosts باید با دامنه واقعی پروژه جایگزین شوند.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**قبل: بدون middleware**

_قبل:_
```
app = FastAPI()
# هیچ middleware امنیتی اضافه نشده
```

_بعد:_
```
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])
```
```

### Step 53: افزودن قابلیت Refresh و Blacklist توکن
**Status:** `pending` (0%)
**Scope:** این مرحله شامل پیاده‌سازی دو endpoint جدید در backend/app/routers/auth.py است: یکی برای logout که توکن را در blacklist قرار می‌دهد و دیگری برای refresh که با توکن منقضی شده یک access_token جدید صادر می‌کند. همچنین باید middleware بررسی blacklist را در backend/app/middleware.py پیاده‌سازی کند. خارج از scope این مرحله: تغییرات در frontend، مدل‌های دیتابیس، یا تنظیمات CORS.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
تنظیمات نادرست CORS می‌تواند دسترسی frontend را قطع کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: medium
- تخمین زمان: small

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 15 از 16
  id: 7182df34-8ad1-495b-8e65-f2f03773b735
  عنوان اصلی: افزودن قابلیت Refresh و Blacklist توکن
  اولویت اصلی: medium
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/routers/auth.py

📋 acceptance_criteria کامل:
  - پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد [verify_method=api_response] [verify_plan={"method": "POST", "path": "/auth/logout", "headers": {"Authorization": "Bearer <valid_token>"}, "json_body": null, "expected_status": 200, "required_fields": [], "json_contains": null}]
  - endpoint /auth/refresh وجود داشته باشد و کار کند [verify_method=api_response] [verify_plan={"method": "POST", "path": "/auth/refresh", "headers": {"Authorization": "Bearer <expired_token>"}, "json_body": null, "expected_status": 200, "required_fields": ["access_token"], "json_contains": nul]
  - توکن‌های revoked در middleware بررسی شوند [verify_method=static] [verify_plan={"grep_patterns": ["blacklist", "revoked", "check_blacklist"], "files_hint": ["backend/app/middleware.py", "backend/app/routers/auth.py"]}]
```

### Step 54: پیاده‌سازی logout واقعی و مکانیزم refresh token در auth.py
**Status:** `pending` (0%)
**Scope:** این مرحله شامل پیاده‌سازی دو قابلیت مجزاست: (1) تکمیل endpoint logout با ذخیره توکن revoked در Redis از طریق database_manager، (2) ایجاد endpoint جدید refresh_token که با استفاده از refresh token جدید (که باید در مدل JWT گنجانده شود) access token جدید صادر کند. خارج از scope این مرحله: تغییرات در middleware برای چک کردن blacklist (در main.py انجام می‌شود)، تست‌های واحد (در test_auth.py). نکته حیاتی: باید از کلاس AsyncSession و Redis از database_manager استفاده شود.
**Excerpt:**
```
## 🎯 هدف
رفع عدم مدیریت صحیح Session و Token Expiry

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/auth.py:80-100` — `logout` — logout واقعی پیاده‌سازی نشده
  ```python
  @router.post("/auth/logout")
  async def logout(token: str = Depends(oauth2_scheme)):
      # هیچ عملی انجام نمی‌شود
      return {"message": "Logged out"}
  ```
- `backend/app/routers/auth.py:100-120` — `refresh_token` — فقدان refresh token
  ```python
  # endpoint refresh_token وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + JWT + Redis

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/database_manager.py` (سطر 30) — برای ذخیره توکن‌های revoked در Redis
- `backend/app/main.py` (سطر 25) — برای اضافه کردن blacklist check در middleware

## 🌐 نقشهٔ وابستگی‌ها
این ماژول مدیریت session کاربران را بر عهده دارد. عدم وجود logout واقعی امنیت را کاهش می‌دهد.

## 🔍 Context و وضعیت فعلی
در backend/app/routers/auth.py، توکن‌های JWT expiry دارند اما مکانیزم refresh token پیاده‌سازی نشده است. همچنین توکن‌های revoked در بلاک‌لیست ذخیره نمی‌شوند و logout واقعی وجود ندارد. کاربران نمی‌توانند session خود را ببندند و توکن‌ها تا زمان expiry معتبر می‌مانند. این موضوع امنیت session را کاهش می‌دهد.
```

### Step 55: پیاده‌سازی مکانیزم Logout با Blacklist توکن و Refresh Token
**Status:** `pending` (0%)
**Scope:** این مرحله شامل پیاده‌سازی کامل logout واقعی با ذخیره توکن‌های revoked در Redis، ایجاد endpoint /auth/refresh با refresh token 7 روزه، و اضافه کردن blacklist check در middleware احراز هویت است. تست‌ها، linter و type-check باید پاس شوند. خارج از scope: تغییرات در frontend، مدل‌های دیتابیس، یا configهای غیرمرتبط.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] پس از logout، توکن در blacklist قرار گیرد و قابل استفاده نباشد
- [ ] endpoint /auth/refresh وجود داشته باشد و کار کند
- [ ] توکن‌های revoked در middleware بررسی شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. پیاده‌سازی refresh token با عمر 7 روز.
2. ایجاد endpoint /auth/refresh.
3. ذخیره توکن‌های revoked در Redis با TTL.
4. پیاده‌سازی logout واقعی با invalidate کردن توکن.
5. اضافه کردن blacklist check در middleware احراز هویت.
```

### Step 56: پیاده‌سازی مکانیزم بلاک‌لیست توکن در logout
**Status:** `pending` (0%)
**Scope:** این بخش صرفاً تغییر endpoint logout از حالت بدون عملیات به حالتی است که توکن را در Redis بلاک‌لیست می‌کند. شامل تغییر فایل backend/app/routers/auth.py و احتمالاً اضافه کردن وابستگی oauth2_scheme است. خارج از scope: پیاده‌سازی Redis connection pool، middleware بررسی بلاک‌لیست، یا تست‌های مربوطه.
**Excerpt:**
```
## 💡 نمونه‌های قبل/بعد
**قبل: logout بدون عملیات**

_قبل:_
```
@router.post("/auth/logout")
async def logout(token: str):
    return {"message": "Logged out"}
```

_بعد:_
```
@router.post("/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    await redis.set(f"blacklist:{token}", "revoked", ex=3600)
    return {"message": "Logged out successfully"}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 57: مدیریت خطاهای دیتابیس در auth pipeline
**Status:** `pending` (0%)
**Scope:** این بخش مربوط به پیاده‌سازی مکانیزم‌های مدیریت خطا (retry, fallback, timeout handling) در pipeline احراز هویت است. شامل مستندسازی ناسازگاری‌های دو طرف (احتمالاً backend و database)، تعیین ground truth، و پیاده‌سازی retry decorator در فایل‌های database.py و auth.py می‌شود. همچنین نیاز به integration test برای auth pipeline و توضیح PR دارد.
**Excerpt:**
```
📋 acceptance_criteria کامل:
  - هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد [verify_method=static] [verify_plan={"grep_patterns": ["retry", "fallback", "connection.*error", "timeout", "retry_decorator"], "files_hint": ["backend/app/database.py", "backend/app/routers/auth.py"]}]
  - ground truth تعیین شد و طرف دیگر align شد [verify_method=static] [verify_plan={"grep_patterns": ["ground.truth", "align", "retry.*mechanism", "fallback.*implement"], "files_hint": ["backend/app/database.py", "backend/app/routers/auth.py"]}]
  - integration test برای pipeline `auth` بدون شکست عبور می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_auth_pipeline.py", "timeout_seconds": 120}]
  - PR description توضیح می‌دهد چرا این تصمیم گرفته شد [verify_method=static] [verify_plan={"grep_patterns": ["why.*decision", "rationale", "reason.*chosen"], "files_hint": ["PR description"]}]
```

### Step 58: بررسی اولیه خودکار و پیش‌نیازهای اجرایی برای تقویت امنیت و احراز هویت
**Status:** `pending` (0%)
**Scope:** این بخش یک یادداشت هشداردهنده و راهنمای اجرایی است که قبل از هرگونه تغییر در repo باید مطالعه شود. شامل دستورالعمل‌های بررسی وجود پیاده‌سازی قبلی، مسئولیت مدل اجراکننده برای تحقیق مستقل، و قواعد مربوط به کامیت‌های طولانی است. این بخش خود یک مرحله اجرایی نیست، بلکه پیش‌نیاز و چارچوب اجرای سایر بخش‌ها را تعیین می‌کند. هیچ فایل یا کلاسی مستقیماً در این بخش برای تغییر معرفی نشده است.
**Excerpt:**
```
## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به آن استناد نکن.

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در commit message توضیح بده.

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همهٔ کامیت‌ها در PR description بنویس.
```

### Step 59: افزودن مکانیزم Retry و Fallback برای خطاهای اتصال دیتابیس در Pipeline Auth
**Status:** `pending` (0%)
**Scope:** این مرحله شامل افزودن یک decorator retry با exponential backoff برای session creation در backend/app/database.py و ایجاد یک health check endpoint برای دیتابیس است. خارج از scope این مرحله: تغییر در frontend، تغییر در مدل‌های کاربر، یا تغییر در منطق احراز هویت (auth logic). نکته حیاتی: این مرحله صرفاً به مدیریت خطاهای اتصال دیتابیس می‌پردازد و نه به بهبود عملکرد یا تغییر ساختار دیتابیس.
**Excerpt:**
```
در pipeline `auth` یک ناسازگاری منطقی پیدا شد:

در backend/app/database.py، اتصال به دیتابیس با SSL و pool size مدیریت می‌شود، اما هیچ fallback یا retry mechanism برای خطاهای اتصال (مانند timeout یا connection reset) وجود ندارد. این می‌تواند باعث failure در عملیات‌های auth شود.

...

یک retry decorator برای session creation اضافه کنید (مثلاً 3 بار تلاش با exponential backoff). همچنین یک health check endpoint برای دیتابیس ایجاد کنید تا frontend بتواند وضعیت را به کاربر نشان دهد.
```

### Step 60: تعیین معیارهای پذیرش رفتار-محور برای هم‌راستاسازی ناسازگاری‌ها و عبور تست‌های pipeline auth
**Status:** `pending` (0%)
**Scope:** این بخش شامل تعریف ۷ معیار پذیرش (AC) برای اطمینان از هم‌راستاسازی دو طرف ناسازگار (احتمالاً backend/frontend یا دو ماژول)، تعیین ground truth، عبور integration test برای pipeline auth، مستندسازی تصمیمات در PR description، و عبور از تست‌ها، linter و type-check است. خارج از scope: پیاده‌سازی کد جدید یا تغییر معماری.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] هر دو طرف ناسازگاری شناسایی + فرض‌هایشان مستند شد
- [ ] ground truth تعیین شد و طرف دیگر align شد
- [ ] integration test برای pipeline `auth` بدون شکست عبور می‌کند
- [ ] PR description توضیح می‌دهد چرا این تصمیم گرفته شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: هر دو طرف ناسازگاری را بخوان و فرض‌هایشان را لیست کن.
```

### Step 61: بررسی و مستندسازی وضعیت فعلی اتصال دیتابیس در auth pipeline
**Status:** `pending` (0%)
**Scope:** این مرحله شامل بررسی کامل و مستندسازی وضعیت فعلی اتصال دیتابیس در auth pipeline است. شامل: تحلیل کد موجود در backend/app/database.py و backend/app/routers/auth.py برای شناسایی نحوه ایجاد session، مدیریت خطاها، و نقاط ضعف. خروجی این مرحله یک سند فنی (در قالب کامنت یا فایل markdown) است که وضعیت فعلی را شرح می‌دهد. این مرحله شامل پیاده‌سازی هیچ تغییری نیست و صرفاً مستندسازی است.
**Excerpt:**
```
بررسی و مستندسازی وضعیت فعلی اتصال دیتابیس در auth pipeline — بررسی و مستندسازی کامل وضعیت فعلی اتصال دیتابیس در auth pipeline
```
