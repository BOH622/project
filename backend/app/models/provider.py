"""Provider org, user, auth-related models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedUUID
from app.models.enums import ImpersonationScope, UserRole, UserStatus


class ProviderOrg(TimestampedUUID, Base):
    __tablename__ = "provider_org"

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_address: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    email_mirror_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class User(TimestampedUUID, Base):
    __tablename__ = "app_user"  # "user" is reserved in Postgres

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provider_org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=32), default=UserRole.member, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=32), default=UserStatus.pending_invite, nullable=False
    )
    global_notification_prefs: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {"new_messages": True, "project_updates": True, "quotes_billing": True},
        nullable=False,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    org: Mapped[ProviderOrg] = relationship(back_populates="users")


class MagicLinkToken(TimestampedUUID, Base):
    """Single-use magic link for email-based login."""

    __tablename__ = "magic_link_token"

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ImpersonationSession(TimestampedUUID, Base):
    """UserCue Super-Admin impersonates a provider org. Read-only in v1. Audit-logged."""

    __tablename__ = "impersonation_session"

    super_admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False, index=True
    )
    impersonated_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provider_org.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[ImpersonationScope] = mapped_column(
        Enum(ImpersonationScope, native_enum=False, length=32),
        default=ImpersonationScope.read_only,
        nullable=False,
    )
    audit_events: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
