# Load libraries
import logging
import os
import re
import shutil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.downloader.fanficfare_wrapper import DownloadResult
from backend.downloader.rating_map import normalize_rating as _normalize_rating
from backend.downloader.html_generator import clean_chapter_html, save_chapters_as_html
from backend.models.author import Author, fic_authors
from backend.models.character import Character, FicCharacter
from backend.models.fandom import Fandom, fic_fandoms
from backend.models.fic import Chapter, Fic
from backend.models.relationship import Relationship, fic_relationships
from backend.models.settings import Settings
from backend.models.tag import Tag, fic_tags
from backend.services import fts_service

logger = logging.getLogger(__name__)


# Retrieves the configured storage path from settings
async def _get_storage_path(db: AsyncSession) -> str:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if not settings_row or not settings_row.storage_path:
        raise ValueError("Storage path not configured")

    return settings_row.storage_path


# Parses a date string from FanFicFare metadata
def _parse_date(value: str | None):
    if not value:
        return None

    from datetime import datetime

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt)

        except (ValueError, TypeError):
            continue

    return None


# Strips HTML tags to extract plain text for word counting
def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


# Stores a downloaded fic, creating database records and saving files
async def store_downloaded_fic(
    db: AsyncSession,
    download_result: DownloadResult,
    source_site: str,
    source_id: str,
    source_url: str,
    import_method: str,
) -> Fic:
    storage_path = await _get_storage_path(db)
    metadata = download_result.metadata

    existing = await db.execute(
        select(Fic).where(Fic.source_site == source_site, Fic.source_id == source_id)
    )

    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Fic already archived: {source_site}/{source_id}")

    total_words = sum(ch.get("word_count", 0) for ch in download_result.chapters)
    num_chapters = metadata.get("numChapters")

    if num_chapters is not None:
        try:
            num_chapters = int(str(num_chapters).replace(",", ""))

        except (ValueError, TypeError):
            num_chapters = len(download_result.chapters)

    else:
        num_chapters = len(download_result.chapters)

    num_words = 0

    try:
        num_words = int(str(metadata.get("numWords", 0)).replace(",", ""))
        
    except (ValueError, TypeError):
        pass

    if not num_words:
        num_words = total_words

    warnings_val = metadata.get("warnings")
    categories_val = metadata.get("ao3categories")

    date_published = _parse_date(metadata.get("datePublished"))
    date_updated = _parse_date(metadata.get("dateUpdated"))

    fic = Fic(
        source_site=source_site,
        source_id=source_id,
        source_url=source_url,
        title=metadata.get("title", "Untitled"),
        summary=metadata.get("description"),
        language=metadata.get("language"),
        rating=_normalize_rating(metadata.get("rating")),
        warnings=warnings_val if isinstance(warnings_val, str) else ", ".join(warnings_val) if warnings_val else None,
        categories=categories_val if isinstance(categories_val, str) else ", ".join(categories_val) if categories_val else None,
        word_count=num_words,
        chapter_count=num_chapters,
        is_complete=metadata.get("status", "").lower() in ("complete", "completed"),
        date_published=date_published,
        date_published_raw=metadata.get("datePublished"),
        date_updated=date_updated,
        date_updated_raw=metadata.get("dateUpdated"),
        import_method=import_method,
    )

    html_dir = os.path.join(storage_path, "fics_html", source_site, source_id)
    epub_dir = os.path.join(storage_path, "fics_epub", source_site)
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(epub_dir, exist_ok=True)

    chapter_paths = save_chapters_as_html(download_result.chapters, html_dir)
    fic.html_path = html_dir

    epub_dest = os.path.join(epub_dir, f"{source_id}.epub")

    if download_result.epub_path and os.path.exists(download_result.epub_path):
        shutil.copy2(download_result.epub_path, epub_dest)

    fic.epub_path = epub_dest

    db.add(fic)
    await db.flush()

    for i, ch_data in enumerate(download_result.chapters):
        chapter = Chapter(
            fic_id=fic.id,
            chapter_number=ch_data["chapter_number"],
            title=ch_data.get("title"),
            html_path=chapter_paths[i] if i < len(chapter_paths) else None,
            word_count=ch_data.get("word_count"),
        )
        db.add(chapter)
        await db.flush()

        plain_text = _strip_html(ch_data.get("html_content", ""))
        await fts_service.index_chapter(
            db, fic.id, chapter.id, ch_data.get("title", ""), plain_text
        )

    await _create_associations(db, fic, metadata)

    return fic


# Creates author, fandom, tag, relationship, and character associations
async def _create_associations(db: AsyncSession, fic: Fic, metadata: dict) -> None:
    for creator_name in metadata.get("creators", []):
        result = await db.execute(
            select(Author).where(
                Author.name == creator_name, Author.source_site == fic.source_site
            )
        )
        author = result.scalar_one_or_none()

        if author is None:
            author = Author(
                name=creator_name,
                source_site=fic.source_site,
                source_id=metadata.get("authorId"),
                profile_url=metadata.get("authorUrl"),
            )
            db.add(author)
            await db.flush()

        await db.execute(
            fic_authors.insert().values(fic_id=fic.id, author_id=author.id)
        )

    for fandom_name in metadata.get("fandoms", []):
        result = await db.execute(
            select(Fandom).where(Fandom.name == fandom_name, Fandom.source_site == fic.source_site)
        )
        fandom = result.scalar_one_or_none()

        if fandom is None:
            fandom = Fandom(name=fandom_name, source_site=fic.source_site)
            db.add(fandom)
            await db.flush()

        await db.execute(fic_fandoms.insert().values(fic_id=fic.id, fandom_id=fandom.id))

    for ship_name in metadata.get("ships", []):
        result = await db.execute(
            select(Relationship).where(
                Relationship.name == ship_name, Relationship.source_site == fic.source_site
            )
        )
        rel = result.scalar_one_or_none()

        if rel is None:
            rel = Relationship(name=ship_name, relationship_type="romantic", source_site=fic.source_site)
            db.add(rel)
            await db.flush()

        await db.execute(fic_relationships.insert().values(fic_id=fic.id, relationship_id=rel.id))

    for char_name in metadata.get("characters", []):
        result = await db.execute(
            select(Character).where(Character.name == char_name, Character.source_site == fic.source_site)
        )
        character = result.scalar_one_or_none()

        if character is None:
            character = Character(name=char_name, source_site=fic.source_site)
            db.add(character)
            await db.flush()

        fic_char = FicCharacter(fic_id=fic.id, character_id=character.id)
        db.add(fic_char)
        await db.flush()

    for tag_name in metadata.get("freeformtags", []):
        result = await db.execute(select(Tag).where(Tag.name == tag_name))
        tag = result.scalar_one_or_none()

        if tag is None:
            tag = Tag(name=tag_name, tag_type="source")
            db.add(tag)
            await db.flush()

        await db.execute(fic_tags.insert().values(fic_id=fic.id, tag_id=tag.id))


# Returns a fic by ID with all associated data
async def get_fic(db: AsyncSession, fic_id: int) -> dict:
    result = await db.execute(select(Fic).where(Fic.id == fic_id))
    fic = result.scalar_one_or_none()

    if fic is None:
        raise ValueError("Fic not found")

    chapter_result = await db.execute(
        select(Chapter).where(Chapter.fic_id == fic.id).order_by(Chapter.chapter_number)
    )
    chapters = chapter_result.scalars().all()

    author_result = await db.execute(
        select(Author).join(fic_authors).where(fic_authors.c.fic_id == fic.id)
    )
    authors = author_result.scalars().all()

    fandom_result = await db.execute(
        select(Fandom).join(fic_fandoms).where(fic_fandoms.c.fic_id == fic.id)
    )
    fandoms = fandom_result.scalars().all()

    rel_result = await db.execute(
        select(Relationship).join(fic_relationships).where(fic_relationships.c.fic_id == fic.id)
    )
    relationships = rel_result.scalars().all()

    char_result = await db.execute(
        select(Character).join(FicCharacter).where(FicCharacter.fic_id == fic.id)
    )
    characters = char_result.scalars().all()

    tag_result = await db.execute(
        select(Tag).join(fic_tags).where(fic_tags.c.fic_id == fic.id)
    )
    tags = tag_result.scalars().all()

    return {
        "id": fic.id,
        "source_site": fic.source_site,
        "source_id": fic.source_id,
        "source_url": fic.source_url,
        "title": fic.title,
        "summary": fic.summary,
        "language": fic.language,
        "rating": fic.rating,
        "warnings": fic.warnings,
        "categories": fic.categories,
        "word_count": fic.word_count,
        "chapter_count": fic.chapter_count,
        "is_complete": fic.is_complete,
        "is_favourite": fic.is_favourite,
        "is_source_available": fic.is_source_available,
        "reading_status": fic.reading_status,
        "import_method": fic.import_method,
        "html_path": fic.html_path,
        "epub_path": fic.epub_path,
        "date_published": fic.date_published_raw or (fic.date_published.isoformat() if fic.date_published else None),
        "date_updated": fic.date_updated_raw or (fic.date_updated.isoformat() if fic.date_updated else None),
        "date_archived": fic.date_archived.isoformat() if fic.date_archived else None,
        "date_last_synced": fic.date_last_synced.isoformat() if fic.date_last_synced else None,
        "authors": [{"id": a.id, "name": a.name} for a in authors],
        "fandoms": [{"id": f.id, "name": f.name} for f in fandoms],
        "relationships": [{"id": r.id, "name": r.name} for r in relationships],
        "characters": [{"id": c.id, "name": c.name} for c in characters],
        "tags": [{"id": t.id, "name": t.name, "tag_type": t.tag_type} for t in tags],
        "chapters": [
            {
                "id": c.id,
                "chapter_number": c.chapter_number,
                "title": c.title,
                "word_count": c.word_count,
            }
            for c in chapters
        ],
    }


# Returns a paginated list of fics with optional filtering and sorting
async def get_fics(
    db: AsyncSession,
    source_site: str | None = None,
    is_complete: bool | None = None,
    is_favourite: bool | None = None,
    is_source_available: bool | None = None,
    import_method: str | None = None,
    sort: str = "-date_archived",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    query = select(Fic)
    count_query = select(func.count(Fic.id))

    if source_site:
        query = query.where(Fic.source_site == source_site)
        count_query = count_query.where(Fic.source_site == source_site)

    if is_complete is not None:
        query = query.where(Fic.is_complete == is_complete)
        count_query = count_query.where(Fic.is_complete == is_complete)

    if is_favourite is not None:
        query = query.where(Fic.is_favourite == is_favourite)
        count_query = count_query.where(Fic.is_favourite == is_favourite)

    if is_source_available is not None:
        query = query.where(Fic.is_source_available == is_source_available)
        count_query = count_query.where(Fic.is_source_available == is_source_available)

    if import_method:
        query = query.where(Fic.import_method == import_method)
        count_query = count_query.where(Fic.import_method == import_method)

    sort_map = {
        "date_archived": Fic.date_archived.asc(),
        "-date_archived": Fic.date_archived.desc(),
        "date_updated": Fic.date_updated.asc(),
        "-date_updated": Fic.date_updated.desc(),
        "title": Fic.title.asc(),
        "-title": Fic.title.desc(),
        "word_count": Fic.word_count.asc(),
        "-word_count": Fic.word_count.desc(),
    }
    query = query.order_by(sort_map.get(sort, Fic.date_archived.desc()))
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    fics = result.scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    items = []

    for fic in fics:
        author_result = await db.execute(
            select(Author).join(fic_authors).where(fic_authors.c.fic_id == fic.id)
        )
        authors = author_result.scalars().all()

        items.append({
            "id": fic.id,
            "source_site": fic.source_site,
            "source_id": fic.source_id,
            "title": fic.title,
            "rating": fic.rating,
            "word_count": fic.word_count,
            "chapter_count": fic.chapter_count,
            "is_complete": fic.is_complete,
            "is_favourite": fic.is_favourite,
            "is_source_available": fic.is_source_available,
            "import_method": fic.import_method,
            "date_archived": fic.date_archived.isoformat() if fic.date_archived else None,
            "authors": [{"id": a.id, "name": a.name} for a in authors],
        })

    return {"items": items, "total": total}


# Returns a list of chapters for a fic
async def get_fic_chapters(db: AsyncSession, fic_id: int) -> list[dict]:
    result = await db.execute(
        select(Chapter).where(Chapter.fic_id == fic_id).order_by(Chapter.chapter_number)
    )
    chapters = result.scalars().all()

    return [
        {
            "id": c.id,
            "chapter_number": c.chapter_number,
            "title": c.title,
            "word_count": c.word_count,
        }
        for c in chapters
    ]


# Reads and returns chapter HTML content from the file system
async def get_chapter_content(db: AsyncSession, chapter_id: int) -> dict:
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if chapter is None:
        raise ValueError("Chapter not found")

    content = ""

    if chapter.html_path and os.path.exists(chapter.html_path):
        with open(chapter.html_path, "r", encoding="utf-8") as f:
            content = f.read()

    return {
        "id": chapter.id,
        "chapter_number": chapter.chapter_number,
        "title": chapter.title,
        "word_count": chapter.word_count,
        "content": content,
    }


# Deletes a fic and all associated files
async def delete_fic(db: AsyncSession, fic_id: int) -> dict:
    result = await db.execute(select(Fic).where(Fic.id == fic_id))
    fic = result.scalar_one_or_none()

    if fic is None:
        raise ValueError("Fic not found")

    if fic.html_path and os.path.isdir(fic.html_path):
        shutil.rmtree(fic.html_path, ignore_errors=True)

    if fic.epub_path and os.path.exists(fic.epub_path):
        os.remove(fic.epub_path)

    await fts_service.remove_fic_index(db, fic_id)

    await db.delete(fic)
    await db.flush()

    return {"success": True}


# Performs a full-text search across all chapter content
async def search_fic_content(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    results = await fts_service.search(db, query, limit=limit, offset=offset)

    enriched = []

    for hit in results:
        fic_result = await db.execute(
            select(Fic.id, Fic.title, Fic.source_site).where(Fic.id == hit["fic_id"])
        )
        fic_row = fic_result.one_or_none()

        if fic_row:
            enriched.append({
                "fic_id": fic_row[0],
                "fic_title": fic_row[1],
                "source_site": fic_row[2],
                "chapter_id": hit["chapter_id"],
                "snippet": hit["snippet"],
            })

    return {"items": enriched, "total": len(enriched)}
