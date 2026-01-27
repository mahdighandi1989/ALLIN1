"""Banking Operations API - Main Entry Point"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

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
    """Application startup and shutdown"""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    await close_db()
    print("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow frontend origins (loaded from environment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


def get_cors_headers(request: Request) -> dict:
    """Get CORS headers based on request origin"""
    origin = request.headers.get("origin", "")
    if origin in cors_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    return {}


# HTTPException handler - preserve status code and add CORS headers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper status codes and CORS headers"""
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


# Global exception handler for unexpected errors only
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions - log the actual error for debugging"""
    logger.error(f"Unexpected error on {request.method} {request.url}: {type(exc).__name__}: {exc}")
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )


# Explicit OPTIONS handler for all API routes (ensures preflight works even during cold starts)
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle preflight CORS requests explicitly"""
    headers = get_cors_headers(request)
    return Response(status_code=200, headers=headers)


# Include routers
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(facilities_router)
app.include_router(stats_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
