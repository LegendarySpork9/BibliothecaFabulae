# Load libraries
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.settings import Settings as SettingsModel
from backend.services.storage_service import (
    _dir_size,
    get_storage_info,
    get_storage_warnings,
)


# Test that get_storage_info returns all expected keys for a valid directory
@pytest.mark.asyncio
async def test_get_storage_info_valid_directory(db_session: AsyncSession, tmp_path):
    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path), setup_complete=True))
    await db_session.flush()

    result = await get_storage_info(db_session)

    assert result["storage_path"] == str(tmp_path)
    assert result["disk_total_bytes"] > 0
    assert result["disk_used_bytes"] >= 0
    assert result["disk_free_bytes"] > 0
    assert result["storage_used_bytes"] >= 0
    assert "breakdown" in result
    assert "fics_html" in result["breakdown"]
    assert "fics_epub" in result["breakdown"]
    assert "audio" in result["breakdown"]
    assert "database" in result["breakdown"]
    assert "other" in result["breakdown"]


# Test that get_storage_info calculates subdirectory sizes correctly
@pytest.mark.asyncio
async def test_get_storage_info_with_subdirectories(db_session: AsyncSession, tmp_path):
    # Create subdirectories with files
    fics_html = tmp_path / "fics_html"
    fics_html.mkdir()
    (fics_html / "story.html").write_text("x" * 100)

    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "chapter1.mp3").write_bytes(b"\x00" * 200)

    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path), setup_complete=True))
    await db_session.flush()

    result = await get_storage_info(db_session)

    assert result["breakdown"]["fics_html"] == 100
    assert result["breakdown"]["audio"] == 200
    assert result["breakdown"]["fics_epub"] == 0
    assert result["breakdown"]["database"] == 0


# Test that get_storage_info raises ValueError when no settings exist
@pytest.mark.asyncio
async def test_get_storage_info_no_settings_raises(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Storage path not configured"):
        await get_storage_info(db_session)


# Test that get_storage_info raises ValueError when settings exist but no path
@pytest.mark.asyncio
async def test_get_storage_info_empty_path_raises(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="", setup_complete=True))
    await db_session.flush()

    with pytest.raises(ValueError, match="Storage path not configured"):
        await get_storage_info(db_session)


# Test that get_storage_info raises ValueError for nonexistent path
@pytest.mark.asyncio
async def test_get_storage_info_nonexistent_path_raises(db_session: AsyncSession):
    db_session.add(
        SettingsModel(
            id=1,
            storage_path="/nonexistent/path/xyz123",
            setup_complete=True,
        )
    )
    await db_session.flush()

    with pytest.raises(ValueError, match="does not exist"):
        await get_storage_info(db_session)


# Test that get_storage_warnings returns a list for a valid path
@pytest.mark.asyncio
async def test_get_storage_warnings_valid_path(db_session: AsyncSession, tmp_path):
    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path), setup_complete=True))
    await db_session.flush()

    warnings = await get_storage_warnings(db_session)
    assert isinstance(warnings, list)

    for w in warnings:
        assert "level" in w
        assert "message" in w


# Test that get_storage_warnings returns empty list when no settings exist
@pytest.mark.asyncio
async def test_get_storage_warnings_no_settings(db_session: AsyncSession):
    warnings = await get_storage_warnings(db_session)
    assert warnings == []


# Test that get_storage_warnings returns empty list when storage_path is empty
@pytest.mark.asyncio
async def test_get_storage_warnings_empty_path(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="", setup_complete=True))
    await db_session.flush()

    warnings = await get_storage_warnings(db_session)
    assert warnings == []


# Test that get_storage_warnings returns error when path does not exist
@pytest.mark.asyncio
async def test_get_storage_warnings_nonexistent_path(db_session: AsyncSession):
    db_session.add(
        SettingsModel(
            id=1,
            storage_path="/nonexistent/path/xyz123",
            setup_complete=True,
        )
    )
    await db_session.flush()

    warnings = await get_storage_warnings(db_session)
    assert len(warnings) == 1
    assert warnings[0]["level"] == "error"
    assert "does not exist" in warnings[0]["message"]


# Test that _dir_size returns 0 for an empty directory
def test_dir_size_empty_directory(tmp_path):
    result = _dir_size(str(tmp_path))
    assert result == 0


# Test that _dir_size returns correct total for files
def test_dir_size_with_files(tmp_path):
    (tmp_path / "file1.txt").write_text("hello")
    (tmp_path / "file2.txt").write_text("world!")

    result = _dir_size(str(tmp_path))
    assert result == 5 + 6


# Test that _dir_size includes files in subdirectories
def test_dir_size_nested_files(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_bytes(b"\x00" * 50)
    (tmp_path / "top.txt").write_bytes(b"\x00" * 30)

    result = _dir_size(str(tmp_path))
    assert result == 80


# Test that _dir_size returns 0 for a nonexistent path
def test_dir_size_nonexistent_path():
    result = _dir_size("/nonexistent/path/xyz123")
    assert result == 0


# Test that get_storage_info counts other files and unknown directories
@pytest.mark.asyncio
async def test_get_storage_info_other_files(db_session: AsyncSession, tmp_path):
    # Create a loose file at the root
    (tmp_path / "readme.txt").write_text("hello")

    # Create an unknown subdirectory
    unknown = tmp_path / "unknown_dir"
    unknown.mkdir()
    (unknown / "data.bin").write_bytes(b"\x00" * 42)

    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path), setup_complete=True))
    await db_session.flush()

    result = await get_storage_info(db_session)

    assert result["breakdown"]["other"] == 5 + 42
