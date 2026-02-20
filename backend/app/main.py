from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
from app.routers import auth, customers, facilities, stats
from app.config import settings  # Use unified config from app.config
from app.database import engine, Base, get_db

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database schema is correct
    try:
        async with engine.begin() as conn:
            # Step 1: Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables verified/created")

            # Step 2: Add missing columns to existing tables with raw SQL
            # create_all does NOT add columns to existing tables, so we must do it manually
            alter_statements = [
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS amount NUMERIC(15,2) NOT NULL DEFAULT 0",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS outstanding NUMERIC(15,2) DEFAULT 0",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'AED'",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS facility_type VARCHAR(20)",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS name VARCHAR(200)",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS start_date DATE",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS expiry_date DATE",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS interest_rate NUMERIC(5,2)",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS tenor_months VARCHAR(20)",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS notes VARCHAR(1000)",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS customer_id VARCHAR",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT now()",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
                "ALTER TABLE facilities ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS account_no VARCHAR(50)",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS name VARCHAR(200)",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS email VARCHAR(100)",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS phone VARCHAR(50)",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now()",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false",
            ]
            for stmt in alter_statements:
                try:
                    await conn.execute(text(stmt))
                except Exception as col_err:
                    logger.warning(f"Column alter skipped: {col_err}")
            logger.info("Database schema fully verified")
    except Exception as e:
        logger.error(f"Database startup error: {e}")
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS middleware - Use the method from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),  # Use configured origins
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,  # Use configured credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend output directory (Next.js export)
# Try multiple paths: direct path for dev, static_frontend for deployed builds
_backend_dir = os.path.dirname(os.path.dirname(__file__))
_candidate_paths = [
    os.path.join(_backend_dir, "static_frontend"),       # Copied by build.sh / render.yaml
    os.path.join(_backend_dir, "../frontend/out"),        # Direct path in dev
]
frontend_out_path = None
for _path in _candidate_paths:
    if os.path.exists(_path):
        frontend_out_path = _path
        break

if frontend_out_path and os.path.exists(frontend_out_path):
    # Serve _next/static files
    next_static_path = os.path.join(frontend_out_path, "_next/static")
    if os.path.exists(next_static_path):
        app.mount("/_next/static", StaticFiles(directory=next_static_path), name="next-static")

    # Serve other static files from out directory
    app.mount("/static", StaticFiles(directory=frontend_out_path), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    # Serve index.html from frontend out directory
    if frontend_out_path:
        index_path = os.path.join(frontend_out_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "Banking Operations API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/debug/db")
async def db_check(db: AsyncSession = Depends(get_db)):
    """Diagnostic endpoint to check database connectivity and table status."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        tables_result = await db.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        )
        tables = [row[0] for row in tables_result]

        return {
            "status": "connected",
            "tables": tables,
            "database_url_prefix": settings.DATABASE_URL[:30] + "...",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_url_prefix": settings.DATABASE_URL[:30] + "...",
        }

# Catch-all route for SPA routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # First check if it's an API route
    if full_path.startswith("api/"):
        return {"error": "API route not found"}

    if frontend_out_path:
        # Check if file exists in out directory
        file_path = os.path.join(frontend_out_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise serve index.html for SPA routing
        index_path = os.path.join(frontend_out_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

    return {"error": "Frontend not found"}