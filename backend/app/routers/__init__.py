"""API Routers"""
from app.routers.auth import router as auth_router
from app.routers.customers import router as customers_router
from app.routers.facilities import router as facilities_router
from app.routers.stats import router as stats_router
from app.routers.offer_letters import router as offer_letters_router
from app.routers.reports import router as reports_router

__all__ = [
    "auth_router",
    "customers_router",
    "facilities_router",
    "stats_router",
    "offer_letters_router",
    "reports_router",
]
