"""Outbound + inbound webhook records. Powers future provider-API adapters and internal event bus."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampedUUID


class OutboundWebhook(TimestampedUUID, Base):
    """Per-provider-org webhook subscription. Adapter layer dispatches canonical events here."""

    __tablename__ = "outbound_webhook"

    provider_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provider_org.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    event_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    hmac_secret: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class InboundWebhook(TimestampedUUID, Base):
    """Log + idempotency key for every inbound webhook from UserCue or provider-native APIs."""

    __tablename__ = "inbound_webhook"

    source: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    raw_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(String(2048), nullable=True)
