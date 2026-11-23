# Load libraries
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.settings import Settings as SettingsModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


# Check database connectivity and setup status
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_healthy = True

    except Exception:
        logger.exception("Health check: database connectivity failed")
        db_healthy = False

    setup_complete = False

    if db_healthy:
        try:
            result = await db.execute(select(SettingsModel).where(SettingsModel.id == 1))
            settings_row = result.scalar_one_or_none()

            if settings_row:
                setup_complete = settings_row.setup_complete

        except Exception:
            logger.exception("Health check: failed to read setup status")

    if not db_healthy:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": "1.0.0",
                "setup_complete": False,
            },
        )

    return {
        "status": "healthy",
        "version": "1.0.0",
        "setup_complete": setup_complete,
    }
