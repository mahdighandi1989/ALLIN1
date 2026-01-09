"""
API Package
تمام روت‌های API
"""
from fastapi import APIRouter

from app.api.v1 import auth, customers, facilities, checklists, settings, ai, personal

api_router = APIRouter()

# نسخه 1 API
api_router.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
api_router.include_router(customers.router, prefix="/v1/customers", tags=["Customers"])
api_router.include_router(facilities.router, prefix="/v1/facilities", tags=["Facilities"])
api_router.include_router(checklists.router, prefix="/v1/checklists", tags=["Checklists"])
api_router.include_router(settings.router, prefix="/v1/settings", tags=["Settings"])
api_router.include_router(ai.router, prefix="/v1/ai", tags=["AI"])
api_router.include_router(personal.router, prefix="/v1/personal", tags=["Personal"])
