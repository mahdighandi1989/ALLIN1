---
task_id: task_97e9c7c534d9
title: افزایش پوشش تست و کیفیت کد بک‌اند
type: other
priority: high
execution_priority: 2200
status: pending
external_status: claimed
verification_status: partial
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-29T22:11:03.258958+00:00'
updated_at: '2026-06-05T01:01:16.047262+00:00'
tags:
- consolidated
- post_verify_merge
---

# افزایش پوشش تست و کیفیت کد بک‌اند

## Raw Idea

🧬 این یک تسک تلفیقی است — از 5 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی بهبود کلی زیرساخت بک‌اند، شامل پیاده‌سازی تست‌های واحد و یکپارچگی، همگام‌سازی وابستگی‌های پایتون، یکپارچه‌سازی فیلدهای پیش‌فرض، رفع الگوهای ضد-طراحی (anti-pattern) و پاکسازی کدهای بلااستفاده یا قدیمی تمرکز دارند. این موارد به پایداری و قابلیت نگهداری کد کمک می‌کنند.
🎯 theme: نگهداری و بهبود زیرساخت بک‌اند
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 5
  id: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9
  عنوان اصلی: پیاده‌سازی تست‌های واحد و یکپارچگی بک‌اند
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/pyproject.toml, backend/tests/

📋 acceptance_criteria کامل:
  - حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/", "timeout_seconds": 120}]
  - پوشش کد (coverage) حداقل 80% باشد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی"}]
  - تست‌ها در CI/CD به صورت خودکار اجرا شوند [verify_method=static] [verify_plan={"grep_patterns": ["pytest", "run:", "script:"], "files_hint": [".github/workflows/*.yml", ".gitlab-ci.yml", "Jenkinsfile"]}]

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
رفع عدم وجود تست‌های امنیتی و یکپارچگی

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/pyproject.toml:30-35` — `dev-dependencies` — وابستگی pytest وجود دارد اما هیچ تستی نوشته نشده
  ```
  [project.optional-dependencies]
  dev = [
      "pytest>=7.4.0",
      "pytest-asyncio>=0.21.0",
  ]
  ```
- `backend/tests/:1-1` — `directory` — فقدان کامل تست‌ها
  ```
  دایرکتوری tests وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
pytest + pytest-asyncio + httpx + GitHub Actions

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/auth.py` (سطر 1) — نیازمند تست‌های امنیتی
- `backend/app/routers/customers.py` (سطر 1) — نیازمند تست‌های یکپارچگی

## 🌐 نقشهٔ وابستگی‌ها
فقدان تست‌ها باعث می‌شود هر تغییر در کد potential regression ایجاد کند. این موضوع reliability پروژه را کاهش می‌دهد.

## 🔍 Context و وضعیت فعلی
پروژه فاقد تست‌های امنیتی و یکپارچگی است. در فایل pyproject.toml وابستگی pytest وجود دارد اما هیچ فایل تستی در backend/tests/ یا frontend/tests/ وجود ندارد. این موضوع باعث می‌شود رگرشن‌ها و آسیب‌پذیری‌های جدید شناسایی نشوند. با توجه به حساسیت سیستم بانکی، این یک نقص بحرانی است.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد
- [ ] پوشش کد (coverage) حداقل 80% باشد
- [ ] تست‌ها در CI/CD به صورت خودکار اجرا شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد ساختار tests/ در backend با پوشش:
   - تست‌های واحد برای models و schemas
   - تست‌های یکپارچگی برای API endpoints
   - تست‌های امنیتی برای SQL Injection, XSS, JWT
2. ایجاد tests/ در frontend با Jest و React Testing Library
3. اضافه کردن GitHub Actions برای اجرای خودکار تست‌ها
4. تنظیم coverage حداقل 80%

## 💡 نمونه‌های قبل/بعد
**قبل: بدون تست**

_قبل:_
```
# هیچ فایل تستی وجود ندارد
```

_بعد:_
```
backend/tests/
├── conftest.py
├── test_auth.py
├── test_customers.py
├── test_facilities.py
└── test_security.py
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing`
- `npm test --prefix frontend`

## ⚠️ ریسک‌ها و موارد احتیاط
نوشتن تست‌ها زمان‌بر است و ممکن است توسعه قابلیت‌های جدید را کند کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: high
- تخمین زمان: large

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 5
  id: 00478042-4983-4f7b-96c1-16c06a2fbf25
  عنوان اصلی: همگام‌سازی وابستگی‌های Python بین pyproject.toml و requirements.txt
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/requirements.txt, pyproject.toml

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["lint", "ruff", "flake8", "pylint"], "files_hint": ["pyproject.toml", "Makefile", "tox.ini"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["mypy", "type: ignore", "pyright"], "files_hint": ["pyproject.toml", "Makefile", "tox.ini"]}]

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
عدم تطابق نسخه‌های وابستگی‌های Python بین pyproject.toml و requirements.txt

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/requirements.txt:1-14` — `dependencies` — فقدان redis, celery, httpx, python-dotenv
  ```
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  sqlalchemy==2.0.23
  alembic==1.13.1
  asyncpg==0.29.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  email-validator==2.1.0
  python-multipart==0.0.6
  python-jose[cryptography]==3.3.0
  PyJWT==2.8.0
  passlib[bcrypt]==1.7.4
  python-dateutil==2.8.2
  psycopg2-binary==2.9.9
  ```
- `pyproject.toml:20-30` — `dependencies` — شامل redis, celery, httpx, python-dotenv, pytest
  ```
  dependencies = [
      "fastapi>=0.100.0",
      "uvicorn[standard]>=0.22.0",
      "sqlalchemy>=2.0.0",
      "alembic>=1.11.0",
      "psycopg2-binary>=2.9.0",
      "pydantic>=2.0.0",
      "python-multipart>=0.0.6",
      "python-jose[cryptography]>=3.3.0",
      "passlib[bcrypt]>=1.7.4",
      "python-dotenv>=1.0.0",
      "redis>=4.5.0",
      "celery>=5.3.0",
      "httpx>=0.24.0",
      "pytest>=7.4.0",
      "pytest-asyncio>=0.21.0",
  ]
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Python project management with pyproject.toml and requirements.txt

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/Dockerfile` (سطر 1) — احتمالاً از requirements.txt برای نصب وابستگی‌ها استفاده می‌کند
- `docker-compose.yml` (سطر 1) — ممکن است سرویس‌های Redis یا Celery را تعریف کرده باشد

## 🌐 نقشهٔ وابستگی‌ها
این ناهماهنگی بین دو فایل مدیریت وابستگی باعث می‌شود که محیط‌های مختلف (توسعه، تست، تولید) وابستگی‌های متفاوتی داشته باشند.

## 🔍 Context و وضعیت فعلی
فایل pyproject.toml وابستگی‌هایی مانند redis>=4.5.0, celery>=5.3.0, httpx>=0.24.0 را مشخص کرده است، اما این وابستگی‌ها در فایل requirements.txt وجود ندارند. همچنین، فایل pyproject.toml به python-dotenv>=1.0.0 اشاره دارد، در حالی که requirements.txt از pydantic-settings==2.1.0 استفاده می‌کند که خود می‌تواند dotenv را مدیریت کند. این ناهماهنگی باعث می‌شود که محیط‌های توسعه و تولید وابستگی‌های متفاوتی داشته باشند و ممکن است برخی ویژگی‌ها (مانند کش Redis یا وظایف پس‌زمینه Celery) در محیط‌های خاص در دسترس نباشند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. فایل requirements.txt را با pyproject.toml هماهنگ کنید. یا تمام وابستگی‌های pyproject.toml را به requirements.txt اضافه کنید، یا از pyproject.toml به عنوان منبع اصلی وابستگی‌ها استفاده کرده و فایل requirements.txt را با دستوری مانند 'pip freeze > requirements.txt' از یک محیط مجازی تمیز تولید کنید.

## 💡 نمونه‌های قبل/بعد
**نمونه 1**

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
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 5
  id: c621424e-f75d-4196-8e29-b28c04aab88b
  عنوان اصلی: یکپارچه‌سازی default فیلد 'user_id'
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - `user_id` در همه‌جا از یک منبع default می‌گیرد [verify_method=static] [verify_plan={"grep_patterns": ["user_id.*default.*None", "user_id.*default.*payload.get", "user_id.*default.*lambda"], "files_hint": ["backend/app/models.py", "backend/app/schemas.py"]}]
  - تست fixture رفتار پیش‌فرض را تأیید می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_defaults.py::test_user_id_default", "timeout_seconds": 30}]
  - اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["migration.*user_id", "backward_compat.*user_id", "compat_layer.*user_id"], "files_hint": ["backend/migrations/", "backend/app/compat.py"]}]

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
تضاد default برای فیلد 'user_id'

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 📋 شرح
فیلد `user_id` در `` در دو یا چند جای مختلف default value متفاوت دارد.

## 🤔 چرا مهم است
defaults متناقض باعث می‌شود رفتار سیستم به ترتیب اجرا/import وابسته شود — bug های غیرقابل reproduce.

## 🔍 جزئیات
- علت: field user_id has different defaults: ['None) -> str:', 'payload.get("user_id")']

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] `user_id` در همه‌جا از یک منبع default می‌گیرد
- [ ] تست fixture رفتار پیش‌فرض را تأیید می‌کند
- [ ] اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: همه جاهایی که `user_id` default می‌گیرد لیست کن.
گام ۲: یک default واحد انتخاب کن و یک منبع (مثل config یا constant).
گام ۳: تست fixture برای رفتار پیش‌فرض بنویس.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر default value برای کاربران فعلی silent behavior change است — حتماً release note بنویس.

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
تسک 4 از 5
  id: 5fa1a292-c7d8-4ef3-95ad-4725e8c3bb8a
  عنوان اصلی: Resolve stale assumption anti-pattern
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/database.py

📋 acceptance_criteria کامل:
  - ریشه anti-pattern تشخیص داده شد [verify_method=static] [verify_plan={"grep_patterns": ["localhost", "127.0.0.1", "ssl", "verify", "certificate"], "files_hint": ["backend/app/database.py"]}]
  - یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["ssl", "verify", "certificate", "hostname"], "files_hint": ["backend/app/database.py"]}]
  - تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_database.py::test_ssl_edge_cases", "timeout_seconds": 60}]

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
Anti-pattern: Stale assumption

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/database.py:10`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/utils/security.py` — این فایل `database.py` را import می‌کند (caller)
- `backend/app/models/customer.py` — این فایل `database.py` را import می‌کند (caller)
- `backend/app/models/facility.py` — این فایل `database.py` را import می‌کند (caller)
- `backend/app/models/offer_letter.py` — این فایل `database.py` را import می‌کند (caller)

## 🔍 Context و وضعیت فعلی
SSL configuration assumes that if the database URL does not contain 'localhost' or '127.0.0.1', it is a remote database requiring SSL with disabled hostname verification and certificate validation. This is a fragile assumption: (1) Some local setups may use hostnames like 'db' in Docker, which would incorrectly trigger SSL; (2) Remote databases may require proper SSL verification; (3) The conditio

📁 file: backend/app/database.py (line 10)

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
- `python -m py_compile backend/app/database.py`
- `ruff check backend/app/database.py`
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
تسک 5 از 5
  id: cb7140d5-f580-4bc5-85e9-db51766cd905
  عنوان اصلی: تعیین وضعیت و حذف/مستندسازی offer_letter.py
  اولویت اصلی: low
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/models/offer_letter.py

📋 acceptance_criteria کامل:
  - مشخص شد فایل dead است یا entry point/dynamic [verify_method=static] [verify_plan={"grep_patterns": ["from.*offer_letter.*import", "import.*offer_letter", "offer_letter"], "files_hint": ["backend/app/models/offer_letter.py"]}]
  - اقدام مناسب: حذف یا مستندسازی [verify_method=static] [verify_plan={"grep_patterns": ["offer_letter"], "files_hint": ["backend/app/models/offer_letter.py"]}]
  - تست‌های مربوطه (در صورت حذف) هم حذف شدند [verify_method=static] [verify_plan={"grep_patterns": ["test.*offer_letter", "offer_letter.*test"], "files_hint": ["tests/"]}]

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
فایل بدون import مرجع: offer_letter.py

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/models/offer_letter.py`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/database.py` — `offer_letter.py` این فایل را import می‌کند

## 🌐 نقشهٔ وابستگی‌ها
این مورد در پایپ‌لاین کدبیس به فایل‌های اطراف وابسته است؛ قبل از تغییر، grep روی نام symbol/path اصلی انجام شود.

## 🔍 Context و وضعیت فعلی
## 📋 شرح
فایل `backend/app/models/offer_letter.py` در هیچ import/require دیده نمی‌شود.

## 🤔 چرا مهم است
فایل orphan یا (الف) از قبل dead code است، یا (ب) entry point است (مثل migrations، scripts، CLI) که از طریق import import نمی‌شود، یا (ج) dynamic import می‌شود (lazy load).

## 🔍 جزئیات
- علت: reverse_import=0 and not entry-point

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] مشخص شد فایل dead است یا entry point/dynamic
- [ ] اقدام مناسب: حذف یا مستندسازی
- [ ] تست‌های مربوطه (در صورت حذف) هم حذف شدند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: grep روی نام فایل (بدون پسوند) و class/function اصلی آن.
گام ۲: اگر CLI/script است، در README ذکر کن.
گام ۳: اگر dead است، حذف کن (همراه با تست‌های مربوطه).

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/models/offer_letter.py`
- `ruff check backend/app/models/offer_letter.py`
- `pytest -x`

## ⚠️ ریسک‌ها و موارد احتیاط
فایل ممکن است در deployment pipeline یا CI به‌صورت direct invocation مصرف شود (مثل `python migrations/run.py`). قبل از حذف، در CI configs و scripts/ هم چک کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: cleanup
- اولویت: low
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9, 00478042-4983-4f7b-96c1-16c06a2fbf25, c621424e-f75d-4196-8e29-b28c04aab88b, 5fa1a292-c7d8-4ef3-95ad-4725e8c3bb8a, cb7140d5-f580-4bc5-85e9-db51766cd905`
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

🧬 این یک تسک تلفیقی است — از 5 تسک منفرد ساخته شده.
📌 دلیل تلفیق (rationale توسط AI): این تسک‌ها بر روی بهبود کلی زیرساخت بک‌اند، شامل پیاده‌سازی تست‌های واحد و یکپارچگی، همگام‌سازی وابستگی‌های پایتون، یکپارچه‌سازی فیلدهای پیش‌فرض، رفع الگوهای ضد-طراحی (anti-pattern) و پاکسازی کدهای بلااستفاده یا قدیمی تمرکز دارند. این موارد به پایداری و قابلیت نگهداری کد کمک می‌کنند.
🎯 theme: نگهداری و بهبود زیرساخت بک‌اند
💎 estimated_difficulty: medium

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 1 از 5
  id: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9
  عنوان اصلی: پیاده‌سازی تست‌های واحد و یکپارچگی بک‌اند
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/pyproject.toml, backend/tests/

📋 acceptance_criteria کامل:
  - حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد [verify_method=backend_test] [verify_plan={"test_node": "backend/tests/", "timeout_seconds": 120}]
  - پوشش کد (coverage) حداقل 80% باشد [verify_method=manual_only] [verify_plan={"reason": "نیاز به بازبینی دستی"}]
  - تست‌ها در CI/CD به صورت خودکار اجرا شوند [verify_method=static] [verify_plan={"grep_patterns": ["pytest", "run:", "script:"], "files_hint": [".github/workflows/*.yml", ".gitlab-ci.yml", "Jenkinsfile"]}]

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
رفع عدم وجود تست‌های امنیتی و یکپارچگی

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/pyproject.toml:30-35` — `dev-dependencies` — وابستگی pytest وجود دارد اما هیچ تستی نوشته نشده
  ```
  [project.optional-dependencies]
  dev = [
      "pytest>=7.4.0",
      "pytest-asyncio>=0.21.0",
  ]
  ```
- `backend/tests/:1-1` — `directory` — فقدان کامل تست‌ها
  ```
  دایرکتوری tests وجود ندارد
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
pytest + pytest-asyncio + httpx + GitHub Actions

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/auth.py` (سطر 1) — نیازمند تست‌های امنیتی
- `backend/app/routers/customers.py` (سطر 1) — نیازمند تست‌های یکپارچگی

## 🌐 نقشهٔ وابستگی‌ها
فقدان تست‌ها باعث می‌شود هر تغییر در کد potential regression ایجاد کند. این موضوع reliability پروژه را کاهش می‌دهد.

## 🔍 Context و وضعیت فعلی
پروژه فاقد تست‌های امنیتی و یکپارچگی است. در فایل pyproject.toml وابستگی pytest وجود دارد اما هیچ فایل تستی در backend/tests/ یا frontend/tests/ وجود ندارد. این موضوع باعث می‌شود رگرشن‌ها و آسیب‌پذیری‌های جدید شناسایی نشوند. با توجه به حساسیت سیستم بانکی، این یک نقص بحرانی است.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد
- [ ] پوشش کد (coverage) حداقل 80% باشد
- [ ] تست‌ها در CI/CD به صورت خودکار اجرا شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد ساختار tests/ در backend با پوشش:
   - تست‌های واحد برای models و schemas
   - تست‌های یکپارچگی برای API endpoints
   - تست‌های امنیتی برای SQL Injection, XSS, JWT
2. ایجاد tests/ در frontend با Jest و React Testing Library
3. اضافه کردن GitHub Actions برای اجرای خودکار تست‌ها
4. تنظیم coverage حداقل 80%

## 💡 نمونه‌های قبل/بعد
**قبل: بدون تست**

_قبل:_
```
# هیچ فایل تستی وجود ندارد
```

_بعد:_
```
backend/tests/
├── conftest.py
├── test_auth.py
├── test_customers.py
├── test_facilities.py
└── test_security.py
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing`
- `npm test --prefix frontend`

## ⚠️ ریسک‌ها و موارد احتیاط
نوشتن تست‌ها زمان‌بر است و ممکن است توسعه قابلیت‌های جدید را کند کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: high
- تخمین زمان: large

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 2 از 5
  id: 00478042-4983-4f7b-96c1-16c06a2fbf25
  عنوان اصلی: همگام‌سازی وابستگی‌های Python بین pyproject.toml و requirements.txt
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/requirements.txt, pyproject.toml

📋 acceptance_criteria کامل:
  - اعمال تغییر بدون شکستن تست‌های موجود [verify_method=backend_test] [verify_plan={"test_node": "tests/", "timeout_seconds": 120}]
  - linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["lint", "ruff", "flake8", "pylint"], "files_hint": ["pyproject.toml", "Makefile", "tox.ini"]}]
  - type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["mypy", "type: ignore", "pyright"], "files_hint": ["pyproject.toml", "Makefile", "tox.ini"]}]

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
عدم تطابق نسخه‌های وابستگی‌های Python بین pyproject.toml و requirements.txt

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/requirements.txt:1-14` — `dependencies` — فقدان redis, celery, httpx, python-dotenv
  ```
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  sqlalchemy==2.0.23
  alembic==1.13.1
  asyncpg==0.29.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  email-validator==2.1.0
  python-multipart==0.0.6
  python-jose[cryptography]==3.3.0
  PyJWT==2.8.0
  passlib[bcrypt]==1.7.4
  python-dateutil==2.8.2
  psycopg2-binary==2.9.9
  ```
- `pyproject.toml:20-30` — `dependencies` — شامل redis, celery, httpx, python-dotenv, pytest
  ```
  dependencies = [
      "fastapi>=0.100.0",
      "uvicorn[standard]>=0.22.0",
      "sqlalchemy>=2.0.0",
      "alembic>=1.11.0",
      "psycopg2-binary>=2.9.0",
      "pydantic>=2.0.0",
      "python-multipart>=0.0.6",
      "python-jose[cryptography]>=3.3.0",
      "passlib[bcrypt]>=1.7.4",
      "python-dotenv>=1.0.0",
      "redis>=4.5.0",
      "celery>=5.3.0",
      "httpx>=0.24.0",
      "pytest>=7.4.0",
      "pytest-asyncio>=0.21.0",
  ]
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Python project management with pyproject.toml and requirements.txt

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/Dockerfile` (سطر 1) — احتمالاً از requirements.txt برای نصب وابستگی‌ها استفاده می‌کند
- `docker-compose.yml` (سطر 1) — ممکن است سرویس‌های Redis یا Celery را تعریف کرده باشد

## 🌐 نقشهٔ وابستگی‌ها
این ناهماهنگی بین دو فایل مدیریت وابستگی باعث می‌شود که محیط‌های مختلف (توسعه، تست، تولید) وابستگی‌های متفاوتی داشته باشند.

## 🔍 Context و وضعیت فعلی
فایل pyproject.toml وابستگی‌هایی مانند redis>=4.5.0, celery>=5.3.0, httpx>=0.24.0 را مشخص کرده است، اما این وابستگی‌ها در فایل requirements.txt وجود ندارند. همچنین، فایل pyproject.toml به python-dotenv>=1.0.0 اشاره دارد، در حالی که requirements.txt از pydantic-settings==2.1.0 استفاده می‌کند که خود می‌تواند dotenv را مدیریت کند. این ناهماهنگی باعث می‌شود که محیط‌های توسعه و تولید وابستگی‌های متفاوتی داشته باشند و ممکن است برخی ویژگی‌ها (مانند کش Redis یا وظایف پس‌زمینه Celery) در محیط‌های خاص در دسترس نباشند.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] اعمال تغییر بدون شکستن تست‌های موجود
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. فایل requirements.txt را با pyproject.toml هماهنگ کنید. یا تمام وابستگی‌های pyproject.toml را به requirements.txt اضافه کنید، یا از pyproject.toml به عنوان منبع اصلی وابستگی‌ها استفاده کرده و فایل requirements.txt را با دستوری مانند 'pip freeze > requirements.txt' از یک محیط مجازی تمیز تولید کنید.

## 💡 نمونه‌های قبل/بعد
**نمونه 1**

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
- اولویت: high
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تسک 3 از 5
  id: c621424e-f75d-4196-8e29-b28c04aab88b
  عنوان اصلی: یکپارچه‌سازی default فیلد 'user_id'
  اولویت اصلی: high
  وضعیت verify قبلی: partial
  فایل‌های دخیل: -

📋 acceptance_criteria کامل:
  - `user_id` در همه‌جا از یک منبع default می‌گیرد [verify_method=static] [verify_plan={"grep_patterns": ["user_id.*default.*None", "user_id.*default.*payload.get", "user_id.*default.*lambda"], "files_hint": ["backend/app/models.py", "backend/app/schemas.py"]}]
  - تست fixture رفتار پیش‌فرض را تأیید می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_defaults.py::test_user_id_default", "timeout_seconds": 30}]
  - اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["migration.*user_id", "backward_compat.*user_id", "compat_layer.*user_id"], "files_hint": ["backend/migrations/", "backend/app/compat.py"]}]

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
تضاد default برای فیلد 'user_id'

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔍 Context و وضعیت فعلی
## 📋 شرح
فیلد `user_id` در `` در دو یا چند جای مختلف default value متفاوت دارد.

## 🤔 چرا مهم است
defaults متناقض باعث می‌شود رفتار سیستم به ترتیب اجرا/import وابسته شود — bug های غیرقابل reproduce.

## 🔍 جزئیات
- علت: field user_id has different defaults: ['None) -> str:', 'payload.get("user_id")']

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] `user_id` در همه‌جا از یک منبع default می‌گیرد
- [ ] تست fixture رفتار پیش‌فرض را تأیید می‌کند
- [ ] اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: همه جاهایی که `user_id` default می‌گیرد لیست کن.
گام ۲: یک default واحد انتخاب کن و یک منبع (مثل config یا constant).
گام ۳: تست fixture برای رفتار پیش‌فرض بنویس.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر default value برای کاربران فعلی silent behavior change است — حتماً release note بنویس.

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
تسک 4 از 5
  id: 5fa1a292-c7d8-4ef3-95ad-4725e8c3bb8a
  عنوان اصلی: Resolve stale assumption anti-pattern
  اولویت اصلی: high
  وضعیت verify قبلی: pending
  فایل‌های دخیل: backend/app/database.py

📋 acceptance_criteria کامل:
  - ریشه anti-pattern تشخیص داده شد [verify_method=static] [verify_plan={"grep_patterns": ["localhost", "127.0.0.1", "ssl", "verify", "certificate"], "files_hint": ["backend/app/database.py"]}]
  - یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["ssl", "verify", "certificate", "hostname"], "files_hint": ["backend/app/database.py"]}]
  - تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_database.py::test_ssl_edge_cases", "timeout_seconds": 60}]

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
Anti-pattern: Stale assumption

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/database.py:10`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/utils/security.py` — این فایل `database.py` را import می‌کند (caller)
- `backend/app/models/customer.py` — این فایل `database.py` را import می‌کند (caller)
- `backend/app/models/facility.py` — این فایل `database.py` را import می‌کند (caller)
- `backend/app/models/offer_letter.py` — این فایل `database.py` را import می‌کند (caller)

## 🔍 Context و وضعیت فعلی
SSL configuration assumes that if the database URL does not contain 'localhost' or '127.0.0.1', it is a remote database requiring SSL with disabled hostname verification and certificate validation. This is a fragile assumption: (1) Some local setups may use hostnames like 'db' in Docker, which would incorrectly trigger SSL; (2) Remote databases may require proper SSL verification; (3) The conditio

📁 file: backend/app/database.py (line 10)

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
- `python -m py_compile backend/app/database.py`
- `ruff check backend/app/database.py`
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
تسک 5 از 5
  id: cb7140d5-f580-4bc5-85e9-db51766cd905
  عنوان اصلی: تعیین وضعیت و حذف/مستندسازی offer_letter.py
  اولویت اصلی: low
  وضعیت verify قبلی: partial
  فایل‌های دخیل: backend/app/models/offer_letter.py

📋 acceptance_criteria کامل:
  - مشخص شد فایل dead است یا entry point/dynamic [verify_method=static] [verify_plan={"grep_patterns": ["from.*offer_letter.*import", "import.*offer_letter", "offer_letter"], "files_hint": ["backend/app/models/offer_letter.py"]}]
  - اقدام مناسب: حذف یا مستندسازی [verify_method=static] [verify_plan={"grep_patterns": ["offer_letter"], "files_hint": ["backend/app/models/offer_letter.py"]}]
  - تست‌های مربوطه (در صورت حذف) هم حذف شدند [verify_method=static] [verify_plan={"grep_patterns": ["test.*offer_letter", "offer_letter.*test"], "files_hint": ["tests/"]}]

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
فایل بدون import مرجع: offer_letter.py

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/models/offer_letter.py`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/database.py` — `offer_letter.py` این فایل را import می‌کند

## 🌐 نقشهٔ وابستگی‌ها
این مورد در پایپ‌لاین کدبیس به فایل‌های اطراف وابسته است؛ قبل از تغییر، grep روی نام symbol/path اصلی انجام شود.

## 🔍 Context و وضعیت فعلی
## 📋 شرح
فایل `backend/app/models/offer_letter.py` در هیچ import/require دیده نمی‌شود.

## 🤔 چرا مهم است
فایل orphan یا (الف) از قبل dead code است، یا (ب) entry point است (مثل migrations، scripts، CLI) که از طریق import import نمی‌شود، یا (ج) dynamic import می‌شود (lazy load).

## 🔍 جزئیات
- علت: reverse_import=0 and not entry-point

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] مشخص شد فایل dead است یا entry point/dynamic
- [ ] اقدام مناسب: حذف یا مستندسازی
- [ ] تست‌های مربوطه (در صورت حذف) هم حذف شدند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: grep روی نام فایل (بدون پسوند) و class/function اصلی آن.
گام ۲: اگر CLI/script است، در README ذکر کن.
گام ۳: اگر dead است، حذف کن (همراه با تست‌های مربوطه).

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/models/offer_letter.py`
- `ruff check backend/app/models/offer_letter.py`
- `pytest -x`

## ⚠️ ریسک‌ها و موارد احتیاط
فایل ممکن است در deployment pipeline یا CI به‌صورت direct invocation مصرف شود (مثل `python migrations/run.py`). قبل از حذف، در CI configs و scripts/ هم چک کن.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: cleanup
- اولویت: low
- تخمین زمان: medium

✅ مراحل قبلاً done شده (در super-task به‌عنوان pre_done):
  (هیچ مرحله‌ای قبلاً done نشده بود)

🔧 مراحل remaining که در super-task باید انجام شوند:
  (همهٔ مراحل remaining هستند)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- ساختار AC ها: acceptance_criteria با verify_method و verify_plan و evidence_locations برای هر AC
- edge cases را در نظر بگیر و در پرامپت ذکر کن
- وابستگی‌ها را اول حل کن (dependency-aware ordering)
- اگر بخشی از یکی از تسک‌ها قبلاً done است (pre_done در بالا)، تکرار نکن — فقط روی remaining_parts تمرکز کن
- در commit message: `merged-from: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9, 00478042-4983-4f7b-96c1-16c06a2fbf25, c621424e-f75d-4196-8e29-b28c04aab88b, 5fa1a292-c7d8-4ef3-95ad-4725e8c3bb8a, cb7140d5-f580-4bc5-85e9-db51766cd905`
- task_steps را با dependency-aware ordering مرتب کن
- هیچ کار قبلاً done شده‌ای نباید دوباره انجام شود
- هیچ خلاصه‌سازی نکن — جزئیات کامل از همهٔ منابع باید حفظ شوند


## Acceptance Criteria

1. حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد _(verify: backend_test)_
2. پوشش کد (coverage) حداقل 80% باشد _(verify: manual_only)_
3. تست‌ها در CI/CD به صورت خودکار اجرا شوند _(verify: static)_
4. اعمال تغییر بدون شکستن تست‌های موجود _(verify: backend_test)_
5. linter بدون warning عبور می‌کند _(verify: static)_
6. type-check موفق است _(verify: static)_
7. `user_id` در همه‌جا از یک منبع default می‌گیرد _(verify: static)_
8. تست fixture رفتار پیش‌فرض را تأیید می‌کند _(verify: backend_test)_
9. اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد _(verify: static)_
10. ریشه anti-pattern تشخیص داده شد _(verify: static)_
11. یا کد اصلاح شد، یا کامنت توجیهی اضافه شد _(verify: static)_
12. تست edge case نوشته شد _(verify: backend_test)_
13. مشخص شد فایل dead است یا entry point/dynamic _(verify: static)_
14. اقدام مناسب: حذف یا مستندسازی _(verify: static)_
15. تست‌های مربوطه (در صورت حذف) هم حذف شدند _(verify: static)_

## Task Steps

### Step 1: ایجاد ساختار دایرکتوری tests/ و فایل‌های تست پایه برای backend
**Status:** `done` (100%)
**Scope:** ایجاد دایرکتوری backend/tests/ و فایل‌های خالی conftest.py, test_auth.py, test_customers.py, test_facilities.py, test_security.py. این مرحله فقط شامل ایجاد ساختار فایل است، نه نوشتن محتوای تست. نکته حیاتی: مسیر دقیق backend/tests/ رعایت شود و فایل‌ها دقیقاً با نام‌های مشخص شده ایجاد شوند.
**Excerpt:**
```
## 🎯 هدف
رفع عدم وجود تست‌های امنیتی و یکپارچگی

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/pyproject.toml:30-35` — `dev-dependencies` — وابستگی pytest وجود دارد اما هیچ تستی نوشته نشده
  ```
  [project.optional-dependencies]
  dev = [
      "pytest>=7.4.0",
      "pytest-asyncio>=0.21.0",
  ]
  ```
- `backend/tests/:1-1` — `directory` — فقدان کامل تست‌ها
  ```
  دایرکتوری tests وجود ندارد
  ```

## 💡 نمونه‌های قبل/بعد
**قبل: بدون تست**

_قبل:_
```
# هیچ فایل تستی وجود ندارد
```

_بعد:_
```
backend/tests/
├── conftest.py
├── test_auth.py
├── test_customers.py
├── test_facilities.py
└── test_security.py
```
```

### Step 2: نوشتن تست‌های واحد برای models و schemas backend
**Status:** `done` (100%)
**Scope:** نوشتن تست‌های واحد برای مدل‌ها و اسکیماهای backend در فایل‌های test_*.py. این مرحله شامل تست‌های مربوط به models.py و schemas.py است. نکته حیاتی: تست‌ها باید با pytest و pytest-asyncio نوشته شوند و حداقل 10 تست واحد برای این بخش ایجاد شود.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد ساختار tests/ در backend با پوشش:
   - تست‌های واحد برای models و schemas
   - تست‌های یکپارچگی برای API endpoints
   - تست‌های امنیتی برای SQL Injection, XSS, JWT

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد
- [ ] پوشش کد (coverage) حداقل 80% باشد
- [ ] تست‌ها در CI/CD به صورت خودکار اجرا شوند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)
```

### Step 3: نوشتن تست‌های یکپارچگی برای API endpoints (auth, customers, facilities)
**Status:** `partial` (70%)
**Scope:** نوشتن تست‌های یکپارچگی برای endpointهای API شامل auth.py, customers.py, facilities.py. این تست‌ها باید با httpx و TestClient اجرا شوند. نکته حیاتی: تست‌ها باید حداقل 20 تست یکپارچگی را پوشش دهند و شامل سناریوهای موفق و خطا باشند.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد ساختار tests/ در backend با پوشش:
   - تست‌های واحد برای models و schemas
   - تست‌های یکپارچگی برای API endpoints
   - تست‌های امنیتی برای SQL Injection, XSS, JWT

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/auth.py` (سطر 1) — نیازمند تست‌های امنیتی
- `backend/app/routers/customers.py` (سطر 1) — نیازمند تست‌های یکپارچگی
```

### Step 4: نوشتن تست‌های امنیتی برای SQL Injection, XSS, JWT
**Status:** `partial` (60%)
**Scope:** نوشتن تست‌های امنیتی در test_security.py که شامل سناریوهای SQL Injection, XSS, و JWT است. این تست‌ها باید حملات رایج را شبیه‌سازی کنند و اطمینان حاصل کنند که سیستم در برابر آنها مقاوم است. نکته حیاتی: تست‌های JWT باید شامل توکن‌های منقضی، دستکاری‌شده، و با امضای نامعتبر باشند.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. 1. ایجاد ساختار tests/ در backend با پوشش:
   - تست‌های واحد برای models و schemas
   - تست‌های یکپارچگی برای API endpoints
   - تست‌های امنیتی برای SQL Injection, XSS, JWT

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/routers/auth.py` (سطر 1) — نیازمند تست‌های امنیتی
```

### Step 5: تنظیم GitHub Actions برای اجرای خودکار تست‌ها
**Status:** `done` (100%)
**Scope:** ایجاد یا اصلاح فایل workflow GitHub Actions برای اجرای خودکار pytest در هر push و pull request. این مرحله شامل تنظیم مراحل نصب وابستگی‌ها، اجرای تست‌ها، و گزارش نتایج است. نکته حیاتی: workflow باید pytest را با پوشش کد اجرا کند و در صورت failure، هشدار دهد.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد
- [ ] پوشش کد (coverage) حداقل 80% باشد
- [ ] تست‌ها در CI/CD به صورت خودکار اجرا شوند

## 🪜 مراحل اجرایی پیشنهادی
3. اضافه کردن GitHub Actions برای اجرای خودکار تست‌ها
4. تنظیم coverage حداقل 80%
```

### Step 6: تنظیم coverage حداقل 80% برای backend
**Status:** `partial` (70%)
**Scope:** اضافه کردن تنظیمات coverage به pyproject.toml یا فایل pytest.ini برای اعمال حداقل 80% پوشش کد. این مرحله شامل تنظیم pytest-cov و تعیین آستانه است. نکته حیاتی: coverage باید برای کل backend/app/ محاسبه شود و در صورت کمتر از 80%، pytest با خطا مواجه شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] حداقل 50 تست واحد و یکپارچگی برای backend وجود داشته باشد
- [ ] پوشش کد (coverage) حداقل 80% باشد
- [ ] تست‌ها در CI/CD به صورت خودکار اجرا شوند

## 🪜 مراحل اجرایی پیشنهادی
4. تنظیم coverage حداقل 80%

## 🧪 دستورات اعتبارسنجی
- `pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing`
```

### Step 7: بررسی و هماهنگ‌سازی وابستگی‌های requirements.txt با pyproject.toml
**Status:** `done` (100%)
**Scope:** مقایسه و هماهنگ‌سازی لیست وابستگی‌های فایل requirements.txt با pyproject.toml. این مرحله شامل اضافه کردن وابستگی‌های گمشده (redis, celery, httpx, python-dotenv) به requirements.txt و اطمینان از تطابق نسخه‌ها است. نکته حیاتی: وابستگی‌های dev مانند pytest نباید به requirements.txt اضافه شوند.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
عدم تطابق نسخه‌های وابستگی‌های Python بین pyproject.toml و requirements.txt

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/requirements.txt:1-14` — `dependencies` — فقدان redis, celery, httpx, python-dotenv
  ```
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  sqlalchemy==2.0.23
  alembic==1.13.1
  asyncpg==0.29.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  email-validator==2.1.0
  python-multipart==0.0.6
  python-jose[cryptography]==3.3.0
  PyJWT==2.8.0
  passlib[bcrypt]==1.7.4
  python-dateutil==2.8.2
  psycopg2-binary==2.9.9
  ```
- `pyproject.toml:20-30` — `dependencies` — شامل redis, celery, httpx, python-dotenv, pytest
  ```
  dependencies = [
      "fastapi>=0.100.0",
      "uvicorn[standard]>=0.22.0",
      "sqlalchemy>=2.0.0",
      "alembic>=1.11.0",
      "psycopg2-binary>=2.9.0",
      "pydantic>=2.0.0",
      "python-multipart>=0.0.6",
      "python-jose[cryptography]>=3.3.0",
      "passlib[bcrypt]>=1.7.4",
      "python-dotenv>=1.0.0",
      "redis>=4.5.0",
      "celery>=5.3.0",
      "httpx>=0.24.0",
      "pytest>=7.4.0",
      "pytest-asyncio>=0.21.0",
  ]
  ```
```

### Step 8: اجرای تست‌های موجود برای اطمینان از عدم شکستن پس از تغییر وابستگی‌ها
**Status:** `done` (100%)
**Scope:** اجرای کامل تست‌های backend با pytest برای اطمینان از اینکه تغییرات در requirements.txt باعث شکستن تست‌ها نشده است. این مرحله شامل اجرای `pytest backend/tests/ -v` و بررسی نتایج است. نکته حیاتی: اگر تستی fail شود، باید علت بررسی و رفع شود.
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

## 🧪 دستورات اعتبارسنجی
- `pytest`
- `npm run build`
- `npm run lint`
```

### Step 9: اجرای linter و type-check برای اطمینان از عدم وجود warning
**Status:** `done` (100%)
**Scope:** اجرای linter (ruff/flake8) و type-check (mypy) روی کدهای backend برای اطمینان از عدم وجود warning پس از تغییر وابستگی‌ها. این مرحله شامل اجرای دستورات مربوطه و رفع هرگونه warning است. نکته حیاتی: اگر warning جدیدی ایجاد شده، باید رفع شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] linter بدون warning عبور می‌کند [verify_method=static] [verify_plan={"grep_patterns": ["lint", "ruff", "flake8", "pylint"], "files_hint": ["pyproject.toml", "Makefile", "tox.ini"]}]
- [ ] type-check موفق است [verify_method=static] [verify_plan={"grep_patterns": ["mypy", "type: ignore", "pyright"], "files_hint": ["pyproject.toml", "Makefile", "tox.ini"]}]
```

### Step 10: شناسایی تمام مکان‌های دارای default متفاوت برای فیلد user_id
**Status:** `done` (100%)
**Scope:** جستجوی کامل در کدبس backend برای یافتن تمام مکان‌هایی که فیلد user_id دارای default value متفاوت است. این مرحله شامل grep روی فایل‌های models.py, schemas.py, و سایر فایل‌های مرتبط است. نکته حیاتی: نتایج جستجو باید مستند شوند و لیست کاملی از مکان‌ها تهیه شود.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
تضاد default برای فیلد 'user_id'

## 📍 موقعیت دقیق در پروژه
_(فایل‌های دقیق توسط مجری شناسایی شوند — هیچ موقعیت مشخصی استخراج نشد)_

## 🔍 جزئیات
- علت: field user_id has different defaults: ['None) -> str:', 'payload.get("user_id")']

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: همه جاهایی که `user_id` default می‌گیرد لیست کن.
```

### Step 11: انتخاب یک منبع واحد برای default value فیلد user_id
**Status:** `done` (100%)
**Scope:** انتخاب یک منبع واحد (مانند config یا constant) برای default value فیلد user_id و اعمال آن در تمام مکان‌های شناسایی‌شده. این مرحله شامل ایجاد یک constant یا config جدید و جایگزینی تمام default values پراکنده با آن است. نکته حیاتی: تغییر باید backward-compatible باشد و رفتار فعلی را نشکند.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: همه جاهایی که `user_id` default می‌گیرد لیست کن.
گام ۲: یک default واحد انتخاب کن و یک منبع (مثل config یا constant).

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] `user_id` در همه‌جا از یک منبع default می‌گیرد
- [ ] تست fixture رفتار پیش‌فرض را تأیید می‌کند
- [ ] اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد
```

### Step 12: نوشتن تست fixture برای تأیید رفتار پیش‌فرض user_id
**Status:** `done` (100%)
**Scope:** نوشتن یک تست fixture در tests/test_defaults.py که رفتار پیش‌فرض فیلد user_id را تأیید می‌کند. این تست باید اطمینان حاصل کند که در صورت عدم ارائه user_id، مقدار پیش‌فرض صحیح استفاده می‌شود. نکته حیاتی: نام تست باید test_user_id_default باشد.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] `user_id` در همه‌جا از یک منبع default می‌گیرد
- [ ] تست fixture رفتار پیش‌فرض را تأیید می‌کند [verify_method=backend_test] [verify_plan={"test_node": "tests/test_defaults.py::test_user_id_default", "timeout_seconds": 30}]
- [ ] اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: همه جاهایی که `user_id` default می‌گیرد لیست کن.
گام ۲: یک default واحد انتخاب کن و یک منبع (مثل config یا constant).
گام ۳: تست fixture برای رفتار پیش‌فرض بنویس.
```

### Step 13: اضافه کردن backward-compat layer در صورت تغییر default value user_id
**Status:** `not_done` (0%)
**Scope:** اگر default value user_id تغییر کرده است، یک backward-compat layer در backend/app/compat.py اضافه کنید تا از شکستن کدهای موجود جلوگیری شود. این مرحله شامل ایجاد توابع compat و مستندسازی تغییر است. نکته حیاتی: اگر تغییری در default value رخ نداده، این مرحله را با یک کامیت توضیحی (no-op) ثبت کنید.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] `user_id` در همه‌جا از یک منبع default می‌گیرد
- [ ] تست fixture رفتار پیش‌فرض را تأیید می‌کند
- [ ] اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["migration.*user_id", "backward_compat.*user_id", "compat_layer.*user_id"], "files_hint": ["backend/migrations/", "backend/app/compat.py"]}]

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر default value برای کاربران فعلی silent behavior change است — حتماً release note بنویس.
```

### Step 14: بررسی و تشخیص ریشه anti-pattern در backend/app/database.py
**Status:** `done` (100%)
**Scope:** بررسی دقیق خط 10 فایل backend/app/database.py برای تشخیص anti-pattern مربوط به SSL configuration. این مرحله شامل تحلیل منطق شرطی که بر اساس hostname SSL را فعال/غیرفعال می‌کند و شناسایی مشکلات آن است. نکته حیاتی: نتایج تشخیص باید مستند شوند.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
Anti-pattern: Stale assumption

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/database.py:10`

## 🔍 Context و وضعیت فعلی
SSL configuration assumes that if the database URL does not contain 'localhost' or '127.0.0.1', it is a remote database requiring SSL with disabled hostname verification and certificate validation. This is a fragile assumption: (1) Some local setups may use hostnames like 'db' in Docker, which would incorrectly trigger SSL; (2) Remote databases may require proper SSL verification; (3) The conditio

📁 file: backend/app/database.py (line 10)

🎯 پیشنهاد: این الگو معمولاً منطق سیستم را در شرایط لبه می‌شکند.
```

### Step 15: اصلاح یا مستندسازی anti-pattern در backend/app/database.py
**Status:** `done` (100%)
**Scope:** اصلاح منطق SSL configuration در backend/app/database.py یا اضافه کردن کامنت توجیهی. اگر اصلاح انجام می‌شود، باید منطق جدید بر اساس پیکربندی explicit (مانند variable environment) باشد. اگر مستندسازی انجام می‌شود، باید دلیل حفظ وضعیت فعلی توضیح داده شود. نکته حیاتی: هر دو گزینه باید با تست edge case همراه باشند.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] ریشه anti-pattern تشخیص داده شد
- [ ] یا کد اصلاح شد، یا کامنت توجیهی اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["ssl", "verify", "certificate", "hostname"], "files_hint": ["backend/app/database.py"]}]
- [ ] تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_database.py::test_ssl_edge_cases", "timeout_seconds": 60}]

## 🪜 مراحل اجرایی پیشنهادی
1. بازنگری منطق در این نقطه و اضافه‌کردن guard/comment مناسب.
```

### Step 16: نوشتن تست edge case برای SSL configuration در test_database.py
**Status:** `done` (100%)
**Scope:** نوشتن تست edge case در tests/test_database.py با نام test_ssl_edge_cases که سناریوهای مختلف SSL configuration را پوشش می‌دهد. این تست باید شامل مواردی مانند hostname 'db' در Docker, localhost, 127.0.0.1, و remote database با SSL باشد. نکته حیاتی: timeout تست 60 ثانیه است.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] ریشه anti-pattern تشخیص داده شد
- [ ] یا کد اصلاح شد، یا کامنت توجیهی اضافه شد
- [ ] تست edge case نوشته شد [verify_method=backend_test] [verify_plan={"test_node": "tests/test_database.py::test_ssl_edge_cases", "timeout_seconds": 60}]

## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/database.py`
- `ruff check backend/app/database.py`
- `pytest -x`
```

### Step 17: اجرای py_compile و ruff check روی backend/app/database.py
**Status:** `not_done` (0%)
**Scope:** اجرای دستورات `python -m py_compile backend/app/database.py` و `ruff check backend/app/database.py` برای اطمینان از عدم وجود خطاهای کامپایل و lint پس از تغییرات. نکته حیاتی: اگر خطایی وجود دارد، باید رفع شود.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/database.py`
- `ruff check backend/app/database.py`
- `pytest -x`
```

### Step 18: بررسی وضعیت فایل offer_letter.py با grep روی importها
**Status:** `not_done` (0%)
**Scope:** اجرای grep روی کل کدبس برای یافتن هرگونه import یا ارجاع به فایل offer_letter.py. این مرحله شامل جستجوی `from.*offer_letter.*import`, `import.*offer_letter`, و `offer_letter` در تمام فایل‌ها است. نکته حیاتی: نتایج جستجو باید مستند شوند تا مشخص شود فایل dead است یا entry point.
**Excerpt:**
```
## 🎯 هدف (خلاصه ساختاریافته)
فایل بدون import مرجع: offer_letter.py

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/models/offer_letter.py`

## 🔍 جزئیات
- علت: reverse_import=0 and not entry-point

## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: grep روی نام فایل (بدون پسوند) و class/function اصلی آن.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] مشخص شد فایل dead است یا entry point/dynamic [verify_method=static] [verify_plan={"grep_patterns": ["from.*offer_letter.*import", "import.*offer_letter", "offer_letter"], "files_hint": ["backend/app/models/offer_letter.py"]}]
```

### Step 19: بررسی entry point بودن offer_letter.py در CI/CD و scripts
**Status:** `not_done` (0%)
**Scope:** بررسی فایل‌های CI/CD (مانند .github/workflows/*.yml) و scripts/ برای اطمینان از اینکه offer_letter.py به صورت مستقیم (direct invocation) استفاده نمی‌شود. این مرحله شامل جستجوی `offer_letter` در این فایل‌ها است. نکته حیاتی: اگر فایل در CI/CD استفاده می‌شود، نباید حذف شود.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: grep روی نام فایل (بدون پسوند) و class/function اصلی آن.
گام ۲: اگر CLI/script است، در README ذکر کن.

## ⚠️ ریسک‌ها و موارد احتیاط
فایل ممکن است در deployment pipeline یا CI به‌صورت direct invocation مصرف شود (مثل `python migrations/run.py`). قبل از حذف، در CI configs و scripts/ هم چک کن.
```

### Step 20: حذف فایل offer_letter.py در صورت dead بودن
**Status:** `not_done` (0%)
**Scope:** اگر فایل offer_letter.py dead است (هیچ import و استفاده‌ای ندارد)، آن را حذف کنید. این مرحله شامل حذف فایل backend/app/models/offer_letter.py و commit تغییر است. نکته حیاتی: قبل از حذف، مطمئن شوید که فایل در CI/CD یا scripts استفاده نمی‌شود.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: grep روی نام فایل (بدون پسوند) و class/function اصلی آن.
گام ۲: اگر CLI/script است، در README ذکر کن.
گام ۳: اگر dead است، حذف کن (همراه با تست‌های مربوطه).

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] مشخص شد فایل dead است یا entry point/dynamic
- [ ] اقدام مناسب: حذف یا مستندسازی
- [ ] تست‌های مربوطه (در صورت حذف) هم حذف شدند
```

### Step 21: حذف تست‌های مربوط به offer_letter.py در صورت حذف فایل
**Status:** `not_done` (0%)
**Scope:** اگر فایل offer_letter.py حذف شده است، تست‌های مربوط به آن (در صورت وجود) نیز باید حذف شوند. این مرحله شامل جستجوی `test.*offer_letter` و `offer_letter.*test` در tests/ و حذف فایل‌های مربوطه است. نکته حیاتی: اگر تستی وجود ندارد، این مرحله را با یک کامیت توضیحی ثبت کنید.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] مشخص شد فایل dead است یا entry point/dynamic
- [ ] اقدام مناسب: حذف یا مستندسازی
- [ ] تست‌های مربوطه (در صورت حذف) هم حذف شدند [verify_method=static] [verify_plan={"grep_patterns": ["test.*offer_letter", "offer_letter.*test"], "files_hint": ["tests/"]}]
```

### Step 22: اجرای py_compile و ruff check روی backend/app/models/offer_letter.py (در صورت وجود)
**Status:** `partial` (50%)
**Scope:** اگر فایل offer_letter.py حذف نشده است (به دلیل entry point بودن)، اجرای `python -m py_compile backend/app/models/offer_letter.py` و `ruff check backend/app/models/offer_letter.py` برای اطمینان از کیفیت کد. نکته حیاتی: اگر فایل حذف شده است، این مرحله را با یک کامیت توضیحی ثبت کنید.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `python -m py_compile backend/app/models/offer_letter.py`
- `ruff check backend/app/models/offer_letter.py`
- `pytest -x`
```

### Step 23: اجرای کامل pytest برای اطمینان از عدم شکستن تست‌ها پس از تغییرات
**Status:** `done` (100%)
**Scope:** اجرای کامل `pytest -x` برای اطمینان از اینکه تمام تغییرات اعمال‌شده (تغییر وابستگی‌ها، اصلاح database.py، حذف offer_letter.py) باعث شکستن هیچ تستی نشده است. نکته حیاتی: اگر تستی fail شود، باید علت بررسی و رفع شود.
**Excerpt:**
```
## 🧪 دستورات اعتبارسنجی
- `pytest -x`

## ⚠️ ریسک‌ها و موارد احتیاط
پیش از merge، تست‌های موجود اجرا شوند تا رگرشن ایجاد نشود.
```

### Step 24: بررسی و مستندسازی فایل offer_letter.py در README در صورت entry point بودن
**Status:** `not_done` (0%)
**Scope:** اگر فایل offer_letter.py entry point است (مثلاً در CI/CD یا scripts استفاده می‌شود)، آن را در README مستند کنید. این مرحله شامل اضافه کردن توضیح در README درباره نحوه استفاده از این فایل است. نکته حیاتی: اگر فایل dead است و حذف شده، این مرحله را با یک کامیت توضیحی ثبت کنید.
**Excerpt:**
```
## 🪜 مراحل اجرایی پیشنهادی
1. گام ۱: grep روی نام فایل (بدون پسوند) و class/function اصلی آن.
گام ۲: اگر CLI/script است، در README ذکر کن.
گام ۳: اگر dead است، حذف کن (همراه با تست‌های مربوطه).
```

### Step 25: ایجاد فایل compat.py برای backward compatibility در صورت نیاز
**Status:** `not_done` (0%)
**Scope:** اگر در مراحل قبلی نیاز به backward-compat layer تشخیص داده شد، فایل backend/app/compat.py را ایجاد کنید. این فایل شامل توابعی است که رفتار قدیمی را شبیه‌سازی می‌کنند. نکته حیاتی: اگر نیازی به compat layer نیست، این مرحله را با یک کامیت توضیحی ثبت کنید.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] اگر default value تغییر کرد، migration یا backward-compat layer اضافه شد [verify_method=static] [verify_plan={"grep_patterns": ["migration.*user_id", "backward_compat.*user_id", "compat_layer.*user_id"], "files_hint": ["backend/migrations/", "backend/app/compat.py"]}]
```

### Step 26: بررسی و رفع warningهای linter در تمام فایل‌های تغییر یافته
**Status:** `done` (100%)
**Scope:** اجرای linter (ruff) روی تمام فایل‌هایی که در این super-task تغییر کرده‌اند و رفع هرگونه warning. این مرحله شامل backend/app/database.py, backend/app/compat.py, backend/tests/*.py, و backend/requirements.txt است. نکته حیاتی: هیچ warning جدیدی نباید اضافه شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] linter بدون warning عبور می‌کند

## 🧪 دستورات اعتبارسنجی
- `ruff check backend/`
```

### Step 27: بررسی و رفع warningهای type-check در تمام فایل‌های تغییر یافته
**Status:** `done` (100%)
**Scope:** اجرای type-check (mypy) روی تمام فایل‌هایی که در این super-task تغییر کرده‌اند و رفع هرگونه warning. این مرحله شامل backend/app/database.py, backend/app/compat.py, backend/tests/*.py است. نکته حیاتی: هیچ warning جدیدی نباید اضافه شود.
**Excerpt:**
```
## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🧪 دستورات اعتبارسنجی
- `mypy backend/`
```

### Step 28: نوشتن commit message با merged-from IDs
**Status:** `done` (100%)
**Scope:** نوشتن commit message برای تمام تغییرات این super-task که شامل merged-from IDs تمام 5 تسک است. این مرحله شامل ایجاد یک commit با پیام واضح و جامع است. نکته حیاتی: commit message باید شامل `merged-from: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9, 00478042-4983-4f7b-96c1-16c06a2fbf25, c621424e-f75d-4196-8e29-b28c04aab88b, 5fa1a292-c7d8-4ef3-95ad-4725e8c3bb8a, cb7140d5-f580-4bc5-85e9-db51766cd905` باشد.
**Excerpt:**
```
💡 نکات استاندارد (همان bullet هایی که در ساخت پرامپت‌های معمولی پروژه رعایت می‌شود — وراثت کامل، نه کپی):
- در commit message: `merged-from: 81c822a5-0e5c-4823-a7a3-6cb68c6104f9, 00478042-4983-4f7b-96c1-16c06a2fbf25, c621424e-f75d-4196-8e29-b28c04aab88b, 5fa1a292-c7d8-4ef3-95ad-4725e8c3bb8a, cb7140d5-f580-4bc5-85e9-db51766cd905`
```

### Step 29: ایجاد PR description با checklist از تمام کامیت‌ها
**Status:** `done` (100%)
**Scope:** ایجاد یک PR description که شامل checklist از تمام کامیت‌های این super-task است. این checklist باید ترتیب منطقی (foundation → core → integration → tests) را رعایت کند. نکته حیاتی: هیچ کامیتی نباید از قلم بیفتد.
**Excerpt:**
```
📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.
```

### Step 30: بررسی نهایی و merge تغییرات
**Status:** `done` (100%)
**Scope:** بررسی نهایی تمام تغییرات، اطمینان از عبور تمام CI checks، و merge کردن PR. این مرحله شامل تأیید نهایی است. نکته حیاتی: قبل از merge، مطمئن شوید که تمام acceptance criteriaهای تمام 5 تسک برآورده شده‌اند.
**Excerpt:**
```
## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.
```

### Step 31: نوشتن release note برای تغییرات اعمال‌شده
**Status:** `done` (100%)
**Scope:** نوشتن release note برای تمام تغییرات این super-task، شامل تغییرات در وابستگی‌ها، اصلاح anti-pattern، پاکسازی dead code، و اضافه شدن تست‌ها. نکته حیاتی: release note باید شامل warning درباره تغییرات backward-incompatible باشد.
**Excerpt:**
```
## ⚠️ ریسک‌ها و موارد احتیاط
تغییر default value برای کاربران فعلی silent behavior change است — حتماً release note بنویس.
```
