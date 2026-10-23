from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def check_health(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """
    Check application and database health status.
    Distinguishes application responsiveness from active database connectivity.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    app_status = "ok" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=app_status,
        database=db_status,
        environment=settings.ENVIRONMENT,
        version="1.0.0",
    )
