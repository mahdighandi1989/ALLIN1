---
task_id: b0f3c4cc-4cf0-49cf-b678-0d64511ecca8
title: رفع SQL Injection در queryهای مستقیم SQL
type: security
priority: critical
execution_priority: 100
status: done
external_status: pending
verification_status: done
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-10T15:32:15.291515+00:00'
updated_at: '2026-05-29T20:07:55.843705+00:00'
archived: true
archived_at: '2026-05-11T09:42:41.076853+00:00'
target_files:
- backend/app/routers/customers.py
- backend/app/routers/facilities.py
---

# رفع SQL Injection در queryهای مستقیم SQL

## Raw Idea

در backend/app/routers/customers.py و backend/app/routers/facilities.py از رشته‌های SQL مستقیم با f-string برای ساخت query استفاده شده است. این روش به مهاجم اجازه تزریق SQL از طریق پارامترهای ورودی را می‌دهد. مثال: query = f"SELECT * FROM customers WHERE name = '{customer_name}'" که customer_name از request body می‌آید. این آسیب‌پذیری می‌تواند منجر به نشت تمام داده‌های بانکی شود.

## Prompt

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
رفع SQL Injection در queryهای مستقیم SQL

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/routers/customers.py:30-45` — `search_customers` — SQL Injection مستقیم از طریق f-string
  ```python
  @router.get("/customers/search")
  async def search_customers(name: str, db: Session = Depends(get_db)):
      query = f"SELECT * FROM customers WHERE name LIKE '%{name}%'"
      result = db.execute(text(query)).fetchall()
  ```
- `backend/app/routers/facilities.py:25-40` — `get_facilities_by_type` — SQL Injection از طریق path parameter
  ```python
  @router.get("/facilities/{facility_type}")
  async def get_facilities_by_type(facility_type: str, db: Session = Depends(get_db)):
      query = f"SELECT * FROM facilities WHERE type = '{facility_type}'"
      result = db.execute(text(query)).fetchall()
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
FastAPI + SQLAlchemy + PostgreSQL

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/models/customer.py` (سطر 1) — مدل SQLAlchemy برای جایگزینی query مستقیم
- `backend/app/models/facility.py` (سطر 1) — مدل SQLAlchemy برای جایگزینی query مستقیم

## 🌐 نقشهٔ وابستگی‌ها
این endpointها برای جستجوی مشتریان و تسهیلات استفاده می‌شوند و در معرض حملات SQL Injection هستند.

## 🔍 Context و وضعیت فعلی
در backend/app/routers/customers.py و backend/app/routers/facilities.py از رشته‌های SQL مستقیم با f-string برای ساخت query استفاده شده است. این روش به مهاجم اجازه تزریق SQL از طریق پارامترهای ورودی را می‌دهد. مثال: query = f"SELECT * FROM customers WHERE name = '{customer_name}'" که customer_name از request body می‌آید. این آسیب‌پذیری می‌تواند منجر به نشت تمام داده‌های بانکی شود.

## ✅ معیار پذیرش (Acceptance Criteria)
- [ ] تلاش برای SQL Injection خطای 400 یا 500 برگرداند نه داده
- [ ] تمام queryها از SQLAlchemy ORM استفاده کنند
- [ ] هیچ f-string در queryهای SQL وجود نداشته باشد
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. 1. تمام queryهای مستقیم SQL را با SQLAlchemy ORM جایگزین کنید.
2. از پارامترهای باند شده (bound parameters) استفاده کنید.
3. یک linter امنیتی مانند bandit به CI اضافه کنید.
4. تمام endpointهای API را برای استفاده از ORM بازنویسی کنید.

## 💡 نمونه‌های قبل/بعد
**قبل: query مستقیم با f-string**

_قبل:_
```
query = f"SELECT * FROM customers WHERE name LIKE '%{name}%'"
result = db.execute(text(query)).fetchall()
```

_بعد:_
```
result = db.query(Customer).filter(Customer.name.ilike(f'%{name}%')).all()
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `curl -X GET "http://localhost:8000/customers/search?name=' OR 1=1--"`
- `pytest tests/test_customers.py -v -k "test_sql_injection_protection"`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر به ORM ممکن است performance را تحت تأثیر قرار دهد، نیاز به benchmark دارد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: security
- اولویت: critical
- تخمین زمان: medium

## Acceptance Criteria

1. تلاش برای SQL Injection خطای 400 یا 500 برگرداند نه داده _(verify: api_response)_
2. تمام queryها از SQLAlchemy ORM استفاده کنند _(verify: static)_
3. هیچ f-string در queryهای SQL وجود نداشته باشد _(verify: static)_
