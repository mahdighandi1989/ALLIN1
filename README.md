# Banking Operations System

سیستم جامع مدیریت عملیات بانکی - نسخه وب

## Overview

این پروژه تبدیل سیستم اکسل-محور مدیریت عملیات بانکی به یک وب اپلیکیشن حرفه‌ای و مقیاس‌پذیر است.

### Features

- **Customer Management** - مدیریت مشتریان با پروفایل 290+ فیلد
- **Facility Management** - مدیریت تسهیلات (OD, Loan, LG, LC, ...)
- **Checklist System** - سیستم چک‌لیست و تسک
- **Guarantor Management** - مدیریت ضامن‌ها و چک‌های ضمانت
- **Property & Deposit Tracking** - پیگیری املاک و سپرده‌ها
- **KYC Management** - مدیریت شناسایی مشتری
- **AI Integration** - یکپارچه‌سازی با OpenAI, Claude, Gemini
- **Google Drive Sync** - همگام‌سازی خودکار با گوگل درایو
- **Personal Notes Panel** - پنل یادداشت‌های شخصی هر کاربر
- **Multi-user Support** - پشتیبانی چند کاربره با سطوح دسترسی
- **Document Expiry Alerts** - هشدار انقضای مدارک
- **Email Notifications** - اعلان‌های ایمیلی

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT with refresh tokens
- **AI**: OpenAI, Anthropic, Google AI

### Frontend
- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **State**: Zustand + React Query
- **UI**: Radix UI primitives

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional)

### Backend Setup