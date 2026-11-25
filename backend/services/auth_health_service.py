# Load libraries
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.utils import utcnow
from backend.models.source import Source
from backend.services.notification_service import create_notification

logger = logging.getLogger(__name__)


# Checks the authentication health for a single source
async def check_source_auth(db: AsyncSession, source_id: int) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    if source.auth_type == "none":
        source.auth_status = "valid"
        source.auth_last_checked = utcnow()
        await db.flush()

        return {"source_id": source_id, "auth_status": "valid"}

    if not source.auth_data_encrypted:
        source.auth_status = "expired"
        source.auth_last_checked = utcnow()
        await db.flush()

        await create_notification(
            db, type="auth_required",
            title=f"{source.site_key.upper()} Authentication Required",
            message=f"No credentials configured for {source.site_key}. Please update your auth settings.",
            severity="warning",
        )

        return {"source_id": source_id, "auth_status": "expired"}

    # TODO: Implement site-specific auth validation
    # For now, mark as valid if auth data exists
    source.auth_status = "valid"
    source.auth_last_checked = utcnow()
    await db.flush()

    return {"source_id": source_id, "auth_status": "valid"}


# Checks authentication health for all enabled sources
async def check_all_source_auth(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Source).where(Source.is_enabled == True)  # noqa: E712
    )
    sources = result.scalars().all()
    results = []

    for source in sources:
        try:
            check_result = await check_source_auth(db, source.id)
            results.append(check_result)

        except Exception:
            logger.exception("Auth health check failed for source %d", source.id)

    return results
