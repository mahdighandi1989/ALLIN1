"""
Banking Operations System
سیستم عملیات بانکی - نسخه ۲.۰
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import structlog

from app.core.config import settings
from app.core.database import init_db, close_db

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("Starting Banking Operations System", version=settings.APP_VERSION)

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database initialization failed", error=str(e))

    # Initialize Google Drive
    try:
        from app.services.google_drive import drive_service
        await drive_service.initialize()
    except Exception as e:
        logger.warning("Google Drive not initialized", error=str(e))

    yield

    # Shutdown
    await close_db()
    logger.info("Application shutdown complete")


# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional Banking Operations Management System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow specific origins
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://banking-ops-frontend.onrender.com",
    "https://banking-ops.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Timing middleware
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response


# Error handler
@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    logger.error("Error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "Internal error"}
    )


# Include routers
from app.api.v1 import auth, customers, facilities, ai, settings as settings_api, reports

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(facilities.router, prefix="/api/v1/facilities", tags=["Facilities"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
