# Load libraries
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


# Stores a compressed snapshot of a chapter's previous content
class ChapterVersion(Base):
    __tablename__ = "chapter_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    version_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    word_count: Mapped[int | None] = mapped_column(Integer)

    chapter: Mapped["backend.models.fic.Chapter"] = relationship(
        back_populates="versions"
    )
