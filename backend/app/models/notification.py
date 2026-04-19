"""Notification — in-portal feed; email sent for events flagged in design §8."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampedUUID
from app.models.enums import NotificationEventType


class Notification(TimestampedUUID, Base):
    __tablename__ = "notification"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, native_enum=False, length=64), nullable=False, index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
