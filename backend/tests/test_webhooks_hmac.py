"""HMAC signing/verification + replay protection."""
from __future__ import annotations

from app.webhooks.hmac_signing import DEFAULT_MAX_AGE_SECONDS, sign, verify


def test_sign_and_verify_round_trip() -> None:
    body = b'{"event": "test"}'
    secret = "shared-secret"
    signature, ts = sign(body, secret)
    assert verify(body, secret, signature=signature, timestamp=ts) is True


def test_signature_with_wrong_secret_rejected() -> None:
    body = b'{"event": "test"}'
    signature, ts = sign(body, "secret-a")
    assert verify(body, "secret-b", signature=signature, timestamp=ts) is False


def test_signature_with_tampered_body_rejected() -> None:
    body = b'{"event": "test"}'
    secret = "shared-secret"
    signature, ts = sign(body, secret)
    tampered = b'{"event": "hijacked"}'
    assert verify(tampered, secret, signature=signature, timestamp=ts) is False


def test_expired_timestamp_rejected() -> None:
    body = b"{}"
    secret = "shared-secret"
    signature, ts = sign(body, secret, timestamp=1_000_000_000)
    # "now" is far in the future compared to timestamp
    assert (
        verify(
            body,
            secret,
            signature=signature,
            timestamp=ts,
            now=1_000_000_000 + DEFAULT_MAX_AGE_SECONDS + 1,
        )
        is False
    )


def test_future_timestamp_rejected() -> None:
    body = b"{}"
    secret = "shared-secret"
    future_ts = 2_000_000_000
    signature, ts = sign(body, secret, timestamp=future_ts)
    assert (
        verify(
            body,
            secret,
            signature=signature,
            timestamp=ts,
            now=future_ts - DEFAULT_MAX_AGE_SECONDS - 1,
        )
        is False
    )


def test_signature_without_scheme_prefix_rejected() -> None:
    body = b"{}"
    assert verify(body, "secret", signature="justhexnoprefix", timestamp=1) is False


def test_signature_is_constant_time_comparison() -> None:
    """hmac.compare_digest is used — not a substring of the test, just a documented invariant."""
    # If the implementation switches to `==` by accident, someone will read this.
    import inspect

    from app.webhooks import hmac_signing

    source = inspect.getsource(hmac_signing.verify)
    assert "compare_digest" in source
