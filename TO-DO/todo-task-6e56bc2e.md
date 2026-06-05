# TODO — Task 6e56bc2e (نیاز به تکمیل دستی)

> **بررسی دکمه افزودن مشتری و تست‌های E2E**

## 🔎 خلاصه وضعیت

- **task_id**: `6e56bc2e-603c-46ff-981c-e25391ccecc6`
- **repo**: `mahdighandi1989/ALLIN1`
- **verification_status**: `partial`
- **archived_reason**: `max_retries` — Claude به سقف retry رسید بدون اینکه verify=done شود
- **retries_done**: 3
- **verifier confidence**: 0.95
- **verifier model**: `—`
- **report_id**: `f74edf31-2576-4c3a-b09b-586c7ff93889`
- **created_at**: 2026-06-05T01:54:28.417486+00:00

## 🚧 چه چیزی باقی مانده (مهم‌ترین بخش)

- [ ] AC3: تست E2E واقعی (Playwright/Cypress) برای کلیک و تأیید رفتار اضافه نشده

## 👉 قدم‌های بعدی پیشنهادی (از verifier)

1. افزودن تست Playwright/Cypress که روی دکمه Add Customer کلیک و بازشدن فرم را تأیید کند

## ✅ چه چیزی Claude انجام داد

- [x] AC1: git blame انجام و علت false positive (JSX چندخطی) مشخص شد
- [x] AC2: حالت (a) تأیید شد — handler دکمه موجود و کار می‌کند
- [x] دکمه Add Customer دارای onClick handler کامل است (خط 131 page.tsx)
- [x] تست‌های interaction (Jest) برای دکمه افزودن مشتری اضافه شده

## 📝 خلاصهٔ verifier

دو AC اول (git blame و تعیین حالت handler) به‌طور کامل انجام شده. دکمه Add Customer در page.tsx دارای onClick handler صحیح است. تست‌های Jest برای interaction اضافه شده، اما AC سوم که تست E2E واقعی (Playwright/Cypress) می‌خواهد برآورده نشده — تست‌های موجود Jest-based هستند نه browser-based E2E.

## 📋 Acceptance Criteria (مرجع کامل)

این لیست معیار done شدن تسک است — هر آیتمی که هنوز satisfy نیست
باید توسط انسان تکمیل شود.

- git blame مشخص می‌کند چرا این دکمه `{ setEditingCustomer(null); setShowForm(true) }}
          className="flex items` فاقد handler است
- یکی از این سه حالت تعیین شده: (a) handler restore شده + کار می‌کند، (b) دکمه حذف شده، (c) به‌صورت decorative علامت‌گذاری شده
- اگر دکمه باقی ماند، تست end-to-end (Playwright یا cypress) برای کلیک و تأیید رفتار اضافه شده

## 🔬 Evidence که verifier پیدا کرد

**Commits:**
- `59d7369`
- `31d3c3b`
- `a1065b6`

**Files lams شده:**
- `frontend/src/app/customers/page.tsx`
- `tests/test_customers_buttons_wired.py`
- `frontend/jest.config.js`

## 💡 ایدهٔ اصلی تسک

## 📋 شرح
یک دکمه/کنترل UI در فایل `frontend/src/app/customers/page.tsx` پیدا شد که هیچ event handler معنادار به آن متصل نیست (onClick، onChange، form submit، router push، یا API call شناسایی نشد).

## 🔍 جزئیات
- label/متن دکمه: `{ setEditingCustomer(null); setShowForm(true) }}
          className="flex items`
- فایل: `frontend/src/app/customers/page.tsx`
- علت تشخیص stale_detector: button has no onClick handler

## 🤔 چرا مهم است
دکمه بدون handler از دید کاربر کار نمی‌کند و دو حالت دارد:
  ۱) **dead UI**: دکمه از قبل کار می‌کرده و در refactor شکست خورده (regression) — باید handler بازگردانده شود.
  ۲) **forgotten option**: دکمه placeholder بوده و هرگز پیاده‌سازی نشده — باید یا حذف شود یا پیاده‌سازی کامل شود.
  ۳) **decorative**: فقط نمایشی است — باید با `aria-disabled` یا `role="presentation"` علامت شود.
---
[scan #2 at 2026-05-17T16:07:03.246767+00:00]
## 📋 شرح
یک دکمه/کنترل UI در فایل `frontend/src/app/customers/page.tsx` پیدا شد که هیچ event handler معنادار به آن متصل نیست (onClick، onChange، form submit، router push، یا API call شناسایی نشد).

## 🔍 جزئیات
- label/متن دکمه: `{ setEditingCustomer(customer); setShowForm(true) }}
                  
---
[scan #3 at 2026-05-17T16:07:03.262656+00:00]
## 📋 شرح
یک دکمه/کنترل UI در فایل `frontend/src/app/customers/page.tsx` پیدا شد که هیچ event handler معنادار به آن متصل نیست (onClick، onChange، form submit، router push، یا API call شناسایی نشد).

## 🔍 جزئیات
- label/متن دکمه: `handleDelete(customer)}
                        classNa

## 📜 پرامپت اصلی (excerpt)

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

---


## 🎯 هدف (خلاصه ساختاریافته)
دکمه‌ی UI بدون handler: { setEditingCustomer(null); setShowForm(true) }}
          className="flex items

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/customers/page.tsx`

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi, nextjs.

## 🌐 نقشهٔ وابستگی‌ها
این مورد در پایپ‌لاین کدبیس به فایل‌های اطراف وابسته است؛ قبل از تغییر، grep روی نام symbol/path اصلی انجام شود.

## 🔍 Context و وضعیت فعلی
## 📋 شرح
یک دکمه/کنترل

_[truncated — full prompt در پنل]_
```

---

_این فایل توسط Claude Auto-Runner تولید شده است. تسک با حالت_ `max_retries` _آرشیو شده و دیگر به‌صورت خودکار pickup نمی‌شود._