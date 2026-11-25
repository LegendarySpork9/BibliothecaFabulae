# Load libraries
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings as app_settings
from backend.core.encryption import decrypt, encrypt
from backend.models.source import Source

logger = logging.getLogger(__name__)

SUPPORTED_SITES = {
    "ao3": {
        "label": "Archive of Our Own",
        "auth_types": ["credentials", "cookies"],
        "config_fields": None,
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 6000, "max_pages": 20},
    },
    "ffnet": {
        "label": "FanFiction.Net",
        "auth_types": ["cookies", "none"],
        "config_fields": {"profile_url": "Your FFNet profile URL (e.g. https://www.fanfiction.net/u/123/Name)"},
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 5000, "max_pages": 10},
    },
    "wattpad": {
        "label": "Wattpad",
        "auth_types": ["cookies", "none"],
        "config_fields": None,
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 1000, "max_pages": 20},
    },
    "royalroad": {
        "label": "Royal Road",
        "auth_types": ["cookies", "none"],
        "config_fields": {"readlist_url": "Your Read Later URL (e.g. https://www.royalroad.com/my/readlater)"},
        "needs_flaresolverr": False,
        "default_rate_limit": {"delay_ms": 1000, "max_pages": 20},
    },
    "spacebattles": {
        "label": "SpaceBattles",
        "auth_types": ["cookies", "none"],
        "config_fields": {"watched_url": "Your watched threads URL (e.g. https://forums.spacebattles.com/watched/threads)"},
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 2000, "max_pages": 10},
    },
    "sufficientvelocity": {
        "label": "Sufficient Velocity",
        "auth_types": ["cookies", "none"],
        "config_fields": {"watched_url": "Your watched threads URL (e.g. https://forums.sufficientvelocity.com/watched/threads)"},
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 2000, "max_pages": 10},
    },
    "scribblehub": {
        "label": "Scribble Hub",
        "auth_types": ["cookies", "none"],
        "config_fields": None,
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 1500, "max_pages": 15},
    },
    "fimfiction": {
        "label": "Fimfiction",
        "auth_types": ["cookies", "none"],
        "config_fields": {"bookshelf_url": "Your bookshelf URL (e.g. https://www.fimfiction.net/bookshelf/123/name)"},
        "needs_flaresolverr": True,
        "default_rate_limit": {"delay_ms": 1000, "max_pages": 20},
    },
    "quotev": {
        "label": "Quotev",
        "auth_types": ["cookies", "none"],
        "config_fields": None,
        "needs_flaresolverr": False,
        "default_rate_limit": {"delay_ms": 1500, "max_pages": 10},
    },
    "ficwad": {
        "label": "FicWad",
        "auth_types": ["credentials", "none"],
        "config_fields": None,
        "needs_flaresolverr": False,
        "default_rate_limit": {"delay_ms": 2000, "max_pages": 10},
    },
    "adultfanfiction": {
        "label": "Adult-FanFiction.org",
        "auth_types": ["none"],
        "config_fields": None,
        "needs_flaresolverr": False,
        "default_rate_limit": {"delay_ms": 2000, "max_pages": 10},
    },
}


# Converts a Source model to a JSON-serializable dictionary
def _source_to_dict(source: Source) -> dict:
    site_info = SUPPORTED_SITES.get(source.site_key, {})

    return {
        "id": source.id,
        "site_key": source.site_key,
        "label": site_info.get("label", source.site_key),
        "is_enabled": source.is_enabled,
        "auth_type": source.auth_type,
        "auth_configured": source.auth_data_encrypted is not None,
        "auth_status": source.auth_status,
        "auth_last_checked": source.auth_last_checked.isoformat() if source.auth_last_checked else None,
        "config_configured": source.config_data_encrypted is not None,
        "config_fields": site_info.get("config_fields"),
        "sync_interval_bookmarks": source.sync_interval_bookmarks,
        "sync_interval_updates": source.sync_interval_updates,
        "rate_limit_config": json.loads(source.rate_limit_config) if source.rate_limit_config else None,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


# Returns the list of all site keys that the application supports
def get_supported_sites() -> list[dict]:
    return [
        {"site_key": key, **value}
        for key, value in SUPPORTED_SITES.items()
    ]


# Returns all configured source sites
async def get_sources(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Source).order_by(Source.site_key))
    sources = result.scalars().all()

    return [_source_to_dict(s) for s in sources]


# Returns a single source by ID
async def get_source(db: AsyncSession, source_id: int) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    return _source_to_dict(source)


# Creates a new source configuration
async def create_source(
    db: AsyncSession,
    site_key: str,
    auth_type: str = "none",
    auth_data: str | None = None,
    config_data: str | None = None,
    sync_interval_bookmarks: str | None = None,
    sync_interval_updates: str | None = None,
    rate_limit_config: dict | None = None,
) -> dict:
    if site_key not in SUPPORTED_SITES:
        raise ValueError(f"Unsupported site: {site_key}")

    site_info = SUPPORTED_SITES[site_key]

    if auth_type not in site_info["auth_types"]:
        raise ValueError(
            f"Auth type '{auth_type}' not supported for {site_key}. "
            f"Supported: {site_info['auth_types']}"
        )

    existing = await db.execute(select(Source).where(Source.site_key == site_key))

    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Source already configured: {site_key}")

    encrypted_auth = None
    encrypted_config = None
    auth_status = "unknown"

    if auth_data:
        encrypted_auth = encrypt(auth_data, app_settings.ENCRYPTION_KEY)
        auth_status = "unknown"

    elif auth_type == "none":
        auth_status = "valid"

    if config_data:
        encrypted_config = encrypt(config_data, app_settings.ENCRYPTION_KEY)

    rl_config = rate_limit_config or site_info["default_rate_limit"]

    source = Source(
        site_key=site_key,
        auth_type=auth_type,
        auth_data_encrypted=encrypted_auth,
        auth_status=auth_status,
        config_data_encrypted=encrypted_config,
        sync_interval_bookmarks=sync_interval_bookmarks or "0 2 * * *",
        sync_interval_updates=sync_interval_updates or "0 3 * * *",
        rate_limit_config=json.dumps(rl_config),
    )
    db.add(source)
    await db.flush()

    return _source_to_dict(source)


# Updates a source's non-auth configuration
async def update_source(
    db: AsyncSession,
    source_id: int,
    is_enabled: bool | None = None,
    sync_interval_bookmarks: str | None = None,
    sync_interval_updates: str | None = None,
    rate_limit_config: dict | None = None,
) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    if is_enabled is not None:
        source.is_enabled = is_enabled

    if sync_interval_bookmarks is not None:
        source.sync_interval_bookmarks = sync_interval_bookmarks

    if sync_interval_updates is not None:
        source.sync_interval_updates = sync_interval_updates

    if rate_limit_config is not None:
        source.rate_limit_config = json.dumps(rate_limit_config)

    await db.flush()
    await db.refresh(source)

    return _source_to_dict(source)


# Updates a source's authentication credentials
async def update_source_auth(
    db: AsyncSession,
    source_id: int,
    auth_type: str,
    auth_data: str | None = None,
) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    site_info = SUPPORTED_SITES.get(source.site_key, {})

    if auth_type != "none" and auth_type not in site_info.get("auth_types", []):
        raise ValueError(
            f"Auth type '{auth_type}' not supported for {source.site_key}"
        )

    source.auth_type = auth_type

    if auth_data:
        source.auth_data_encrypted = encrypt(auth_data, app_settings.ENCRYPTION_KEY)
        source.auth_status = "unknown"

    elif auth_type == "none":
        source.auth_data_encrypted = None
        source.auth_status = "valid"

    else:
        source.auth_data_encrypted = None
        source.auth_status = "unknown"

    await db.flush()
    await db.refresh(source)

    return _source_to_dict(source)


# Removes a source configuration
async def delete_source(db: AsyncSession, source_id: int) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    await db.delete(source)
    await db.flush()

    return {"success": True}


# Validates auth credentials by attempting a lightweight site-specific request
async def validate_source_auth(db: AsyncSession, source_id: int) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    if source.auth_type == "none":
        source.auth_status = "valid"

        from backend.core.utils import utcnow
        source.auth_last_checked = utcnow()
        await db.flush()
        await db.refresh(source)

        result = _source_to_dict(source)
        result["validation_message"] = "No authentication required for this source"

        return result

    if source.auth_data_encrypted is None:
        source.auth_status = "expired"

        from backend.core.utils import utcnow
        source.auth_last_checked = utcnow()
        await db.flush()
        await db.refresh(source)

        result = _source_to_dict(source)
        result["validation_message"] = "No credentials saved — click Auth to enter your username and password"

        return result

    auth_data = decrypt(
        source.auth_data_encrypted,
        app_settings.ENCRYPTION_KEY,
        app_settings.ENCRYPTION_KEY_PREVIOUS or None,
    )

    check = await _check_site_credentials(source.site_key, source.auth_type, auth_data)

    from backend.core.utils import utcnow
    source.auth_status = check["status"]
    source.auth_last_checked = utcnow()
    await db.flush()
    await db.refresh(source)

    result = _source_to_dict(source)
    result["validation_message"] = check.get("message")

    return result


# Validates credentials by using FanFicFare's own adapter login.
# This tests the actual auth flow the library will use during sync.
async def _check_site_credentials(site_key: str, auth_type: str, auth_data: str) -> dict:
    import asyncio

    try:
        return await asyncio.to_thread(
            _check_credentials_sync, site_key, auth_type, auth_data
        )

    except Exception as e:
        logger.error("Credential check failed for %s: %s: %s", site_key, type(e).__name__, e)

        return {"status": "unknown", "message": f"Validation error for {site_key}: {e}"}


# Synchronously checks credentials using FanFicFare adapters, dispatching AO3 to its own handler
def _check_credentials_sync(site_key: str, auth_type: str, auth_data: str) -> dict:
    if site_key == "ao3":
        return _check_ao3_credentials_sync(auth_type, auth_data)

    if auth_type == "cookies":
        return _check_cookies_format(site_key, auth_data)

    from fanficfare.adapters import getAdapter, getSiteExamples
    from fanficfare.configurable import Configuration
    from fanficfare import exceptions

    site_domain = _SITE_KEY_TO_DOMAIN.get(site_key)

    if not site_domain:
        return _check_generic_credentials(auth_type, auth_data)

    try:
        config = Configuration([site_domain], "EPUB", lightweight=True)
        example_url = None

        for domain, urls in getSiteExamples():
            if domain == site_domain:
                example_url = urls[0]
                break

        if not example_url:
            example_url = f"https://{site_domain}/works/1"

        adapter = getAdapter(config, example_url)

        if auth_type == "credentials":
            creds = json.loads(auth_data)
            adapter.username = creds.get("username", "")
            adapter.password = creds.get("password", "")

            if not adapter.username or not adapter.password:
                return {"status": "expired", "message": "Username and password are required"}

        elif auth_type == "cookies":
            if not auth_data or not auth_data.strip():
                return {"status": "expired", "message": "No cookies provided"}

            config.set(site_domain, "cookie", auth_data.strip())

        elif auth_type == "api_key":
            if not auth_data or not auth_data.strip():
                return {"status": "expired", "message": "No API key provided"}

            return {"status": "valid", "message": "API key format accepted — will be verified on first use"}

        else:
            return {"status": "unknown", "message": f"Unsupported auth type: {auth_type}"}

        result = adapter.performLogin(example_url, "")

        if result:
            return {"status": "valid", "message": "Login successful"}
        
        else:
            return {"status": "expired", "message": "Login failed — credentials were rejected"}

    except exceptions.FailedToLogin:
        return {"status": "expired", "message": "Invalid username or password"}

    except exceptions.FailedToDownload as e:
        err = str(e).lower()

        if "token_dispenser" in err or "403" in err or "cloudflare" in err:
            return {
                "status": "unknown",
                "message": f"{site_domain} is behind Cloudflare protection — credentials will be verified on first sync",
            }

        return {"status": "unknown", "message": f"Could not reach {site_domain}: {e}"}

    except json.JSONDecodeError:
        return {"status": "expired", "message": "Credentials must be valid JSON with username and password fields"}

    except Exception as e:
        logger.exception("FanFicFare login check failed for %s", site_key)

        return {"status": "unknown", "message": f"Validation error: {e}"}


# Validates AO3 credentials or cookies using the ao3 client library
def _check_ao3_credentials_sync(auth_type: str, auth_data: str) -> dict:
    from ao3 import AO3Client

    try:
        if auth_type == "credentials":
            creds = json.loads(auth_data)
            username = creds.get("username", "").strip()
            password = creds.get("password", "").strip()

            if not username or not password:
                return {"status": "expired", "message": "Username and password are required"}

            with AO3Client(timeout=30) as client:
                client.login(username, password)

            return {"status": "valid", "message": "Login successful"}

        elif auth_type == "cookies":
            if not auth_data or not auth_data.strip():
                return {"status": "expired", "message": "No cookies provided"}

            cookies = {}

            for pair in auth_data.split(";"):
                pair = pair.strip()

                if "=" in pair:
                    key, _, value = pair.partition("=")
                    cookies[key.strip()] = value.strip()

            with AO3Client(timeout=30, cookies=cookies) as client:
                user = client.user("me")
                _ = user.id

            return {"status": "valid", "message": "Cookies are valid — logged in"}

        return {"status": "unknown", "message": f"Unsupported auth type: {auth_type}"}

    except json.JSONDecodeError:
        return {"status": "expired", "message": "Credentials must be valid JSON"}

    except Exception as e:
        err = str(e).lower()

        if "authentication" in err or "login" in err or "password" in err:
            return {"status": "expired", "message": "Invalid username or password"}

        if "403" in err or "cloudflare" in err or "timeout" in err or "connect" in err:
            return {
                "status": "unknown",
                "message": "AO3 is unreachable — may be behind Cloudflare protection. Credentials will be verified on first sync.",
            }

        return {"status": "unknown", "message": f"Validation error: {e}"}


# Validates that cookies are in the correct name=value format
def _check_cookies_format(site_key: str, auth_data: str) -> dict:
    if not auth_data or not auth_data.strip():
        return {"status": "unknown", "message": "No cookies provided"}

    stripped = auth_data.strip()

    if "=" not in stripped:
        return {"status": "unknown", "message": "Invalid format — cookies should be in name=value format (e.g. cf_clearance=abc123)"}

    if len(stripped) < 10:
        return {"status": "unknown", "message": "Invalid format — cookie value seems too short"}

    site_label = SUPPORTED_SITES.get(site_key, {}).get("label", site_key)

    return {"status": "unknown", "message": f"Format valid — cookies will be verified on first {site_label} sync"}


# Validates credential format for sites without a dedicated checker
def _check_generic_credentials(auth_type: str, auth_data: str) -> dict:
    if not auth_data or not auth_data.strip():
        return {"status": "expired", "message": "No credentials provided"}

    if auth_type == "credentials":
        try:
            creds = json.loads(auth_data)

            if not isinstance(creds, dict):
                return {"status": "expired", "message": "Credentials must be a JSON object"}

            if not creds.get("username") and not creds.get("password"):
                return {"status": "expired", "message": "No username or password found"}

            return {"status": "valid", "message": "Credential format accepted — will be verified on first sync"}

        except json.JSONDecodeError:
            return {"status": "expired", "message": "Credentials are not valid JSON"}

    return {"status": "valid", "message": "Credential format accepted — will be verified on first sync"}


_SITE_KEY_TO_DOMAIN: dict[str, str] = {
    "ao3": "archiveofourown.org",
    "ffnet": "fanfiction.net",
    "wattpad": "www.wattpad.com",
    "royalroad": "www.royalroad.com",
    "spacebattles": "forums.spacebattles.com",
    "sufficientvelocity": "forums.sufficientvelocity.com",
    "scribblehub": "www.scribblehub.com",
    "fimfiction": "www.fimfiction.net",
    "quotev": "www.quotev.com",
    "ficwad": "ficwad.com",
    "adultfanfiction": "www.adult-fanfiction.org",
}


# Updates a source's config data (URLs, settings — not credentials)
async def update_source_config(
    db: AsyncSession,
    source_id: int,
    config_data: str,
) -> dict:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    source.config_data_encrypted = encrypt(config_data, app_settings.ENCRYPTION_KEY)
    await db.flush()
    await db.refresh(source)

    return _source_to_dict(source)


# Decrypts and returns config data for internal use
async def get_source_config_data(db: AsyncSession, source_id: int) -> str | None:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    if source.config_data_encrypted is None:
        return None

    return decrypt(
        source.config_data_encrypted,
        app_settings.ENCRYPTION_KEY,
        app_settings.ENCRYPTION_KEY_PREVIOUS or None,
    )


# Decrypts and returns auth data for internal use only
async def get_source_auth_data(db: AsyncSession, source_id: int) -> str | None:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    if source.auth_data_encrypted is None:
        return None

    return decrypt(
        source.auth_data_encrypted,
        app_settings.ENCRYPTION_KEY,
        app_settings.ENCRYPTION_KEY_PREVIOUS or None,
    )
