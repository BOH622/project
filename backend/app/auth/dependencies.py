"""FastAPI auth dependencies. `get_session_context` is the chokepoint."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import COOKIE_NAME, InvalidSession, verify
from app.db import get_session
from app.models import ImpersonationSession, User


@dataclass
class SessionContext:
    """Per-request auth state. Feeds every provider-scoped query."""

    user: User
    impersonation: ImpersonationSession | None = None

    @property
    def is_impersonating(self) -> bool:
        return self.impersonation is not None

    @property
    def effective_org_id(self) -> uuid.UUID:
        """The provider_org_id to filter provider-scoped queries by."""
        if self.impersonation is not None:
            return self.impersonation.impersonated_org_id
        return self.user.org_id


async def get_session_context(
    session_cookie: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: AsyncSession = Depends(get_session),
) -> SessionContext:
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    try:
        user_id, imp_id = verify(session_cookie)
    except InvalidSession as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid session") from e

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")

    impersonation: ImpersonationSession | None = None
    if imp_id is not None:
        impersonation = await db.get(ImpersonationSession, imp_id)
        if impersonation is None or impersonation.ended_at is not None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "impersonation session ended")
        if impersonation.super_admin_user_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "impersonation/user mismatch")

    return SessionContext(user=user, impersonation=impersonation)


async def require_super_admin(ctx: SessionContext = Depends(get_session_context)) -> SessionContext:
    if not ctx.user.is_super_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "super-admin required")
    return ctx


async def require_org_admin(ctx: SessionContext = Depends(get_session_context)) -> SessionContext:
    from app.models.enums import UserRole

    if ctx.is_impersonating:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "read-only during impersonation")
    if ctx.user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "org admin required")
    return ctx


async def reject_if_impersonating(
    ctx: SessionContext = Depends(get_session_context),
) -> SessionContext:
    """Attach to any mutation endpoint to enforce read-only impersonation."""
    if ctx.is_impersonating:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "read-only during impersonation")
    return ctx
