"""Project + QuotaSegment — the per-campaign shared records."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import JSON, Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedUUID
from app.models.enums import ProjectLifecycleStage


class Project(TimestampedUUID, Base):
    """Shared project record. Client identity is never stored on fields exposed to providers."""

    __tablename__ = "project"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_stage: Mapped[ProjectLifecycleStage] = mapped_column(
        Enum(ProjectLifecycleStage, native_enum=False, length=32),
        default=ProjectLifecycleStage.quoting,
        nullable=False,
        index=True,
    )
    audience_brief: Mapped[str] = mapped_column(Text, default="", nullable=False)
    loi_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_n_target: Mapped[int] = mapped_column(Integer, nullable=False)
    timeline_start: Mapped[date] = mapped_column(Date, nullable=False)
    timeline_end: Mapped[date] = mapped_column(Date, nullable=False)
    geographies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    screener_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screener.id"), nullable=True
    )
    discussion_guide_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    segments: Mapped[list["QuotaSegment"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class QuotaSegment(TimestampedUUID, Base):
    """Per-project quota segment. `visible_to_providers` gates exposure end-to-end."""

    __tablename__ = "quota_segment"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    segment_group: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    quota_target_n: Mapped[int] = mapped_column(Integer, nullable=False)
    visible_to_providers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped[Project] = relationship(back_populates="segments")
