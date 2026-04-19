"""Super-admin impersonation: start, stop, audit."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImpersonationSession, ProviderOrg, User
from app.models.enums import ImpersonationScope


class ImpersonationError(Exception):
    pass


async def start(
    db: AsyncSession,
    *,
    super_admin: User,
    target_org_id: uuid.UUID,
) -> ImpersonationSession:
    if not super_admin.is_super_admin:
        raise ImpersonationError("super-admin required")

    target = await db.get(ProviderOrg, target_org_id)
    if target is None:
        raise ImpersonationError("target org not found")

    sess = ImpersonationSession(
        super_admin_user_id=super_admin.id,
        impersonated_org_id=target_org_id,
        started_at=datetime.now(timezone.utc),
        scope=ImpersonationScope.read_only,
        audit_events=[],
    )
    db.add(sess)
    await db.commit()
    await db.refresh(sess)
    return sess


async def stop(db: AsyncSession, impersonation: ImpersonationSession) -> None:
    impersonation.ended_at = datetime.now(timezone.utc)
    await db.commit()


async def record_access(
    db: AsyncSession,
    impersonation: ImpersonationSession,
    *,
    method: str,
    path: str,
) -> None:
    """Append a single audit event. Called by the auth dependency on every request."""
    # Mutating JSON in SQLAlchemy requires reassignment to signal dirty.
    events = list(impersonation.audit_events or [])
    events.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "path": path,
        }
    )
    impersonation.audit_events = events
    await db.commit()
