# Load libraries
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


# Stores global application configuration and preferences
class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    theme: Mapped[str] = mapped_column(String(10), default="dark")
    smtp_host: Mapped[str | None] = mapped_column(String(255))
    smtp_port: Mapped[int | None] = mapped_column(Integer)
    smtp_username: Mapped[str | None] = mapped_column(String(255))
    smtp_password_encrypted: Mapped[str | None] = mapped_column(Text)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    smtp_from_address: Mapped[str | None] = mapped_column(String(255))
    smtp_to_address: Mapped[str | None] = mapped_column(String(255))
    backup_location: Mapped[str | None] = mapped_column(Text)
    backup_schedule: Mapped[str | None] = mapped_column(String(50))
    cloudflare_trust_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    remember_device_days: Mapped[int] = mapped_column(Integer, default=30)
    setup_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now()
    )
