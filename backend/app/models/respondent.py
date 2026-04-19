"""Respondent — most security-sensitive object. QC fields gated at query layer."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampedUUID
from app.models.enums import QcStatus, RespondentStatus


class Respondent(TimestampedUUID, Base):
    """Per-ID respondent record. QC fields null during fielding; revealed on close-out flip.
    Duration fields (active_time, total_duration, message_count) are NOT present in this schema
    by design — the canonical model refuses to store them on provider-visible surfaces."""

    __tablename__ = "respondent"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[RespondentStatus] = mapped_column(
        Enum(RespondentStatus, native_enum=False, length=32),
        default=RespondentStatus.in_progress,
        nullable=False,
        index=True,
    )
    progression_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    segment_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Termination context — provider-visible when status == terminated
    termination_question_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    termination_question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    termination_response_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    screener_responses: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    # QC — hidden from providers until CloseoutPacket.state == 'finalized'
    qc_status: Mapped[QcStatus | None] = mapped_column(
        Enum(QcStatus, native_enum=False, length=32), nullable=True
    )
    qc_reason_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    qc_reason_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
