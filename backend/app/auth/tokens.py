"""Magic-link token service: signed, time-limited, single-use (DB-backed)."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import MagicLinkToken

_serializer = URLSafeTimedSerializer(settings.auth_signing_key, salt="magic-link")


class InvalidToken(Exception):
    """Token is malformed, expired, reused, or revoked."""


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def issue(db: AsyncSession, email: str, *, ip_address: str | None = None) -> str:
    """Generate a single-use magic-link token. Returns the raw token (put in email URL)."""
    nonce = secrets.token_urlsafe(16)
    raw = _serializer.dumps({"email": email.lower(), "nonce": nonce})
    row = MagicLinkToken(
        email=email.lower(),
        token_hash=_hash(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.magic_link_ttl_seconds),
        ip_address=ip_address,
    )
    db.add(row)
    await db.commit()
    return raw


async def consume(db: AsyncSession, raw: str) -> str:
    """Verify + mark-used. Returns the email the token was issued for."""
    # Step 1: signature + TTL check (fast reject on bad tokens)
    try:
        payload = _serializer.loads(raw, max_age=settings.magic_link_ttl_seconds)
    except SignatureExpired as e:
        raise InvalidToken("token expired") from e
    except BadSignature as e:
        raise InvalidToken("bad signature") from e

    # Step 2: DB single-use check
    stmt = select(MagicLinkToken).where(MagicLinkToken.token_hash == _hash(raw))
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise InvalidToken("unknown token")
    if row.used_at is not None:
        raise InvalidToken("token already used")
    if row.expires_at < datetime.now(timezone.utc):
        raise InvalidToken("token expired (db)")

    row.used_at = datetime.now(timezone.utc)
    await db.commit()
    return payload["email"]
