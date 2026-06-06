# Feature Backlog — فیچرهای برنامه‌ریزی‌شده اما پیاده‌نشده

این فایل فیچرهایی را فهرست می‌کند که پیش‌تر در `README.md` به‌عنوان قابلیت
معرفی شده بودند اما در کد (مدل‌ها، روت‌ها، سرویس‌ها، فرانت‌اند) **پیاده‌سازی
نشده‌اند**. برای جلوگیری از عدم تطابق مستندات و کد، از `README.md` حذف و به
این backlog منتقل شدند. برای هر مورد یک GitHub issue نیز ایجاد می‌شود
(label: `feature-backlog`).

| # | فیچر | وضعیت فعلی در کد | Issue | توضیح |
|---|------|------------------|-------|-------|
| 1 | **Checklist System** | موجود نیست | [#140](https://github.com/mahdighandi1989/ALLIN1/issues/140) | هیچ مدل/روت/سرویس/UI با مفهوم checklist یا task یافت نشد. |
| 2 | **Guarantor Management** | موجود نیست | [#141](https://github.com/mahdighandi1989/ALLIN1/issues/141) | مدیریت ضامن‌ها و چک‌های ضمانت پیاده‌سازی نشده است. |
| 3 | **Property & Deposit Tracking** | موجود نیست | [#142](https://github.com/mahdighandi1989/ALLIN1/issues/142) | تنها ارجاع‌های `property`/`deposit` در کد، اتفاقی‌اند (مثل `@property` پایتون و فیلدهای دیگر)؛ فیچر پیگیری املاک و سپرده وجود ندارد. |
| 4 | **KYC Management** | موجود نیست | [#143](https://github.com/mahdighandi1989/ALLIN1/issues/143) | هیچ کد مرتبط با KYC یافت نشد. |
| 5 | **AI Integration (OpenAI, Claude, Gemini)** | موجود نیست | [#144](https://github.com/mahdighandi1989/ALLIN1/issues/144) | هیچ کتابخانهٔ AI (مانند `openai`، `anthropic`، `google-generativeai`) در `requirements.txt` نیست و کدی برای فراخوانی این سرویس‌ها وجود ندارد. |
| 6 | **Personal Notes Panel** | موجود نیست | [#145](https://github.com/mahdighandi1989/ALLIN1/issues/145) | فیلد `notes` روی مدل‌های customer/facility صرفاً یک فیلد متنی است؛ پنل یادداشت شخصیِ هر کاربر پیاده‌سازی نشده است. |
| 7 | **Email Notifications** | فقط config | [#146](https://github.com/mahdighandi1989/ALLIN1/issues/146) | تنظیمات `SMTP_*` در `config.py` تعریف شده‌اند اما هیچ کدِ ارسال ایمیل (`smtplib`/`send_email`/SMTP client) از آن‌ها استفاده نمی‌کند. اعلان‌های فعلی فقط in-app و Telegram (برای رویدادهای operator) هستند. |

## وضعیت فیچرهای پیاده‌سازی‌شدهٔ مرتبط (برای رفع ابهام)

- **Google Drive**: README پیش‌تر «Google Drive Sync (همگام‌سازی خودکار)» را
  ادعا می‌کرد؛ آنچه واقعاً پیاده شده **پشتیبان‌گیری (backup)** از طریق
  Google OAuth با scope `drive.file` است — نه sync دوطرفهٔ خودکار. در README
  به «Google Drive Backup» اصلاح شد.
- **Document Expiry Alerts**: آنچه پیاده شده، هشدار **انقضای تسهیلات
  (facility)** به‌صورت اعلان درون‌برنامه‌ای است (تسهیلاتِ نزدیک به انقضا در
  ۳۰ روز آینده)، نه «انقضای مدارک». در README به «Facility Expiry Alerts»
  اصلاح شد.

## وقتی یکی از این فیچرها پیاده‌سازی شد

1. مورد مربوطه را از این جدول حذف کن.
2. آن را به بخش `Features` در `README.md` اضافه کن.
3. GitHub issue مرتبط را ببند.

---

# Page Audit — صفحات ناقص، کارکرد و دسته‌بندی ناوبری

ممیزی (page audit) همهٔ مسیرهای فرانت‌اند (`frontend/src/app/*/page.tsx`) در پاسخ به
درخواست کاربر دربارهٔ «صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن».
هر صفحه با الگوی «صفحهٔ سالم» (`customers/page.tsx`) سنجیده شد: داشتن `Layout`،
بارگذاری داده از `@/lib/api`، spinner و empty-state، `data-testid` روی المان‌های کلیدی،
و اتصال به یک router فعال backend.

## دسته‌بندی منوی ناوبری (navigation grouping)

منوی تخت قبلی در `frontend/src/components/Layout.tsx` به گروه‌های عنوان‌دار بازسازی شد:

| گروه | صفحات |
| --- | --- |
| **Operations** | Dashboard, Customers, Facilities, Offer Letters |
| **Finance & Reports** | Reports, Import |
| **System** (admin) | Users, Audit Log, Settings, Recycle Bin |

صفحات detail (`/customer-detail`, `/facility-detail`) اکنون آیتم والد خود را در nav
highlight می‌کنند (`usePathname()`) و یک `Breadcrumb` بازگشت به فهرست والد دارند.

## وضعیت صفحات (page status)

| صفحه (route) | Router backend | وضعیت | توضیح |
| --- | --- | --- | --- |
| `/dashboard` | stats | ✅ کار می‌کند | کارت‌های KPI + نمودارها |
| `/customers` | customers | ✅ کار می‌کند | الگوی مرجع؛ حالا از `Button` مشترک استفاده می‌کند |
| `/customer-detail` | customers | ✅ کار می‌کند | breadcrumb افزوده شد |
| `/facilities` | facilities | ✅ کار می‌کند | الگوی مرجع |
| `/facility-detail` | facilities | ✅ کار می‌کند | breadcrumb افزوده شد |
| `/offer-letters` | offer_letters | ✅ کار می‌کند | فهرست + ساخت/پیش‌نمایش |
| `/reports` | reports | ✅ کار می‌کند | خروجی PDF/XLSX/CSV + snapshot |
| `/import` | imports | ✅ کار می‌کند | آپلود + pipeline پیش‌نمایش |
| `/trash` | trash | ✅ کار می‌کند | بازیابی رکوردهای حذف‌شده |
| `/users` | users | ✅ کار می‌کند | فقط admin؛ **خطای 500 فهرست رفع شد** |
| `/audit` | audit | ✅ کار می‌کند | جدول audit log |
| `/settings` | settings | ✅ کار می‌کند | تنظیمات برنامه |
| `/profile` | auth | ✅ کار می‌کند | پروفایل کاربر جاری |
| `/login` | auth + google_auth | ✅ کار می‌کند | بازطراحی‌شده: nav bar + «Sign in with Google» |

هیچ لینک منو به صفحهٔ ۴۰۴ (broken page) منتهی نمی‌شود — هر آیتم منو به یک
`page.tsx` واقعی متصل است که router فعال آن در `backend/app/main.py` ثبت شده.

## موارد رفع‌شدهٔ اخیر

- **`GET /api/users` خطای 500 می‌داد** — علت، schema drift در production بود
  (ستون‌های `auth_provider`/`google_sub`/`picture` در دیتابیس‌های قدیمی‌تر نبودند).
  self-heal در `backend/app/db_init.py` ستون‌های缺 را اضافه می‌کند و تست رگرسیون
  `backend/tests/integration/test_users.py::test_list_users_pagination` پاسخ 200
  صفحه‌بندی‌شده را قفل می‌کند.
- **ورود با Google** — `GET /api/auth/google/login` و `/callback` با اعتبارسنجی
  `state` (CSRF) پیاده شده و صفحهٔ login این گزینه را نمایش می‌دهد.
