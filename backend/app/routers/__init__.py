"""API Routers"""
from app.routers.auth import router as auth_router
from app.routers.customers import router as customers_router
from app.routers.facilities import router as facilities_router
from app.routers.stats import router as stats_router

__all__ = ["auth_router", "customers_router", "facilities_router", "stats_router"]
