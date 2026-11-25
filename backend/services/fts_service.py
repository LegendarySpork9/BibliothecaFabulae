# Load libraries
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Inserts or replaces a chapter's content in the FTS5 index
async def index_chapter(
    db: AsyncSession,
    fic_id: int,
    chapter_id: int,
    title: str,
    content: str,
) -> None:
    await db.execute(
        text(
            "DELETE FROM fic_content_fts "
            "WHERE fic_id = :fic_id AND chapter_id = :chapter_id"
        ),
        {"fic_id": str(fic_id), "chapter_id": str(chapter_id)},
    )
    await db.execute(
        text(
            "INSERT INTO fic_content_fts(fic_id, chapter_id, title, content) "
            "VALUES (:fic_id, :chapter_id, :title, :content)"
        ),
        {
            "fic_id": str(fic_id),
            "chapter_id": str(chapter_id),
            "title": title or "",
            "content": content,
        },
    )


# Removes all FTS5 entries for a fic
async def remove_fic_index(db: AsyncSession, fic_id: int) -> None:
    await db.execute(
        text("DELETE FROM fic_content_fts WHERE fic_id = :fic_id"),
        {"fic_id": str(fic_id)},
    )


# Performs full-text search and returns ranked results with snippets
async def search(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    result = await db.execute(
        text(
            "SELECT fic_id, chapter_id, "
            "snippet(fic_content_fts, 3, '<mark>', '</mark>', '...', 64) as snippet, "
            "rank "
            "FROM fic_content_fts "
            "WHERE fic_content_fts MATCH :query "
            "ORDER BY rank "
            "LIMIT :limit OFFSET :offset"
        ),
        {"query": query, "limit": limit, "offset": offset},
    )

    rows = result.fetchall()

    return [
        {
            "fic_id": int(row[0]),
            "chapter_id": int(row[1]),
            "snippet": row[2],
            "rank": row[3],
        }
        for row in rows
    ]
