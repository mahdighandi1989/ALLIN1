from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings, enforce_security_on_startup
from app.routers import auth, customers, facilities, stats
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast on insecure configuration (e.g. a lingering AUTH_DISABLED in
    # production) and log any security warnings before serving requests.
    enforce_security_on_startup()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=settings.CORS_MAX_AGE,
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# The static directory should contain the frontend build files.
static_dir = "static"

# Mount the static directory to serve the frontend.
# This must be the last thing added to the app so that it doesn't
# override the API routes.
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static_frontend")
    logger.info(f"Serving frontend from directory: {static_dir}")
else:
    logger.warning(f"Static directory '{static_dir}' not found. Frontend will not be served.")
