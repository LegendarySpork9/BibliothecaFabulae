# Load libraries
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

# Association table linking fics to their tags
fic_tags = Table(
    "fic_tags",
    Base.metadata,
    Column("fic_id", Integer, ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


# Stores tags (source-imported or user-defined) for organising fics
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(20), nullable=False, default="source")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    fics: Mapped[list["backend.models.fic.Fic"]] = relationship(
        secondary=fic_tags, back_populates="tags",
    )
