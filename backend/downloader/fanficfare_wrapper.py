# Load libraries
import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_last_request_time: dict[str, float] = {}

RETRY_BACKOFFS = [6, 12, 24, 48]


# Holds the result of a fic download including EPUB path, metadata, and chapters
@dataclass
class DownloadResult:
    epub_path: str
    metadata: dict = field(default_factory=dict)
    chapters: list[dict] = field(default_factory=list)
    success: bool = True
    error: str | None = None


# Holds the result of a fic update including new chapters and whether changes were found
@dataclass
class UpdateResult:
    epub_path: str
    new_chapters: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    has_updates: bool = False
    success: bool = True
    error: str | None = None


# Enforces per-site rate limiting by sleeping if needed
async def _enforce_rate_limit(site_key: str, delay_ms: int) -> None:
    now = time.monotonic()
    last = _last_request_time.get(site_key, 0)
    elapsed_ms = (now - last) * 1000

    if elapsed_ms < delay_ms:
        wait_seconds = (delay_ms - elapsed_ms) / 1000
        await asyncio.sleep(wait_seconds)

    _last_request_time[site_key] = time.monotonic()


# Builds a temporary personal.ini file for FanFicFare configuration
def _build_personal_ini(
    output_dir: str,
    auth_data: str | None = None,
    auth_type: str = "none",
    delay_ms: int = 2000,
    site_key: str = "unknown",
) -> str:
    from backend.core.config import settings as app_settings
    from backend.services.source_service import SUPPORTED_SITES

    ini_path = os.path.join(output_dir, "personal.ini")
    lines = [
        "[defaults]",
        f"slow_down_sleep_time={delay_ms / 1000:.1f}",
        "is_adult=true",
        "max_request_retries=0",
    ]

    site_info = SUPPORTED_SITES.get(site_key, {})
    flaresolverr_url = app_settings.FLARESOLVERR_URL

    if site_info.get("needs_flaresolverr") and flaresolverr_url:
        from urllib.parse import urlparse

        parsed = urlparse(flaresolverr_url)
        lines.append("use_flaresolverr_proxy=true")
        lines.append(f"flaresolverr_proxy_address={parsed.hostname or 'localhost'}")
        lines.append(f"flaresolverr_proxy_port={parsed.port or 8191}")
        lines.append(f"flaresolverr_proxy_protocol={parsed.scheme or 'http'}")
        lines.append("flaresolverr_proxy_timeout=59000")
        lines.append("use_flaresolverr_session=true")
        lines[1] = "slow_down_sleep_time=0.5"

    if auth_data and auth_type == "credentials":
        import json

        try:
            creds = json.loads(auth_data)
            username = creds.get("username", "")
            password = creds.get("password", "")

            if username:
                lines.append(f"username={username}")

            if password:
                lines.append(f"password={password}")

        except (json.JSONDecodeError, AttributeError):
            pass

    elif auth_data and auth_type == "cookies":
        lines.append(f"cookie={auth_data}")
        lines.append("use_cloudscraper=true")

    with open(ini_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return ini_path


# Downloads a fanfiction work using FanFicFare CLI
async def download_fic(
    url: str,
    output_dir: str,
    site_key: str = "unknown",
    auth_data: str | None = None,
    auth_type: str = "none",
    delay_ms: int = 2000,
) -> DownloadResult:
    os.makedirs(output_dir, exist_ok=True)
    ini_path = _build_personal_ini(output_dir, auth_data=auth_data, auth_type=auth_type, delay_ms=delay_ms, site_key=site_key)

    from backend.core.config import settings as app_settings
    from backend.services.source_service import SUPPORTED_SITES

    site_info = SUPPORTED_SITES.get(site_key, {})
    uses_flaresolverr = site_info.get("needs_flaresolverr") and app_settings.FLARESOLVERR_URL
    process_timeout = None if uses_flaresolverr else 600

    try:
        for attempt in range(len(RETRY_BACKOFFS) + 1):
            await _enforce_rate_limit(site_key, delay_ms)

            process = await asyncio.create_subprocess_exec(
                "fanficfare",
                "--non-interactive",
                "--config", ini_path,
                "--json-meta-file",
                "--update-epub",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=output_dir,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=process_timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            combined = f"{stdout} {stderr}"

            if process.returncode != 0 and "429" in combined:
                if attempt < len(RETRY_BACKOFFS):
                    wait = RETRY_BACKOFFS[attempt]
                    logger.warning(
                        "Rate limited (429) downloading %s — backing off %ds (attempt %d/%d)",
                        url, wait, attempt + 1, len(RETRY_BACKOFFS),
                    )
                    await asyncio.sleep(wait)
                    continue

                return DownloadResult(
                    epub_path="",
                    success=False,
                    error=f"Rate limited by {site_key} after {len(RETRY_BACKOFFS)} retries (backed off 6s, 12s, 24s, 48s). Try again later.",
                )

            if process.returncode != 0:
                logger.error("FanFicFare failed for %s: %s", url, combined.strip())

                return DownloadResult(
                    epub_path="",
                    success=False,
                    error=f"FanFicFare returned exit code {process.returncode}: {(stderr or stdout).strip()}",
                )

            epub_path = _find_epub(output_dir)

            if not epub_path:
                return DownloadResult(
                    epub_path="",
                    success=False,
                    error="FanFicFare completed but no EPUB file was found",
                )

            from backend.downloader.metadata_extractor import (
                extract_chapters,
                extract_metadata,
                load_fff_json_metadata,
            )

            json_meta = load_fff_json_metadata(epub_path)
            metadata = json_meta if json_meta else extract_metadata(epub_path)
            chapters = extract_chapters(epub_path)

            return DownloadResult(
                epub_path=epub_path,
                metadata=metadata,
                chapters=chapters,
            )

    except asyncio.TimeoutError:
        return DownloadResult(
            epub_path="",
            success=False,
            error=f"FanFicFare timed out after {process_timeout or 'unknown'} seconds",
        )

    except Exception as e:
        logger.exception("FanFicFare error for %s", url)

        return DownloadResult(
            epub_path="",
            success=False,
            error=str(e),
        )

    finally:
        if os.path.exists(ini_path):
            os.remove(ini_path)


# Fetches metadata only without downloading the full content
async def get_story_metadata(
    url: str,
    site_key: str = "unknown",
    auth_data: str | None = None,
    auth_type: str = "none",
    delay_ms: int = 2000,
) -> dict:
    await _enforce_rate_limit(site_key, delay_ms)

    with tempfile.TemporaryDirectory() as tmpdir:
        ini_path = _build_personal_ini(tmpdir, auth_data=auth_data, auth_type=auth_type, delay_ms=delay_ms, site_key=site_key)

        try:
            process = await asyncio.create_subprocess_exec(
                "fanficfare",
                "--non-interactive",
                "--config", ini_path,
                "--json-meta",
                "--meta-only",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmpdir,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=120
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")

            if process.returncode != 0:
                return {"error": f"FanFicFare returned exit code {process.returncode}"}

            import json as _json

            try:
                return _json.loads(stdout)
            
            except _json.JSONDecodeError:
                return _parse_meta_output(stdout)

        except asyncio.TimeoutError:
            return {"error": "Metadata fetch timed out"}


# Updates an existing fic by passing the existing EPUB to FanFicFare
async def update_fic(
    url: str,
    existing_epub: str,
    output_dir: str,
    site_key: str = "unknown",
    auth_data: str | None = None,
    auth_type: str = "none",
    delay_ms: int = 2000,
) -> UpdateResult:
    os.makedirs(output_dir, exist_ok=True)
    ini_path = _build_personal_ini(output_dir, auth_data=auth_data, auth_type=auth_type, delay_ms=delay_ms, site_key=site_key)

    from backend.core.config import settings as app_settings
    from backend.services.source_service import SUPPORTED_SITES

    site_info = SUPPORTED_SITES.get(site_key, {})
    uses_flaresolverr = site_info.get("needs_flaresolverr") and app_settings.FLARESOLVERR_URL
    process_timeout = None if uses_flaresolverr else 600

    try:
        for attempt in range(len(RETRY_BACKOFFS) + 1):
            await _enforce_rate_limit(site_key, delay_ms)

            process = await asyncio.create_subprocess_exec(
                "fanficfare",
                "--non-interactive",
                "--config", ini_path,
                "--update-epub",
                existing_epub,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=output_dir,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=process_timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            combined = f"{stdout} {stderr}"

            if process.returncode != 0 and "429" in combined:
                if attempt < len(RETRY_BACKOFFS):
                    wait = RETRY_BACKOFFS[attempt]
                    logger.warning(
                        "Rate limited (429) updating %s — backing off %ds (attempt %d/%d)",
                        url, wait, attempt + 1, len(RETRY_BACKOFFS),
                    )
                    await asyncio.sleep(wait)
                    continue

                return UpdateResult(
                    epub_path=existing_epub,
                    success=False,
                    error=f"Rate limited by {site_key} after {len(RETRY_BACKOFFS)} retries. Try again later.",
                )

            if process.returncode != 0:
                return UpdateResult(
                    epub_path=existing_epub,
                    success=False,
                    error=f"FanFicFare returned exit code {process.returncode}: {(stderr or stdout).strip()}",
                )

            has_updates = "already contains" not in stdout.lower()
            epub_path = _find_epub(output_dir) or existing_epub

            from backend.downloader.metadata_extractor import extract_metadata, extract_chapters

            metadata = extract_metadata(epub_path)
            chapters = extract_chapters(epub_path)

            return UpdateResult(
                epub_path=epub_path,
                new_chapters=chapters,
                metadata=metadata,
                has_updates=has_updates,
            )

    except asyncio.TimeoutError:
        return UpdateResult(
            epub_path=existing_epub,
            success=False,
            error="FanFicFare update timed out after 300 seconds",
        )

    except Exception as e:
        logger.exception("FanFicFare update error for %s", url)

        return UpdateResult(
            epub_path=existing_epub,
            success=False,
            error=str(e),
        )

    finally:
        if os.path.exists(ini_path):
            os.remove(ini_path)


# Finds the first EPUB file in a directory
def _find_epub(directory: str) -> str | None:
    for entry in os.scandir(directory):
        if entry.is_file() and entry.name.endswith(".epub"):
            return entry.path

    return None


# Parses FanFicFare's --meta-only output into a dict
def _parse_meta_output(output: str) -> dict:
    metadata: dict = {}

    for line in output.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip().lower()] = value.strip()

    return metadata
