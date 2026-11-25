# Load libraries
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# Stores character information from source sites
class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_site: Mapped[str | None] = mapped_column(String(50))
    gender: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    fic_links: Mapped[list["FicCharacter"]] = relationship(
        back_populates="character", cascade="all, delete-orphan",
    )


# Associates a character with a fic, tracking POV status
class FicCharacter(Base):
    __tablename__ = "fic_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_pov: Mapped[bool] = mapped_column(Boolean, default=False)

    fic: Mapped["backend.models.fic.Fic"] = relationship(back_populates="characters")
    character: Mapped["Character"] = relationship(back_populates="fic_links")
