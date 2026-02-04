"""
ALLIN1 Banking Operations API

A comprehensive banking operations management system providing APIs for:
- User authentication and authorization
- Customer management (retail, corporate, SME)
- Facility management (loans, overdrafts, LC, LG)
- Dashboard statistics and reporting

Version: 3.0.0
Author: ALLIN1 Development Team
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, customers_router, facilities_router, stats_router

# Get CORS origins from settings
cors_origins = settings.get_cors_origins()
print(f"CORS Origins configured: {cors_origins}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    
    Handles startup and shutdown events:
    - Database initialization on startup
    - Cleanup on shutdown
    """
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    await close_db()
    print("Shutdown complete")

def custom_openapi():
    """
    Custom OpenAPI schema with enhanced documentation
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="ALLIN1 Banking Operations API",
        version="3.0.0",
        description="""
# ALLIN1 Banking Operations Management System

A comprehensive RESTful API for managing banking operations including customer relationships, facility management, and operational reporting.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Secure password management
- Token refresh capabilities

### 👥 Customer Management
- Multi-type customer support (Retail, Corporate, SME)
- Complete customer lifecycle management
- Advanced search and filtering
- Soft delete with restore functionality

### 💳 Facility Management
- Multiple facility types (Loans, Overdrafts, LC, LG)
- Comprehensive facility tracking
- Status management and reporting
- Integration with customer data

### 📊 Dashboard & Analytics
- Real-time statistics
- Facility expiry tracking
- Customer analytics
- Performance metrics

## Security

All endpoints (except authentication) require valid JWT tokens. Include the token in the Authorization header: