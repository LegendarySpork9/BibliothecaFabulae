# Load libraries
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.database import async_session
from backend.models.settings import Settings as SettingsModel

logger = logging.getLogger(__name__)

ALLOWED_PATHS = {"/api/health", "/api/setup", "/docs", "/openapi.json", "/redoc"}


# Block non-setup API requests when initial setup has not been completed
class SetupGuardMiddleware(BaseHTTPMiddleware):

    # Intercept requests and check setup status before forwarding
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        path = request.url.path

        if any(path == p or path.startswith(p + "/") for p in ALLOWED_PATHS):
            return await call_next(request)

        try:
            async with async_session() as session:
                from sqlalchemy import select

                result = await session.execute(
                    select(SettingsModel).where(SettingsModel.id == 1)
                )
                settings_row = result.scalar_one_or_none()

                if settings_row is None or not settings_row.setup_complete:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Setup not complete",
                            "setup_required": True,
                        },
                    )

        except Exception:
            logger.exception("Setup guard check failed")

        return await call_next(request)
