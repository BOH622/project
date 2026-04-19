"""Defense-in-depth middleware: writes are blocked while an impersonation cookie is present.

Tests exercise the middleware directly through the ASGI app, no DB needed — we
build a signed session cookie and hit endpoints that don't require a database
(the middleware rejects before the route runs).
"""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.session import COOKIE_NAME, sign
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_write_without_impersonation_cookie_is_not_short_circuited(client: AsyncClient) -> None:
    # No cookie at all → middleware lets it through; auth dependency 401s.
    response = await client.post("/admin/impersonate/stop")
    assert response.status_code in (204, 401)
    # Not 403 — that would indicate middleware incorrectly short-circuited.
    assert response.status_code != 403


async def test_write_with_impersonation_cookie_is_rejected(client: AsyncClient) -> None:
    user_id = uuid.uuid4()
    imp_id = uuid.uuid4()
    cookie = sign(user_id, impersonation_id=imp_id)
    # /auth/logout isn't exempt-listed — wait, /auth/logout IS exempt. Try a write on /auth/request instead.
    response = await client.post(
        "/auth/request",
        json={"email": "foo@bar.com"},
        cookies={COOKIE_NAME: cookie},
    )
    assert response.status_code == 403
    assert "read-only" in response.json()["detail"]


async def test_stop_impersonation_is_exempt(client: AsyncClient) -> None:
    """Must be able to exit impersonation even while impersonating.

    If middleware short-circuited with 403 we'd get a clean response. If middleware
    lets the request through, it reaches the DB-backed auth dep which fails
    because we have no Postgres in unit-test env — and that failure itself proves
    the middleware did not block.
    """
    user_id = uuid.uuid4()
    imp_id = uuid.uuid4()
    cookie = sign(user_id, impersonation_id=imp_id)
    try:
        response = await client.post(
            "/admin/impersonate/stop",
            cookies={COOKIE_NAME: cookie},
        )
        assert response.status_code != 403, "middleware incorrectly short-circuited"
    except (OSError, ConnectionError):
        pass  # reached DB layer → middleware let it through → test passes


async def test_get_requests_always_pass_middleware(client: AsyncClient) -> None:
    user_id = uuid.uuid4()
    imp_id = uuid.uuid4()
    cookie = sign(user_id, impersonation_id=imp_id)
    response = await client.get("/healthz", cookies={COOKIE_NAME: cookie})
    assert response.status_code == 200
