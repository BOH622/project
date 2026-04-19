"""ActionRequest (ID reset, invoice dispute) and RespondentAction (follow-up, clarification)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampedUUID
from app.models.enums import (
    ActionRequestState,
    ActionRequestType,
    RespondentActionState,
    RespondentActionType,
)


class ActionRequest(TimestampedUUID, Base):
    """v1 scope: id_reset + invoice_dispute. Quota changes stay on email until v2."""

    __tablename__ = "action_request"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[ActionRequestType] = mapped_column(
        Enum(ActionRequestType, native_enum=False, length=32), nullable=False, index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[ActionRequestState] = mapped_column(
        Enum(ActionRequestState, native_enum=False, length=32),
        default=ActionRequestState.submitted,
        nullable=False,
        index=True,
    )
    ops_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RespondentAction(TimestampedUUID, Base):
    """Row-level respondent-directed actions (follow-up, clarification). v2+. All ops-gated."""

    __tablename__ = "respondent_action"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_respondent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("respondent.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[RespondentActionType] = mapped_column(
        Enum(RespondentActionType, native_enum=False, length=32), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    state: Mapped[RespondentActionState] = mapped_column(
        Enum(RespondentActionState, native_enum=False, length=32),
        default=RespondentActionState.submitted,
        nullable=False,
    )
    ops_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    routed_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
