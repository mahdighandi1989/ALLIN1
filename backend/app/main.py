"""Banking Operations API - Main Entry Point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, customers_router, facilities_router, stats_router


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

# CORS - Allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://banking-ops-frontend.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


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
