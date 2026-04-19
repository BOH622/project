"""Chat threads + messages, with email-mirror support."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedUUID
from app.models.enums import MessageSource


class MessageThread(TimestampedUUID, Base):
    __tablename__ = "message_thread"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provider_org.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email_mirror_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(TimestampedUUID, Base):
    __tablename__ = "message"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("message_thread.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=True
    )
    # For email-inbound messages where sender is not a known portal user yet
    sender_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    mentions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[MessageSource] = mapped_column(
        Enum(MessageSource, native_enum=False, length=32),
        default=MessageSource.portal,
        nullable=False,
    )
    read_by: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    email_message_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    thread: Mapped[MessageThread] = relationship(back_populates="messages")
