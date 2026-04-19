"""HMAC-SHA256 signing for inbound + outbound webhooks.

Format (loosely modelled on Stripe):
    X-Portal-Signature: v1=<hex>
    X-Portal-Timestamp: <unix-seconds>
    X-Portal-Idempotency-Key: <string>

Signing payload: `"{timestamp}.".encode() + raw_body_bytes`
"""
from __future__ import annotations

import hashlib
import hmac
import time

HEADER_SIGNATURE = "X-Portal-Signature"
HEADER_TIMESTAMP = "X-Portal-Timestamp"
HEADER_IDEMPOTENCY = "X-Portal-Idempotency-Key"

SIGNATURE_SCHEME = "v1"
DEFAULT_MAX_AGE_SECONDS = 300  # 5 minutes — rejects replay attacks


def _compute_digest(body: bytes, secret: str, timestamp: int) -> str:
    payload = f"{timestamp}.".encode() + body
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def sign(body: bytes, secret: str, *, timestamp: int | None = None) -> tuple[str, int]:
    """Returns (signature_header_value, timestamp_used)."""
    ts = int(time.time()) if timestamp is None else timestamp
    sig = f"{SIGNATURE_SCHEME}=" + _compute_digest(body, secret, ts)
    return sig, ts


def verify(
    body: bytes,
    secret: str,
    *,
    signature: str,
    timestamp: int,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
    now: int | None = None,
) -> bool:
    """Constant-time signature verification + timestamp freshness check."""
    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > max_age_seconds:
        return False
    if not signature.startswith(f"{SIGNATURE_SCHEME}="):
        return False
    expected = f"{SIGNATURE_SCHEME}=" + _compute_digest(body, secret, timestamp)
    return hmac.compare_digest(signature, expected)
