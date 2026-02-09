from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.routers import auth, customers, facilities, stats
from app.config import settings  # Use unified config from app.config

app = FastAPI(title=settings.APP_NAME)

# CORS middleware - Use the method from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),  # Use configured origins
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,  # Use configured credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend output directory (Next.js export)
frontend_out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../frontend/out")

if os.path.exists(frontend_out_path):
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

@app.get("/")
async def root():
    # Serve index.html from frontend out directory
    index_path = os.path.join(frontend_out_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Banking Operations API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Catch-all route for SPA routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # First check if it's an API route
    if full_path.startswith("api/"):
        return {"error": "API route not found"}

    # Check if file exists in out directory
    file_path = os.path.join(frontend_out_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # Otherwise serve index.html for SPA routing
    index_path = os.path.join(frontend_out_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"error": "Frontend not found"}
