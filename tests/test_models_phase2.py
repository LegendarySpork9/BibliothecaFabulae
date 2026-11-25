# Load libraries
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.author import Author, fic_authors
from backend.models.character import Character, FicCharacter
from backend.models.chapter_version import ChapterVersion
from backend.models.fandom import Fandom, fic_fandoms
from backend.models.fic import Chapter, Fic
from backend.models.relationship import Relationship, fic_relationships
from backend.models.source import BookmarkSyncState, Source
from backend.models.tag import Tag, fic_tags


@pytest.mark.asyncio
async def test_create_fic(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3",
        source_id="12345",
        source_url="https://archiveofourown.org/works/12345",
        title="Test Fic",
        import_method="manual_url",
    )
    db_session.add(fic)
    await db_session.flush()

    result = await db_session.execute(select(Fic).where(Fic.id == fic.id))
    fetched = result.scalar_one()

    assert fetched.source_site == "ao3"
    assert fetched.source_id == "12345"
    assert fetched.title == "Test Fic"
    assert fetched.is_favourite is False
    assert fetched.is_source_available is True
    assert fetched.reading_status == "none"
    assert fetched.import_method == "manual_url"


@pytest.mark.asyncio
async def test_fic_unique_constraint(db_session: AsyncSession):
    fic1 = Fic(
        source_site="ao3", source_id="12345",
        source_url="https://archiveofourown.org/works/12345",
        title="Fic One", import_method="manual_url",
    )
    fic2 = Fic(
        source_site="ao3", source_id="12345",
        source_url="https://archiveofourown.org/works/12345",
        title="Fic Two", import_method="manual_url",
    )
    db_session.add(fic1)
    await db_session.flush()
    db_session.add(fic2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_create_chapter(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="99999",
        source_url="https://archiveofourown.org/works/99999",
        title="Chapter Test", import_method="manual_url",
    )
    db_session.add(fic)
    await db_session.flush()

    chapter = Chapter(
        fic_id=fic.id, chapter_number=1, title="Chapter 1", word_count=5000,
    )
    db_session.add(chapter)
    await db_session.flush()

    result = await db_session.execute(select(Chapter).where(Chapter.fic_id == fic.id))
    fetched = result.scalar_one()

    assert fetched.chapter_number == 1
    assert fetched.title == "Chapter 1"
    assert fetched.word_count == 5000


@pytest.mark.asyncio
async def test_chapter_version(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="88888",
        source_url="https://archiveofourown.org/works/88888",
        title="Version Test", import_method="manual_url",
    )
    db_session.add(fic)
    await db_session.flush()

    chapter = Chapter(fic_id=fic.id, chapter_number=1)
    db_session.add(chapter)
    await db_session.flush()

    import zlib
    compressed = zlib.compress(b"Old chapter content here")

    version = ChapterVersion(
        chapter_id=chapter.id, content=compressed, word_count=4,
    )
    db_session.add(version)
    await db_session.flush()

    result = await db_session.execute(
        select(ChapterVersion).where(ChapterVersion.chapter_id == chapter.id)
    )
    fetched = result.scalar_one()

    assert zlib.decompress(fetched.content) == b"Old chapter content here"
    assert fetched.word_count == 4


@pytest.mark.asyncio
async def test_fic_author_many_to_many(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="77777",
        source_url="https://archiveofourown.org/works/77777",
        title="Author Test", import_method="manual_url",
    )
    author = Author(name="TestAuthor", source_site="ao3", source_id="user1")
    db_session.add_all([fic, author])
    await db_session.flush()

    await db_session.execute(
        fic_authors.insert().values(fic_id=fic.id, author_id=author.id)
    )
    await db_session.flush()

    result = await db_session.execute(
        select(fic_authors).where(fic_authors.c.fic_id == fic.id)
    )
    rows = result.all()

    assert len(rows) == 1
    assert rows[0].author_id == author.id


@pytest.mark.asyncio
async def test_fic_fandom_many_to_many(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="66666",
        source_url="https://archiveofourown.org/works/66666",
        title="Fandom Test", import_method="manual_url",
    )
    fandom = Fandom(name="Harry Potter")
    db_session.add_all([fic, fandom])
    await db_session.flush()

    await db_session.execute(
        fic_fandoms.insert().values(fic_id=fic.id, fandom_id=fandom.id)
    )
    await db_session.flush()

    result = await db_session.execute(
        select(fic_fandoms).where(fic_fandoms.c.fic_id == fic.id)
    )
    rows = result.all()

    assert len(rows) == 1
    assert rows[0].fandom_id == fandom.id


@pytest.mark.asyncio
async def test_fic_tag_many_to_many(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="55555",
        source_url="https://archiveofourown.org/works/55555",
        title="Tag Test", import_method="manual_url",
    )
    tag = Tag(name="Angst", tag_type="source")
    db_session.add_all([fic, tag])
    await db_session.flush()

    await db_session.execute(
        fic_tags.insert().values(fic_id=fic.id, tag_id=tag.id)
    )
    await db_session.flush()

    result = await db_session.execute(
        select(fic_tags).where(fic_tags.c.fic_id == fic.id)
    )
    rows = result.all()

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_fic_relationship_many_to_many(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="44444",
        source_url="https://archiveofourown.org/works/44444",
        title="Relationship Test", import_method="manual_url",
    )
    rel = Relationship(
        name="Character A/Character B", relationship_type="romantic", source_site="ao3",
    )
    db_session.add_all([fic, rel])
    await db_session.flush()

    await db_session.execute(
        fic_relationships.insert().values(fic_id=fic.id, relationship_id=rel.id)
    )
    await db_session.flush()

    result = await db_session.execute(
        select(fic_relationships).where(fic_relationships.c.fic_id == fic.id)
    )
    rows = result.all()

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_fic_character_with_pov(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="33333",
        source_url="https://archiveofourown.org/works/33333",
        title="Character Test", import_method="manual_url",
    )
    character = Character(name="Test Character", source_site="ao3", gender="female")
    db_session.add_all([fic, character])
    await db_session.flush()

    fic_char = FicCharacter(
        fic_id=fic.id, character_id=character.id, is_pov=True,
    )
    db_session.add(fic_char)
    await db_session.flush()

    result = await db_session.execute(
        select(FicCharacter).where(FicCharacter.fic_id == fic.id)
    )
    fetched = result.scalar_one()

    assert fetched.character_id == character.id
    assert fetched.is_pov is True


@pytest.mark.asyncio
async def test_create_source(db_session: AsyncSession):
    source = Source(
        site_key="ao3",
        auth_type="cookies",
        auth_data_encrypted="encrypted_data_here",
        rate_limit_config='{"delay_ms": 2000, "max_pages": 20}',
    )
    db_session.add(source)
    await db_session.flush()

    result = await db_session.execute(select(Source).where(Source.id == source.id))
    fetched = result.scalar_one()

    assert fetched.site_key == "ao3"
    assert fetched.is_enabled is True
    assert fetched.auth_type == "cookies"
    assert fetched.auth_status == "unknown"
    assert fetched.sync_interval_bookmarks == "0 2 * * *"
    assert fetched.sync_interval_updates == "0 3 * * *"


@pytest.mark.asyncio
async def test_source_unique_site_key(db_session: AsyncSession):
    source1 = Source(site_key="ao3", auth_type="none")
    source2 = Source(site_key="ao3", auth_type="cookies")
    db_session.add(source1)
    await db_session.flush()
    db_session.add(source2)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_create_bookmark_sync_state(db_session: AsyncSession):
    state = BookmarkSyncState(source_site="ao3")
    db_session.add(state)
    await db_session.flush()

    result = await db_session.execute(
        select(BookmarkSyncState).where(BookmarkSyncState.source_site == "ao3")
    )
    fetched = result.scalar_one()

    assert fetched.total_bookmarks == 0
    assert fetched.total_synced == 0
    assert fetched.last_synced is None


@pytest.mark.asyncio
async def test_chapter_cascade_delete(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3", source_id="22222",
        source_url="https://archiveofourown.org/works/22222",
        title="Cascade Test", import_method="manual_url",
    )
    db_session.add(fic)
    await db_session.flush()

    chapter = Chapter(fic_id=fic.id, chapter_number=1)
    db_session.add(chapter)
    await db_session.flush()

    await db_session.delete(fic)
    await db_session.flush()

    result = await db_session.execute(select(Chapter).where(Chapter.fic_id == fic.id))
    assert result.scalar_one_or_none() is None
