# Banking Operations System

سیستم جامع مدیریت عملیات بانکی - نسخه وب

## Overview

این پروژه تبدیل سیستم اکسل-محور مدیریت عملیات بانکی به یک وب اپلیکیشن حرفه‌ای و مقیاس‌پذیر است.

### Features

> فهرست زیر فقط فیچرهایی است که **در کد پیاده‌سازی شده‌اند**. فیچرهای
> برنامه‌ریزی‌شده اما هنوز پیاده‌نشده در [`FEATURE_BACKLOG.md`](FEATURE_BACKLOG.md)
> نگه‌داری می‌شوند.

- **Customer Management** - مدیریت مشتریان با پروفایل 290+ فیلد
- **Facility Management** - مدیریت تسهیلات (OD, Loan, LG, LC, ...) به‌همراه
  محاسبهٔ اقساط (amortization) و authorization
- **Offer Letter Management** - مدیریت و صدور نامه‌های پیشنهاد تسهیلات
- **FX / Exchange Rate Tracking** - نرخ ارز و محاسبهٔ exposure
- **Excel Import** - ورود داده از فایل‌های اکسل
- **Reports & Statistics** - گزارش‌ها و داشبورد آماری
- **Google Drive Backup** - پشتیبان‌گیری در گوگل درایو از طریق OAuth
  (scope `drive.file`)
- **In-app Notifications** - اعلان‌های درون‌برنامه‌ای (زنگولهٔ UI)
- **Facility Expiry Alerts** - هشدار درون‌برنامه‌ای برای تسهیلاتِ نزدیک به انقضا
- **Telegram Integration (two-way)** - اعلان‌های رویدادی به تلگرام با کنترل
  per-event در پنل (ارسال شود/نشود، با صدا/بی‌صدا)، منوی ثابت، و دستورهای دوطرفه
  (`/status`، `/stats`، `/expiring`، `/fx`، `/scan`، `/backup`، و پل به مدل‌های
  هوش مصنوعی با `/ai`). دسترسی با allow-list از `chat_id`ها و وب‌هوک محافظت‌شده با
  secret token. تنظیمات در `Settings → Telegram`.
- **Audit Log** - ثبت رویدادها و گزارش حسابرسی
- **Trash / Soft Delete** - حذف نرم و سطل بازیافت
- **Multi-user Support** - پشتیبانی چند کاربره با احراز هویت JWT و سطوح دسترسی

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT with refresh tokens
- **Integrations**: Google OAuth 2.0 (Drive backup)

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS
- **HTTP**: Axios
- **UI**: lucide-react icons, react-hot-toast / sonner notifications

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional)

### Backend Setup