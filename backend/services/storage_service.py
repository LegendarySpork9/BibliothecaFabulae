# Load libraries
import logging
import os
import shutil

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.settings import Settings

logger = logging.getLogger(__name__)

SUBDIRECTORIES = ["fics_html", "fics_epub", "audio", "database"]
LOW_STORAGE_THRESHOLD = 0.10


# Calculates the total size in bytes of a directory tree
def _dir_size(path: str) -> int:
    total = 0

    for dirpath, _dirnames, filenames in os.walk(path):
        for filename in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, filename))

            except OSError:
                pass

    return total


# Returns disk usage and per-subdirectory size breakdown
async def get_storage_info(db: AsyncSession) -> dict:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None or not settings_row.storage_path:
        raise ValueError("Storage path not configured")

    storage_path = settings_row.storage_path

    if not os.path.isdir(storage_path):
        raise ValueError(f"Storage path does not exist: {storage_path}")

    disk_usage = shutil.disk_usage(storage_path)

    breakdown = {}
    known_dirs = set()

    for subdir in SUBDIRECTORIES:
        known_dirs.add(subdir)
        subdir_path = os.path.join(storage_path, subdir)
        breakdown[subdir] = _dir_size(subdir_path) if os.path.isdir(subdir_path) else 0

    other_size = 0

    for entry in os.scandir(storage_path):
        try:
            if entry.is_file():
                other_size += entry.stat().st_size

            elif entry.is_dir() and entry.name not in known_dirs:
                other_size += _dir_size(entry.path)

        except OSError:
            pass

    breakdown["other"] = other_size

    storage_used = sum(breakdown.values())

    return {
        "storage_path": storage_path,
        "disk_total_bytes": disk_usage.total,
        "disk_used_bytes": disk_usage.used,
        "disk_free_bytes": disk_usage.free,
        "storage_used_bytes": storage_used,
        "breakdown": breakdown,
    }


# Returns warnings when available disk space falls below the threshold
async def get_storage_warnings(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None or not settings_row.storage_path:
        return []

    storage_path = settings_row.storage_path

    if not os.path.isdir(storage_path):
        return [{"level": "error", "message": f"Storage path does not exist: {storage_path}"}]

    disk_usage = shutil.disk_usage(storage_path)
    warnings = []

    free_ratio = disk_usage.free / disk_usage.total if disk_usage.total > 0 else 0

    if free_ratio < LOW_STORAGE_THRESHOLD:
        free_pct = round(free_ratio * 100, 1)
        free_gb = round(disk_usage.free / (1024 ** 3), 2)
        warnings.append({
            "level": "warning",
            "message": (
                f"Disk space is low: {free_pct}% free ({free_gb} GB remaining)"
            ),
        })

    storage_info = await get_storage_info(db)
    archive_used = storage_info["storage_used_bytes"]
    archive_available = disk_usage.free + archive_used

    if archive_available > 0:
        archive_usage_ratio = archive_used / archive_available

        if archive_usage_ratio > (1 - LOW_STORAGE_THRESHOLD):
            used_gb = round(archive_used / (1024 ** 3), 2)
            available_gb = round(disk_usage.free / (1024 ** 3), 2)
            warnings.append({
                "level": "warning",
                "message": (
                    f"Archive storage is filling up: {used_gb} GB used, {available_gb} GB remaining"
                ),
            })

    return warnings
