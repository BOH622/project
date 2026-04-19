"""Magic-link token — signature & DB-backed single-use enforcement.

These tests use a mock AsyncSession since we can't assume Postgres in unit env.
Integration tests (once a dev DB exists) will exercise the same paths against real SQL.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from itsdangerous import URLSafeTimedSerializer

from app.auth import tokens
from app.auth.tokens import InvalidToken
from app.config import settings


def _make_db_with_row(row: object | None) -> MagicMock:
    """Build a mock AsyncSession whose .execute returns the given row."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none = MagicMock(return_value=row)
    db.execute = AsyncMock(return_value=execute_result)
    return db


async def test_issue_persists_row_and_returns_signed_token() -> None:
    db = _make_db_with_row(None)
    raw = await tokens.issue(db, "Alice@Provider.com")

    # Token decodes correctly with expected payload
    serializer = URLSafeTimedSerializer(settings.auth_signing_key, salt="magic-link")
    payload = serializer.loads(raw)
    assert payload["email"] == "alice@provider.com"  # lowercased
    assert "nonce" in payload

    # Row was added and committed
    db.add.assert_called_once()
    added_row = db.add.call_args[0][0]
    assert added_row.email == "alice@provider.com"
    assert added_row.expires_at > datetime.now(timezone.utc)
    db.commit.assert_awaited()


async def test_consume_rejects_bad_signature() -> None:
    db = _make_db_with_row(None)
    with pytest.raises(InvalidToken, match="signature"):
        await tokens.consume(db, "totally-bogus-token")


async def test_consume_rejects_expired_token() -> None:
    """A token signed with the real serializer but with an old timestamp must be rejected."""
    serializer = URLSafeTimedSerializer(settings.auth_signing_key, salt="magic-link")
    raw = serializer.dumps({"email": "x@y.com", "nonce": "abc"})

    # Monkey-patch the loads to raise as if expired. Easier than waiting 15 min.
    import app.auth.tokens as t
    original = t._serializer.loads

    def expired(*args, **kwargs):
        from itsdangerous import SignatureExpired
        raise SignatureExpired("test")

    t._serializer.loads = expired
    try:
        db = _make_db_with_row(None)
        with pytest.raises(InvalidToken, match="expired"):
            await tokens.consume(db, raw)
    finally:
        t._serializer.loads = original


async def test_consume_rejects_unknown_token() -> None:
    """Valid signature but token_hash not in DB → rejected."""
    serializer = URLSafeTimedSerializer(settings.auth_signing_key, salt="magic-link")
    raw = serializer.dumps({"email": "x@y.com", "nonce": "abc"})
    db = _make_db_with_row(None)  # DB returns None — no row found
    with pytest.raises(InvalidToken, match="unknown"):
        await tokens.consume(db, raw)


async def test_consume_rejects_already_used_token() -> None:
    serializer = URLSafeTimedSerializer(settings.auth_signing_key, salt="magic-link")
    raw = serializer.dumps({"email": "x@y.com", "nonce": "abc"})
    used_row = SimpleNamespace(
        email="x@y.com",
        token_hash=tokens._hash(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        used_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db = _make_db_with_row(used_row)
    with pytest.raises(InvalidToken, match="already used"):
        await tokens.consume(db, raw)


async def test_consume_success_marks_used_and_returns_email() -> None:
    serializer = URLSafeTimedSerializer(settings.auth_signing_key, salt="magic-link")
    raw = serializer.dumps({"email": "alice@provider.com", "nonce": "abc"})
    fresh_row = SimpleNamespace(
        email="alice@provider.com",
        token_hash=tokens._hash(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        used_at=None,
    )
    db = _make_db_with_row(fresh_row)
    email = await tokens.consume(db, raw)
    assert email == "alice@provider.com"
    assert fresh_row.used_at is not None  # marked used
    db.commit.assert_awaited()


def test_hash_is_deterministic_and_collision_resistant() -> None:
    assert tokens._hash("abc") == tokens._hash("abc")
    assert tokens._hash("abc") != tokens._hash("abd")
    assert len(tokens._hash("abc")) == 64  # sha256 hex
