"""Launch-phase models: redirect URLs, test-ID exchange."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampedUUID
from app.models.enums import RedirectOutcome, TestOutcome


class RedirectURL(TimestampedUUID, Base):
    __tablename__ = "redirect_url"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    outcome: Mapped[RedirectOutcome] = mapped_column(
        Enum(RedirectOutcome, native_enum=False, length=32), nullable=False
    )
    url_template: Mapped[str] = mapped_column(String(1024), nullable=False)


class TestExchange(TimestampedUUID, Base):
    __tablename__ = "test_exchange"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_id_value: Mapped[str] = mapped_column(String(255), nullable=False)
    test_outcome: Mapped[TestOutcome] = mapped_column(
        Enum(TestOutcome, native_enum=False, length=32), nullable=False
    )
    verified_by_ops: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
