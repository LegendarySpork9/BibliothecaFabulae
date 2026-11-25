# Load libraries
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings as app_settings
from backend.core.encryption import decrypt
from backend.models.source import Source
from backend.services.source_service import (
    create_source,
    delete_source,
    get_source,
    get_source_auth_data,
    get_sources,
    get_supported_sites,
    update_source,
    update_source_auth,
)


@pytest.mark.asyncio
async def test_get_supported_sites():
    sites = get_supported_sites()

    assert len(sites) > 0
    ao3 = next(s for s in sites if s["site_key"] == "ao3")
    assert ao3["label"] == "Archive of Our Own"
    assert "credentials" in ao3["auth_types"]


@pytest.mark.asyncio
async def test_create_source(db_session: AsyncSession):
    result = await create_source(
        db_session,
        site_key="ao3",
        auth_type="credentials",
        auth_data='{"username": "test", "password": "secret"}',
    )

    assert result["site_key"] == "ao3"
    assert result["label"] == "Archive of Our Own"
    assert result["auth_configured"] is True
    assert result["auth_status"] == "unknown"
    assert result["is_enabled"] is True
    assert result["rate_limit_config"] is not None


@pytest.mark.asyncio
async def test_create_source_unsupported_site(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Unsupported site"):
        await create_source(db_session, site_key="nonexistent")


@pytest.mark.asyncio
async def test_create_source_invalid_auth_type(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Auth type .* not supported"):
        await create_source(
            db_session, site_key="royalroad", auth_type="credentials",
        )


@pytest.mark.asyncio
async def test_create_source_duplicate(db_session: AsyncSession):
    await create_source(db_session, site_key="ao3", auth_type="credentials")

    with pytest.raises(ValueError, match="Source already configured"):
        await create_source(db_session, site_key="ao3", auth_type="credentials")


@pytest.mark.asyncio
async def test_create_source_no_auth(db_session: AsyncSession):
    result = await create_source(db_session, site_key="adultfanfiction", auth_type="none")

    assert result["auth_configured"] is False
    assert result["auth_status"] == "valid"


@pytest.mark.asyncio
async def test_get_sources_empty(db_session: AsyncSession):
    result = await get_sources(db_session)

    assert result == []


@pytest.mark.asyncio
async def test_get_sources_multiple(db_session: AsyncSession):
    await create_source(db_session, site_key="ao3", auth_type="credentials")
    await create_source(db_session, site_key="adultfanfiction", auth_type="none")

    result = await get_sources(db_session)

    assert len(result) == 2
    site_keys = [s["site_key"] for s in result]
    assert "ao3" in site_keys
    assert "adultfanfiction" in site_keys


@pytest.mark.asyncio
async def test_get_source_by_id(db_session: AsyncSession):
    created = await create_source(db_session, site_key="ao3", auth_type="credentials")
    result = await get_source(db_session, created["id"])

    assert result["site_key"] == "ao3"


@pytest.mark.asyncio
async def test_get_source_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Source not found"):
        await get_source(db_session, 9999)


@pytest.mark.asyncio
async def test_update_source(db_session: AsyncSession):
    created = await create_source(db_session, site_key="ao3", auth_type="credentials")

    updated = await update_source(
        db_session,
        created["id"],
        is_enabled=False,
        sync_interval_bookmarks="0 4 * * *",
        rate_limit_config={"delay_ms": 5000, "max_pages": 5},
    )

    assert updated["is_enabled"] is False
    assert updated["sync_interval_bookmarks"] == "0 4 * * *"
    assert updated["rate_limit_config"]["delay_ms"] == 5000


@pytest.mark.asyncio
async def test_update_source_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Source not found"):
        await update_source(db_session, 9999, is_enabled=False)


@pytest.mark.asyncio
async def test_update_source_auth(db_session: AsyncSession):
    created = await create_source(db_session, site_key="ao3", auth_type="credentials")

    updated = await update_source_auth(
        db_session,
        created["id"],
        auth_type="cookies",
        auth_data="session_cookie_value",
    )

    assert updated["auth_type"] == "cookies"
    assert updated["auth_configured"] is True
    assert updated["auth_status"] == "unknown"


@pytest.mark.asyncio
async def test_update_source_auth_to_none(db_session: AsyncSession):
    created = await create_source(
        db_session, site_key="ao3", auth_type="credentials",
        auth_data="secret",
    )

    updated = await update_source_auth(
        db_session, created["id"], auth_type="none",
    )

    assert updated["auth_configured"] is False
    assert updated["auth_status"] == "valid"


@pytest.mark.asyncio
async def test_update_source_auth_invalid_type(db_session: AsyncSession):
    created = await create_source(db_session, site_key="adultfanfiction", auth_type="none")

    with pytest.raises(ValueError, match="Auth type .* not supported"):
        await update_source_auth(
            db_session, created["id"], auth_type="credentials",
        )


@pytest.mark.asyncio
async def test_delete_source(db_session: AsyncSession):
    created = await create_source(db_session, site_key="ao3", auth_type="credentials")

    result = await delete_source(db_session, created["id"])
    assert result["success"] is True

    db_result = await db_session.execute(select(Source).where(Source.id == created["id"]))
    assert db_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_source_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Source not found"):
        await delete_source(db_session, 9999)


@pytest.mark.asyncio
async def test_get_source_auth_data_decrypts(db_session: AsyncSession):
    created = await create_source(
        db_session,
        site_key="ao3",
        auth_type="credentials",
        auth_data='{"username": "myuser", "password": "mypass"}',
    )

    decrypted = await get_source_auth_data(db_session, created["id"])

    assert decrypted == '{"username": "myuser", "password": "mypass"}'


@pytest.mark.asyncio
async def test_get_source_auth_data_none(db_session: AsyncSession):
    created = await create_source(db_session, site_key="adultfanfiction", auth_type="none")

    result = await get_source_auth_data(db_session, created["id"])

    assert result is None


@pytest.mark.asyncio
async def test_auth_data_is_encrypted_in_db(db_session: AsyncSession):
    await create_source(
        db_session,
        site_key="ao3",
        auth_type="credentials",
        auth_data="plain_secret",
    )

    result = await db_session.execute(select(Source).where(Source.site_key == "ao3"))
    source = result.scalar_one()

    assert source.auth_data_encrypted is not None
    assert source.auth_data_encrypted != "plain_secret"
    assert decrypt(source.auth_data_encrypted, app_settings.ENCRYPTION_KEY) == "plain_secret"
