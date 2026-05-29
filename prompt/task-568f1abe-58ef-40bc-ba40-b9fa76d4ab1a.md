---
task_id: 568f1abe-58ef-40bc-ba40-b9fa76d4ab1a
title: رفع عدم اعتبارسنجی ورودی در Pydantic models
type: security
priority: high
execution_priority: 2300
status: awaiting_review
external_status: pending
verification_status: partial
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-05-10T15:32:15.291639+00:00'
updated_at: '2026-05-29T16:40:51.762569+00:00'
target_files:
- backend/app/schemas/__init__.py
- backend/app/schemas/facility.py
---

# رفع عدم اعتبارسنجی ورودی در Pydantic models

## Raw Idea

در backend/app/schemas/__init__.py و فایل‌های schemas مربوطه، بسیاری از فیلدها بدون اعتبارسنجی مناسب تعریف شده‌اند. مثلاً فیلدهای شماره تلفن، کد ملی، ایمیل و مقادیر عددی بدون validation pattern یا محدودیت طول هستند. این موضوع باعث می‌شود داده‌های نامعتبر وارد دیتابیس شوند و همچنین امکان حملات XSS از طریق فیلدهای متنی فراهم شود.

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

## Acceptance Criteria

1. ورودی‌های نامعتبر با خطای 422 رد شوند _(verify: api_response)_
2. تمامی فیلدهای متنی محدودیت طول داشته باشند _(verify: static)_
3. الگوهای regex برای فیلدهای حساس اعمال شده باشد _(verify: static)_
