"""Outbound webhook dispatcher — fans canonical events out to subscribers.

v1: synchronous per-subscriber POST with a 10-second timeout. If volume grows,
swap the inline httpx calls for a queued worker (arq) — the rest of the contract
stays stable because everything flows through the bus.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.events.types import Event
from app.models import OutboundWebhook
from app.webhooks.hmac_signing import HEADER_IDEMPOTENCY, HEADER_SIGNATURE, HEADER_TIMESTAMP, sign

log = logging.getLogger(__name__)
WILDCARD_EVENT = "*"


async def dispatch(event: Event) -> None:
    """Subscribed to the bus. Fetches active webhooks and posts to each."""
    async with SessionFactory() as db:
        subs = await _load_subscribers(db, event)
        for sub in subs:
            await _deliver(db, sub, event)


async def _load_subscribers(db: AsyncSession, event: Event) -> list[OutboundWebhook]:
    stmt = select(OutboundWebhook).where(OutboundWebhook.is_active.is_(True))
    if event.provider_org_id is not None:
        stmt = stmt.where(
            (OutboundWebhook.provider_org_id == event.provider_org_id)
            | (OutboundWebhook.provider_org_id.is_(None))
        )
    rows = (await db.execute(stmt)).scalars().all()
    return [s for s in rows if event.type.value in s.event_types or WILDCARD_EVENT in s.event_types]


async def _deliver(db: AsyncSession, sub: OutboundWebhook, event: Event) -> None:
    body = json.dumps(event.to_json()).encode()
    sig, ts = sign(body, sub.hmac_secret)
    headers = {
        "Content-Type": "application/json",
        HEADER_SIGNATURE: sig,
        HEADER_TIMESTAMP: str(ts),
        HEADER_IDEMPOTENCY: event.idempotency_key,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(sub.url, content=body, headers=headers)
            resp.raise_for_status()
        sub.last_success_at = datetime.now(timezone.utc)
        sub.failure_count = 0
    except Exception as e:  # noqa: BLE001 — dispatcher must be resilient
        sub.last_failure_at = datetime.now(timezone.utc)
        sub.failure_count = (sub.failure_count or 0) + 1
        log.warning("webhook delivery failed %s → %s: %s", event.type.value, sub.url, e)
    await db.commit()
