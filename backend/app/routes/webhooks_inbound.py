"""Inbound webhook endpoint — UserCue side (and future provider integrations) post here."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models import InboundWebhook
from app.webhooks.hmac_signing import (
    HEADER_IDEMPOTENCY,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    verify,
)

router = APIRouter(prefix="/webhooks/inbound", tags=["webhooks"])


@router.post("/{source}")
async def receive(
    source: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    body = await request.body()
    sig = request.headers.get(HEADER_SIGNATURE, "")
    ts_raw = request.headers.get(HEADER_TIMESTAMP, "")
    idem = request.headers.get(HEADER_IDEMPOTENCY, "")

    if not idem:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing idempotency key")
    try:
        ts = int(ts_raw)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "bad timestamp") from e

    # Idempotency replay: if we've seen this key, return 200 without re-processing.
    existing_stmt = select(InboundWebhook).where(InboundWebhook.idempotency_key == idem)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        return {"status": "replay"}

    sig_valid = verify(body, settings.webhook_hmac_secret, signature=sig, timestamp=ts)

    try:
        parsed = json.loads(body) if body else {}
    except json.JSONDecodeError:
        parsed = {"_raw": body.decode("utf-8", errors="replace")}

    # Always persist for audit, whether valid or not.
    row = InboundWebhook(
        source=source,
        event_type=str(parsed.get("type") or parsed.get("event_type") or "unknown"),
        idempotency_key=idem,
        raw_body=parsed,
        signature_valid=sig_valid,
    )
    db.add(row)
    await db.commit()

    if not sig_valid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad signature")

    # TODO: route to internal handler based on (source, event_type).
    # Each handler translates provider-native payload → canonical Event,
    # then bus.publish(event). For M1 Task 1.5 (UserCue publish_invitation),
    # this is where the handler lives.
    return {"status": "accepted"}
