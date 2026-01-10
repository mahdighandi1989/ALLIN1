"""
API Package
تمام روت‌های API
"""
from fastapi import APIRouter

from app.api.v1 import auth, customers, facilities, checklists, settings, ai, personal, ai_providers, properties, profile, tasks, securities, data_import, google_drive

api_router = APIRouter()

# نسخه 1 API
api_router.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
api_router.include_router(customers.router, prefix="/v1/customers", tags=["Customers"])
api_router.include_router(facilities.router, prefix="/v1/facilities", tags=["Facilities"])
api_router.include_router(checklists.router, prefix="/v1/checklists", tags=["Checklists"])
api_router.include_router(settings.router, prefix="/v1/settings", tags=["Settings"])
api_router.include_router(ai.router, prefix="/v1/ai", tags=["AI"])
api_router.include_router(personal.router, prefix="/v1/personal", tags=["Personal"])
api_router.include_router(ai_providers.router, prefix="/v1/ai-providers", tags=["AI Providers"])
api_router.include_router(properties.router, prefix="/v1/properties", tags=["Properties"])
api_router.include_router(profile.router, prefix="/v1/profile", tags=["Profile"])
api_router.include_router(tasks.router, prefix="/v1/tasks", tags=["Tasks"])
api_router.include_router(securities.router, prefix="/v1/securities", tags=["Securities"])
api_router.include_router(data_import.router, prefix="/v1/data-import", tags=["Data Import"])
api_router.include_router(google_drive.router, prefix="/v1/google-drive", tags=["Google Drive"])
