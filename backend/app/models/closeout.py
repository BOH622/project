"""Close-out packet + Invoice."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampedUUID
from app.models.enums import CloseoutState, PaymentState


class CloseoutPacket(TimestampedUUID, Base):
    __tablename__ = "closeout_packet"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    state: Mapped[CloseoutState] = mapped_column(
        Enum(CloseoutState, native_enum=False, length=32),
        default=CloseoutState.pending,
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=True
    )
    outstanding_action_request_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    post_mortem_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_accepted_n: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_removed_n: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_charge_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )


class Invoice(TimestampedUUID, Base):
    __tablename__ = "invoice"

    closeout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("closeout_packet.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    po_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    payment_state: Mapped[PaymentState] = mapped_column(
        Enum(PaymentState, native_enum=False, length=32),
        default=PaymentState.pending,
        nullable=False,
        index=True,
    )
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
