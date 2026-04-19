"""Super-admin routes: impersonate a provider org (read-only)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import impersonation as impersonation_service
from app.auth.dependencies import (
    SessionContext,
    get_session_context,
    require_super_admin,
)
from app.auth.session import COOKIE_MAX_AGE_SECONDS, COOKIE_NAME, sign
from app.config import settings
from app.db import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


class ImpersonationStarted(BaseModel):
    impersonation_id: str
    impersonated_org_id: str
    scope: str


def _refresh_cookie(response: Response, user_id: uuid.UUID, imp_id: uuid.UUID | None) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=sign(user_id, impersonation_id=imp_id),
        max_age=COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=not settings.backend_base_url.startswith("http://"),
        path="/",
    )


@router.post("/impersonate/{org_id}")
async def start_impersonation(
    org_id: uuid.UUID,
    response: Response,
    ctx: SessionContext = Depends(require_super_admin),
    db: AsyncSession = Depends(get_session),
) -> ImpersonationStarted:
    if ctx.is_impersonating:
        raise HTTPException(status.HTTP_409_CONFLICT, "already impersonating; stop first")

    try:
        imp = await impersonation_service.start(db, super_admin=ctx.user, target_org_id=org_id)
    except impersonation_service.ImpersonationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    _refresh_cookie(response, ctx.user.id, imp.id)
    return ImpersonationStarted(
        impersonation_id=str(imp.id),
        impersonated_org_id=str(imp.impersonated_org_id),
        scope=imp.scope.value,
    )


@router.post("/impersonate/stop", status_code=status.HTTP_204_NO_CONTENT)
async def stop_impersonation(
    response: Response,
    ctx: SessionContext = Depends(get_session_context),
    db: AsyncSession = Depends(get_session),
) -> None:
    if ctx.impersonation is None:
        return  # idempotent — stopping when not impersonating is a no-op
    await impersonation_service.stop(db, ctx.impersonation)
    _refresh_cookie(response, ctx.user.id, None)
