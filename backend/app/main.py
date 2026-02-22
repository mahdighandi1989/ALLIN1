from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import auth, customers, facilities, stats
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
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
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Ensure the static_frontend directory exists
static_frontend_dir = "static_frontend"
if not os.path.exists(static_frontend_dir):
    os.makedirs(static_frontend_dir, exist_ok=True)
    logger.info(f"Created directory: {static_frontend_dir}")

# Mount the static directory to serve the frontend.
# This must be the last thing added to the app so that it doesn't
# override the API routes.
app.mount("/", StaticFiles(directory=static_frontend_dir, html=True), name="static_frontend")
