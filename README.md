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

## Project Structure

```
ALLIN1/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, security
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── main.py       # Entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── pages/        # Next.js pages
│   │   ├── services/     # API services
│   │   └── styles/       # CSS
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml           # Render deployment config
└── README.md
```

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd ALLIN1

# Start all services
docker-compose up -d

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Deployment on Render

1. Push code to GitHub
2. Connect Render to your GitHub repo
3. Use `render.yaml` blueprint for auto-configuration
4. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `SMTP_*` settings
   - `GOOGLE_*` for Drive integration

## API Documentation

When running locally, access Swagger UI at:
- http://localhost:8000/docs

## Default Credentials

- Username: `admin`
- Password: `admin123`

## Environment Variables

See `backend/.env.example` for all configuration options.

### Required

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT signing key

### Optional

- `OPENAI_API_KEY` - For OpenAI features
- `ANTHROPIC_API_KEY` - For Claude features
- `GOOGLE_AI_API_KEY` - For Gemini features
- `SMTP_*` - Email configuration
- `GOOGLE_DRIVE_*` - Google Drive sync

## License

Private - All rights reserved

## Original System

This web application is based on the Excel macro system documented in `SYSTEM_DOCUMENTATION_REPORT.md`.
