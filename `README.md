# Banking Operations System (ALLIN1)

A comprehensive banking operations management system built with FastAPI (backend) and Next.js (frontend). This system transforms traditional Excel-based banking operations into a modern, scalable web application.

## 🌟 Features

### Core Functionality
- **Customer Management**: Complete CRUD operations with advanced search and filtering
- **Facility Management**: Loan, overdraft, LC/LG facility tracking with expiry monitoring
- **Dashboard Analytics**: Real-time statistics and business insights
- **User Authentication**: Secure JWT-based authentication with role management
- **Audit Trail**: Comprehensive logging of all system operations
- **Data Export**: Export capabilities for reporting and compliance

### Advanced Features
- **Multi-currency Support**: Handle facilities in different currencies
- **Expiry Alerts**: Automatic notifications for expiring facilities
- **Advanced Search**: Complex filtering across all entities
- **Soft Delete**: Safe deletion with restore capabilities
- **Pagination**: Efficient handling of large datasets
- **Real-time Updates**: Live dashboard statistics

## 🏗️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.0**: Advanced ORM with async support
- **PostgreSQL**: Primary database with JSONB support
- **JWT**: Secure authentication tokens with refresh mechanism
- **Pydantic v2**: Data validation and serialization
- **Alembic**: Database migrations and version control
- **pytest**: Comprehensive testing framework
- **uvicorn**: ASGI server for production deployment

### Frontend
- **Next.js 14**: React framework with App Router and server components
- **TypeScript**: Type safety and enhanced developer experience
- **Tailwind CSS**: Utility-first CSS framework for responsive design
- **Axios**: HTTP client with interceptors and error handling
- **React Hot Toast**: User-friendly notifications
- **Lucide Icons**: Modern icon library

### Infrastructure
- **Docker**: Containerization for consistent deployments
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Reverse proxy and static file serving
- **PostgreSQL**: Production-ready database with backup strategies

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Docker & Docker Compose (optional)

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**: