# Load libraries
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# Stores metadata and local state for an archived fanfiction work
class Fic(Base):
    __tablename__ = "fics"
    __table_args__ = (
        UniqueConstraint("source_site", "source_id", name="uq_fic_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_site: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(50))
    rating: Mapped[str | None] = mapped_column(String(50))
    warnings: Mapped[str | None] = mapped_column(Text)
    categories: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(Integer)
    chapter_count: Mapped[int | None] = mapped_column(Integer)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    date_published: Mapped[datetime | None] = mapped_column(DateTime)
    date_published_raw: Mapped[str | None] = mapped_column(Text)
    date_updated: Mapped[datetime | None] = mapped_column(DateTime)
    date_updated_raw: Mapped[str | None] = mapped_column(Text)
    date_archived: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    date_last_synced: Mapped[datetime | None] = mapped_column(DateTime)
    is_favourite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_source_available: Mapped[bool] = mapped_column(Boolean, default=True)
    reading_chapter_index: Mapped[int | None] = mapped_column(Integer)
    reading_paragraph_index: Mapped[int | None] = mapped_column(Integer)
    reading_char_offset: Mapped[int | None] = mapped_column(Integer)
    reading_status: Mapped[str] = mapped_column(String(20), default="none")
    html_path: Mapped[str | None] = mapped_column(Text)
    epub_path: Mapped[str | None] = mapped_column(Text)
    import_method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now()
    )

    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="fic", cascade="all, delete-orphan",
        order_by="Chapter.chapter_number",
    )
    authors: Mapped[list["backend.models.author.Author"]] = relationship(
        secondary="fic_authors", back_populates="fics", lazy="selectin",
    )
    fandoms: Mapped[list["backend.models.fandom.Fandom"]] = relationship(
        secondary="fic_fandoms", back_populates="fics", lazy="selectin",
    )
    tags: Mapped[list["backend.models.tag.Tag"]] = relationship(
        secondary="fic_tags", back_populates="fics", lazy="selectin",
    )
    relationships_list: Mapped[list["backend.models.relationship.Relationship"]] = relationship(
        secondary="fic_relationships", back_populates="fics", lazy="selectin",
    )
    characters: Mapped[list["backend.models.character.FicCharacter"]] = relationship(
        back_populates="fic", cascade="all, delete-orphan", lazy="selectin",
    )


# Stores an individual chapter belonging to a fic
class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    html_path: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now()
    )

    fic: Mapped["Fic"] = relationship(back_populates="chapters")
    versions: Mapped[list["backend.models.chapter_version.ChapterVersion"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan",
        order_by="backend.models.chapter_version.ChapterVersion.version_date.desc()",
    )
