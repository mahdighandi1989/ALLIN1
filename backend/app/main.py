"""
Banking Operations System - Main Application
سیستم مدیریت عملیات بانکی - نقطه ورود اصلی
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import structlog

from app.core.config import settings
from app.api import api_router
from app.services.file_service import file_service

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Banking Operations System", version=settings.APP_VERSION)

    # Initialize database
    try:
        from app.core.database import init_db
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning("Database initialization skipped", error=str(e))

    # Auto-import data from Excel files on startup
    try:
        from app.services.data_importer import auto_import_data
        await auto_import_data()
        logger.info("Data import completed")
    except Exception as e:
        logger.warning("Data import skipped", error=str(e))

    # Initialize file service
    await file_service.initialize()

    # Initialize Google Drive sync if enabled
    if settings.GOOGLE_DRIVE_ENABLED:
        try:
            from app.services.google_drive_service import drive_service, sync_manager
            await drive_service.initialize()
            await sync_manager.start()
            logger.info("Google Drive sync initialized")
        except Exception as e:
            logger.warning("Google Drive sync not available", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down Banking Operations System")

    # Stop Google Drive sync
    if settings.GOOGLE_DRIVE_ENABLED:
        try:
            from app.services.google_drive_service import sync_manager
            await sync_manager.stop()
        except Exception:
            pass


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Banking Operations System API

    سیستم جامع مدیریت عملیات بانکی

    ### Features:
    - **Customer Management**: مدیریت مشتریان و پروفایل جامع
    - **Facility Management**: مدیریت تسهیلات و ضامن‌ها
    - **Checklist System**: سیستم چک‌لیست و تسک
    - **AI Integration**: یکپارچه‌سازی با هوش مصنوعی
    - **Google Drive Sync**: همگام‌سازی با گوگل درایو
    - **Personal Panel**: پنل شخصی کاربران

    ### Authentication:
    Use JWT Bearer token for authentication.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
# Build allowed origins list
cors_origins = []
for host in settings.ALLOWED_HOSTS:
    if host == "*":
        # When * is specified, add common frontend origins
        cors_origins.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "https://banking-ops-frontend.onrender.com",
            "https://banking-ops-frontend-*.onrender.com",
        ])
    else:
        cors_origins.append(host)

# Remove duplicates
cors_origins = list(set(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",  # Allow all onrender.com subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )

    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include API router
app.include_router(api_router, prefix="/api")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "api": "/api/v1"
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1
    )
