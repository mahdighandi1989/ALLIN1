"""API Routers"""
from app.routers.auth import router as auth_router
from app.routers.customers import router as customers_router
from app.routers.facilities import router as facilities_router
from app.routers.stats import router as stats_router
from app.routers.offer_letters import router as offer_letters_router
from app.routers.reports import router as reports_router
from app.routers.users import router as users_router
from app.routers.trash import router as trash_router
from app.routers.audit import router as audit_router
from app.routers.notifications import router as notifications_router
from app.routers.imports import router as imports_router

__all__ = [
    "auth_router",
    "customers_router",
    "facilities_router",
    "stats_router",
    "offer_letters_router",
    "reports_router",
    "users_router",
    "trash_router",
    "audit_router",
    "notifications_router",
    "imports_router",
]
