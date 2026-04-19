"""Session cookie signing. One cookie: session, carries user_id. Long-lived, revoked by re-auth."""
from __future__ import annotations

import uuid

from itsdangerous import BadSignature, URLSafeSerializer

from app.config import settings

_serializer = URLSafeSerializer(settings.auth_signing_key, salt="session")

COOKIE_NAME = "session"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days


class InvalidSession(Exception):
    pass


def sign(user_id: uuid.UUID, impersonation_id: uuid.UUID | None = None) -> str:
    payload = {"u": str(user_id)}
    if impersonation_id is not None:
        payload["i"] = str(impersonation_id)
    return _serializer.dumps(payload)


def verify(cookie: str) -> tuple[uuid.UUID, uuid.UUID | None]:
    """Returns (user_id, impersonation_id_or_none)."""
    try:
        payload = _serializer.loads(cookie)
    except BadSignature as e:
        raise InvalidSession("bad signature") from e
    user_id = uuid.UUID(payload["u"])
    imp_id = uuid.UUID(payload["i"]) if "i" in payload else None
    return user_id, imp_id
