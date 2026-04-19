"""Invitation, Quote, Assignment, Screener — the bid/quote lifecycle."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedUUID
from app.models.enums import (
    AssignmentState,
    DeclineReason,
    InvitationState,
    QuoteState,
    ScreenerBlockType,
    ScreenerType,
)


class Screener(TimestampedUUID, Base):
    __tablename__ = "screener"

    type: Mapped[ScreenerType] = mapped_column(
        Enum(ScreenerType, native_enum=False, length=32), nullable=False
    )
    file_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_study_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True  # points to UserCue-side programming, no FK here
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    blocks: Mapped[list["ScreenerBlock"]] = relationship(
        back_populates="screener",
        cascade="all, delete-orphan",
        order_by="ScreenerBlock.order_index",
    )


class ScreenerBlock(TimestampedUUID, Base):
    __tablename__ = "screener_block"

    screener_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screener.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[ScreenerBlockType] = mapped_column(
        Enum(ScreenerBlockType, native_enum=False, length=32), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    logic: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    screener: Mapped[Screener] = relationship(back_populates="blocks")


class Invitation(TimestampedUUID, Base):
    __tablename__ = "invitation"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provider_org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    state: Mapped[InvitationState] = mapped_column(
        Enum(InvitationState, native_enum=False, length=32),
        default=InvitationState.new,
        nullable=False,
        index=True,
    )
    bid_brief: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    quote_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    declined_reason: Mapped[DeclineReason | None] = mapped_column(
        Enum(DeclineReason, native_enum=False, length=32), nullable=True
    )
    declined_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    quotes: Mapped[list["Quote"]] = relationship(
        back_populates="invitation", cascade="all, delete-orphan"
    )


class Quote(TimestampedUUID, Base):
    __tablename__ = "quote"

    invitation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invitation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    n_commit: Mapped[int] = mapped_column(Integer, nullable=False)
    cpi: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pm_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    timeline_commit: Mapped[str] = mapped_column(String(255), nullable=False)
    segment_commits: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    state: Mapped[QuoteState] = mapped_column(
        Enum(QuoteState, native_enum=False, length=32),
        default=QuoteState.submitted,
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revision_history: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    invitation: Mapped[Invitation] = relationship(back_populates="quotes")


class Assignment(TimestampedUUID, Base):
    """Created when a Quote is accepted. The provider's working record for this project."""

    __tablename__ = "assignment"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provider_org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    accepted_quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote.id"), nullable=False
    )
    state: Mapped[AssignmentState] = mapped_column(
        Enum(AssignmentState, native_enum=False, length=32),
        default=AssignmentState.pre_launch,
        nullable=False,
        index=True,
    )
    team_member_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    team_notification_prefs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
