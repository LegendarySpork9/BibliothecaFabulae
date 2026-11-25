# Load libraries
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


# Stores configuration for an enabled source site
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auth_type: Mapped[str] = mapped_column(String(30), nullable=False, default="none")
    auth_data_encrypted: Mapped[str | None] = mapped_column(Text)
    auth_status: Mapped[str] = mapped_column(String(20), default="unknown")
    config_data_encrypted: Mapped[str | None] = mapped_column(Text)
    auth_last_checked: Mapped[datetime | None] = mapped_column(DateTime)
    sync_interval_bookmarks: Mapped[str] = mapped_column(
        String(50), default="0 2 * * *"
    )
    sync_interval_updates: Mapped[str] = mapped_column(
        String(50), default="0 3 * * *"
    )
    rate_limit_config: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now()
    )


# Tracks the progress of bookmark synchronisation for a source site
class BookmarkSyncState(Base):
    __tablename__ = "bookmark_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_site: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    last_synced: Mapped[datetime | None] = mapped_column(DateTime)
    last_bookmark_id: Mapped[str | None] = mapped_column(String(100))
    total_bookmarks: Mapped[int] = mapped_column(Integer, default=0)
    total_synced: Mapped[int] = mapped_column(Integer, default=0)
    sync_status: Mapped[str] = mapped_column(String(20), default="idle")
    sync_progress_current: Mapped[int] = mapped_column(Integer, default=0)
    sync_progress_total: Mapped[int | None] = mapped_column(Integer)
    sync_message: Mapped[str | None] = mapped_column(Text)
