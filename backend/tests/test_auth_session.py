"""Session cookie signing — deterministic, no DB."""
from __future__ import annotations

import uuid

import pytest

from app.auth.session import InvalidSession, sign, verify


def test_round_trip_user_only() -> None:
    user_id = uuid.uuid4()
    cookie = sign(user_id)
    recovered_user, recovered_imp = verify(cookie)
    assert recovered_user == user_id
    assert recovered_imp is None


def test_round_trip_with_impersonation() -> None:
    user_id = uuid.uuid4()
    imp_id = uuid.uuid4()
    cookie = sign(user_id, impersonation_id=imp_id)
    recovered_user, recovered_imp = verify(cookie)
    assert recovered_user == user_id
    assert recovered_imp == imp_id


def test_tampered_cookie_rejected() -> None:
    user_id = uuid.uuid4()
    cookie = sign(user_id)
    tampered = cookie[:-4] + "xxxx"
    with pytest.raises(InvalidSession):
        verify(tampered)


def test_gibberish_cookie_rejected() -> None:
    with pytest.raises(InvalidSession):
        verify("not-a-real-cookie")
