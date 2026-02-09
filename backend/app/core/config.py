import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Import the single source of truth for settings
from backend.app.core.config import Settings

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url=settings.docs_url if not settings.is_production() else None,
    redoc_url=settings.redoc_url if not settings.is_production() else None,
    openapi_url=settings.openapi_url if not settings.is_production() else None,
)

# --- Middlewares ---
# Set up CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=settings.cors_max_age,
)


# --- API Routers ---
# Here you would include your API routers
# from backend.app.api.v1 import users, customers, facilities
# app.include_router(users.router, prefix=settings.api_prefix, tags=["Users"])
# app.include_router(customers.router, prefix=settings.api_prefix, tags=["Customers"])
# app.include_router(facilities.router, prefix=settings.api_prefix, tags=["Facilities"])

# For demonstration, let's create a dummy dashboard endpoint that was failing
@app.get("/api/dashboard")
async def get_dashboard_data():
    """
    Provides summary data for the main dashboard.
    NOTE: This is mock data. Replace with actual database queries.
    """
    # In a real application, you would fetch this from the database
    return {
        "total_customers": 125,
        "active_customers": 120,
        "total_facilities": 50,
        "expiring_soon_count": 5,
        "total_exposure": {
            "amount": 1500000.75,
            "currency": "AED"
        },
        "outstanding_amount": {
            "amount": 750000.50,
            "currency": "AED"
        },
        "recent_customers": [
            {"id": 1, "name": "Global Exports Inc.", "account_number": "AE123456789"},
            {"id": 2, "name": "Tech Innovators LLC", "account_number": "AE987654321"},
        ]
    }

# --- Exception Handlers ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# --- Static Files Mounting ---
# This serves the built Next.js frontend
# It must be placed AFTER all API routes
static_files_path = Path(__file__).parent.parent / "static"
app.mount("/", StaticFiles(directory=static_files_path, html=True), name="static")


# --- Lifespan Events (for startup and shutdown) ---
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Banking Operations API...")
    # Here you can initialize database connections, etc.
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"CORS Origins: {settings.get_cors_origins_list()}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Banking Operations API...")
    # Here you can close database connections, etc.