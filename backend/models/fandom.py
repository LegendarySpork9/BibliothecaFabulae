# Load libraries
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

# Association table linking fics to their fandoms
fic_fandoms = Table(
    "fic_fandoms",
    Base.metadata,
    Column("fic_id", Integer, ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
    Column("fandom_id", Integer, ForeignKey("fandoms.id", ondelete="CASCADE"), primary_key=True),
)


# Stores fandom categories from source sites
class Fandom(Base):
    __tablename__ = "fandoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_site: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    fics: Mapped[list["backend.models.fic.Fic"]] = relationship(
        secondary=fic_fandoms, back_populates="fandoms",
    )
