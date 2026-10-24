from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.test_roles import router as test_roles_router
from app.api.v1.media import router as media_router
from app.api.v1.assessment import router as assessment_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(test_roles_router)
api_router.include_router(media_router)
api_router.include_router(assessment_router)

__all__ = ["api_router"]
