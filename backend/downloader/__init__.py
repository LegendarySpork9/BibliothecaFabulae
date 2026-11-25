# FanFicFare download integration
from backend.downloader.fanficfare_wrapper import (
    DownloadResult,
    UpdateResult,
    download_fic,
    get_story_metadata,
    update_fic,
)
from backend.downloader.html_generator import clean_chapter_html, save_chapters_as_html
from backend.downloader.metadata_extractor import extract_chapters, extract_metadata

__all__ = [
    "DownloadResult",
    "UpdateResult",
    "clean_chapter_html",
    "download_fic",
    "extract_chapters",
    "extract_metadata",
    "get_story_metadata",
    "save_chapters_as_html",
    "update_fic",
]
