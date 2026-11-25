# Load libraries
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

# Association table linking fics to their authors
fic_authors = Table(
    "fic_authors",
    Base.metadata,
    Column("fic_id", Integer, ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)


# Stores author information from source sites
class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_site: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(100))
    profile_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    fics: Mapped[list["backend.models.fic.Fic"]] = relationship(
        secondary=fic_authors, back_populates="authors",
    )
