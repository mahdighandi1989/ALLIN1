"""Banking Operations API - Main Entry Point"""
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, customers_router, facilities_router, stats_router


# Get CORS origins from settings
cors_origins = settings.get_cors_origins()
print(f"CORS Origins configured: {cors_origins}")

# Frontend static files directory (relative to backend directory)
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "out"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    await init_db()
    print("Database initialized")

    # Check if frontend is available
    if FRONTEND_DIR.exists():
        print(f"Frontend static files found at: {FRONTEND_DIR}")
    else:
        print(f"Frontend static files not found at: {FRONTEND_DIR}")
        print("Frontend will not be served. Build the frontend first.")

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


# Include API routers
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(facilities_router)
app.include_router(stats_router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount frontend static files if available
if FRONTEND_DIR.exists():
    # Mount _next directory for Next.js static assets
    next_static = FRONTEND_DIR / "_next"
    if next_static.exists():
        app.mount("/_next", StaticFiles(directory=str(next_static)), name="next-static")

    # Serve index.html for root
    @app.get("/")
    async def serve_frontend_root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file), media_type="text/html")
        return JSONResponse({"error": "Frontend not found"}, status_code=404)

    # Catch-all route for SPA - must be last
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Skip API paths
        if path.startswith("api/") or path in ["docs", "redoc", "openapi.json", "health"]:
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve the exact file first (for static assets)
        file_path = FRONTEND_DIR / path
        if file_path.is_file():
            # Determine media type based on extension
            suffix = file_path.suffix.lower()
            media_types = {
                ".html": "text/html",
                ".css": "text/css",
                ".js": "application/javascript",
                ".json": "application/json",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".woff": "font/woff",
                ".woff2": "font/woff2",
                ".ttf": "font/ttf",
            }
            media_type = media_types.get(suffix, "application/octet-stream")
            return FileResponse(str(file_path), media_type=media_type)

        # Try with .html extension (Next.js static export)
        html_path = FRONTEND_DIR / f"{path.rstrip('/')}.html"
        if html_path.is_file():
            return FileResponse(str(html_path), media_type="text/html")

        # Try index.html in directory (Next.js trailingSlash)
        index_path = FRONTEND_DIR / path.rstrip('/') / "index.html"
        if index_path.is_file():
            return FileResponse(str(index_path), media_type="text/html")

        # Fall back to main index.html for SPA routing
        main_index = FRONTEND_DIR / "index.html"
        if main_index.exists():
            return FileResponse(str(main_index), media_type="text/html")

        raise HTTPException(status_code=404, detail="Not found")

else:
    # No frontend - serve API info at root
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "3.0.0",
            "status": "running",
            "docs": "/docs"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
