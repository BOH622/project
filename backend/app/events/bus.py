"""In-process event bus. Sync dispatch for v1; swap for a queue later without changing callers."""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable

from app.events.types import CanonicalEventType, Event

log = logging.getLogger(__name__)

Subscriber = Callable[[Event], Awaitable[None]]
_WILDCARD = "*"


class EventBus:
    """Simple in-memory pub/sub. Module-level singleton `bus` is the canonical instance."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)

    def subscribe(self, event_type: CanonicalEventType | None, handler: Subscriber) -> None:
        """Subscribe to a specific event type, or None to receive every event."""
        key = event_type.value if event_type is not None else _WILDCARD
        self._subscribers[key].append(handler)

    def clear(self) -> None:
        """Test-only: reset all subscriptions."""
        self._subscribers.clear()

    async def publish(self, event: Event) -> None:
        handlers = list(self._subscribers.get(event.type.value, []))
        handlers.extend(self._subscribers.get(_WILDCARD, []))
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                # One bad subscriber never poisons the others.
                log.exception("subscriber failed for %s", event.type.value)


bus = EventBus()
