"""Inbound webhook endpoint: rejects unsigned, accepts signed, replays are no-ops."""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.webhooks.hmac_signing import (
    HEADER_IDEMPOTENCY,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    sign,
)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _mock_db(existing: object | None = None) -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    class _Result:
        def scalar_one_or_none(self) -> object | None:
            return existing

    db.execute = AsyncMock(return_value=_Result())
    return db


def _override_db(db: MagicMock) -> None:
    from app.db import get_session

    async def _fake():
        yield db

    app.dependency_overrides[get_session] = _fake


def _reset_overrides() -> None:
    app.dependency_overrides.clear()


async def test_missing_idempotency_key_rejected(client: AsyncClient) -> None:
    _override_db(_mock_db())
    try:
        resp = await client.post("/webhooks/inbound/usercue", content=b"{}")
        assert resp.status_code == 400
        assert "idempotency" in resp.json()["detail"]
    finally:
        _reset_overrides()


async def test_bad_signature_rejected(client: AsyncClient) -> None:
    _override_db(_mock_db())
    try:
        body = json.dumps({"type": "invitation.published"}).encode()
        resp = await client.post(
            "/webhooks/inbound/usercue",
            content=body,
            headers={
                HEADER_SIGNATURE: "v1=deadbeef",
                HEADER_TIMESTAMP: str(int(time.time())),
                HEADER_IDEMPOTENCY: "idem-1",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401
    finally:
        _reset_overrides()


async def test_valid_signature_accepted(client: AsyncClient) -> None:
    _override_db(_mock_db())
    try:
        body = json.dumps({"type": "invitation.published"}).encode()
        signature, ts = sign(body, settings.webhook_hmac_secret)
        resp = await client.post(
            "/webhooks/inbound/usercue",
            content=body,
            headers={
                HEADER_SIGNATURE: signature,
                HEADER_TIMESTAMP: str(ts),
                HEADER_IDEMPOTENCY: "idem-valid-1",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "accepted"}
    finally:
        _reset_overrides()


async def test_replay_returns_200_without_processing(client: AsyncClient) -> None:
    # Existing row = this idempotency_key was already seen → short-circuit.
    existing_row = MagicMock()
    _override_db(_mock_db(existing=existing_row))
    try:
        body = json.dumps({"type": "invitation.published"}).encode()
        signature, ts = sign(body, settings.webhook_hmac_secret)
        resp = await client.post(
            "/webhooks/inbound/usercue",
            content=body,
            headers={
                HEADER_SIGNATURE: signature,
                HEADER_TIMESTAMP: str(ts),
                HEADER_IDEMPOTENCY: "already-seen",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "replay"}
    finally:
        _reset_overrides()


async def test_invalid_body_still_persists_and_rejects(client: AsyncClient) -> None:
    """Even if the body is not JSON, we persist the audit record but reject with 401 (no sig)."""
    db = _mock_db()
    _override_db(db)
    try:
        resp = await client.post(
            "/webhooks/inbound/usercue",
            content=b"not json at all",
            headers={
                HEADER_SIGNATURE: "v1=fake",
                HEADER_TIMESTAMP: str(int(time.time())),
                HEADER_IDEMPOTENCY: "idem-bad-body",
                "Content-Type": "text/plain",
            },
        )
        assert resp.status_code == 401
        # Audit row was still added before the 401.
        db.add.assert_called_once()
    finally:
        _reset_overrides()
