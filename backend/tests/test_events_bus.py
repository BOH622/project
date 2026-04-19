"""In-memory event bus: subscribe, publish, fan-out, resilience to handler errors."""
from __future__ import annotations

import pytest

from app.events.bus import EventBus
from app.events.types import CanonicalEventType, Event


def _evt(type: CanonicalEventType) -> Event:
    return Event(type=type, idempotency_key="test", payload={"x": 1})


async def test_subscriber_receives_matching_event() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(CanonicalEventType.invitation_published, handler)
    await bus.publish(_evt(CanonicalEventType.invitation_published))

    assert len(received) == 1
    assert received[0].type == CanonicalEventType.invitation_published


async def test_subscriber_does_not_receive_other_event_types() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(CanonicalEventType.invitation_published, handler)
    await bus.publish(_evt(CanonicalEventType.quote_submitted))

    assert received == []


async def test_wildcard_subscriber_receives_all_events() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def wildcard(event: Event) -> None:
        received.append(event)

    bus.subscribe(None, wildcard)
    await bus.publish(_evt(CanonicalEventType.invitation_published))
    await bus.publish(_evt(CanonicalEventType.closeout_published))

    assert len(received) == 2


async def test_subscriber_error_does_not_poison_other_subscribers() -> None:
    bus = EventBus()
    received_by_good: list[Event] = []

    async def bad(_event: Event) -> None:
        raise RuntimeError("I am a bad subscriber")

    async def good(event: Event) -> None:
        received_by_good.append(event)

    bus.subscribe(CanonicalEventType.invitation_published, bad)
    bus.subscribe(CanonicalEventType.invitation_published, good)
    # Must not raise.
    await bus.publish(_evt(CanonicalEventType.invitation_published))
    assert len(received_by_good) == 1


def test_event_to_json_shape() -> None:
    import uuid

    ev = Event(
        type=CanonicalEventType.quote_accepted,
        idempotency_key="abc-123",
        provider_org_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        project_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        payload={"n_commit": 50, "cpi": "120.00"},
    )
    j = ev.to_json()
    assert j["type"] == "quote.accepted"
    assert j["idempotency_key"] == "abc-123"
    assert j["provider_org_id"] == "11111111-1111-1111-1111-111111111111"
    assert j["payload"]["n_commit"] == 50


async def test_bus_clear_removes_subscribers() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(CanonicalEventType.invitation_published, handler)
    bus.clear()
    await bus.publish(_evt(CanonicalEventType.invitation_published))
    assert received == []
