"""Magic-link authentication routes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import tokens
from app.auth.dependencies import SessionContext, get_session_context
from app.auth.session import COOKIE_MAX_AGE_SECONDS, COOKIE_NAME, sign
from app.config import settings
from app.db import get_session
from app.email.sender import get_sender
from app.models import ProviderOrg, User
from app.models.enums import UserStatus
from app.notifications.templates import render

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: EmailStr


class AuthCallback(BaseModel):
    token: str


class CurrentUser(BaseModel):
    id: str
    email: str
    name: str
    org_id: str
    role: str
    is_super_admin: bool
    is_impersonating: bool
    impersonated_org_id: str | None


async def _ensure_super_admin_user(db: AsyncSession, email: str) -> User:
    """Super-admin emails get auto-provisioned into a UserCue Internal org."""
    stmt = select(User).where(User.email == email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is not None:
        return user

    # Find or create the UserCue Internal org
    internal_stmt = select(ProviderOrg).where(ProviderOrg.display_name == "UserCue Internal")
    internal = (await db.execute(internal_stmt)).scalar_one_or_none()
    if internal is None:
        internal = ProviderOrg(
            legal_name="UserCue, Inc.",
            display_name="UserCue Internal",
        )
        db.add(internal)
        await db.flush()

    user = User(
        org_id=internal.id,
        email=email,
        name=email.split("@")[0],
        role="admin",
        status=UserStatus.active,
        is_super_admin=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/request", status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(
    body: AuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Request a magic link. Returns 202 whether or not the email is known — do not leak."""
    email = body.email.lower()
    client_ip = request.client.host if request.client else None

    if email in settings.super_admins:
        await _ensure_super_admin_user(db, email)
        send_email = True
    else:
        stmt = select(User).where(User.email == email)
        user = (await db.execute(stmt)).scalar_one_or_none()
        send_email = user is not None and user.status != UserStatus.disabled

    if send_email:
        raw_token = await tokens.issue(db, email, ip_address=client_ip)
        link = f"{settings.portal_base_url}/auth/callback?token={raw_token}"
        html, text = render("magic_link", link=link)
        await get_sender().send(
            to=email, subject="Sign in to UserCue Projects", html=html, text=text
        )
    return {"status": "accepted"}


@router.post("/callback")
async def auth_callback(
    body: AuthCallback,
    response: Response,
    db: AsyncSession = Depends(get_session),
) -> CurrentUser:
    try:
        email = await tokens.consume(db, body.token)
    except tokens.InvalidToken as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    if user.status == UserStatus.disabled:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "user disabled")

    # First successful login flips invite → active
    if user.status == UserStatus.pending_invite:
        user.status = UserStatus.active
    user.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=sign(user.id),
        max_age=COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=not settings.backend_base_url.startswith("http://"),
        path="/",
    )
    return CurrentUser(
        id=str(user.id),
        email=user.email,
        name=user.name,
        org_id=str(user.org_id),
        role=user.role.value,
        is_super_admin=user.is_super_admin,
        is_impersonating=False,
        impersonated_org_id=None,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me")
async def me(ctx: SessionContext = Depends(get_session_context)) -> CurrentUser:
    return CurrentUser(
        id=str(ctx.user.id),
        email=ctx.user.email,
        name=ctx.user.name,
        org_id=str(ctx.user.org_id),
        role=ctx.user.role.value,
        is_super_admin=ctx.user.is_super_admin,
        is_impersonating=ctx.is_impersonating,
        impersonated_org_id=str(ctx.impersonation.impersonated_org_id)
        if ctx.impersonation is not None
        else None,
    )
