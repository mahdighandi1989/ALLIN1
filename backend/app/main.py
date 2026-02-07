from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, customers, facilities, stats

app = FastAPI(title="Banking Operations API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/")
async def root():
    return {"message": "Banking Operations API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}