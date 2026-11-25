# Load libraries
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

# Association table linking fics to their relationships
fic_relationships = Table(
    "fic_relationships",
    Base.metadata,
    Column("fic_id", Integer, ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
    Column("relationship_id", Integer, ForeignKey("relationships.id", ondelete="CASCADE"), primary_key=True),
)


# Stores relationship/ship pairings from source sites
class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship_type: Mapped[str | None] = mapped_column(String(20))
    source_site: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    fics: Mapped[list["backend.models.fic.Fic"]] = relationship(
        secondary=fic_relationships, back_populates="relationships_list",
    )
