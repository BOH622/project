"""Canonical event types emitted by the portal.

Every state change anywhere in the codebase emits an Event onto the bus.
Subscribers (outbound webhooks, internal handlers, notification fan-out) fan it out
from there. This enum is the authoritative list of events external consumers may
subscribe to — adding one is a cross-cutting change; removing one is a breaking change.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class CanonicalEventType(str, enum.Enum):
    # Invitations + quotes
    invitation_published = "invitation.published"
    invitation_viewed = "invitation.viewed"
    invitation_declined = "invitation.declined"
    quote_submitted = "quote.submitted"
    quote_revised = "quote.revised"
    quote_withdrawn = "quote.withdrawn"
    quote_accepted = "quote.accepted"
    quote_declined = "quote.declined"
    quote_revision_requested = "quote.revision_requested"
    # Launch
    assignment_created = "assignment.created"
    redirects_published = "redirects.published"
    test_id_submitted = "test_id.submitted"
    test_id_verified = "test_id.verified"
    sl_requested = "sl.requested"
    sl_granted = "sl.granted"
    fl_requested = "fl.requested"
    fl_granted = "fl.granted"
    # In-field
    respondent_started = "respondent.started"
    respondent_progressed = "respondent.progressed"
    respondent_completed = "respondent.completed"
    respondent_terminated = "respondent.terminated"
    respondent_quota_full = "respondent.quota_full"
    respondent_timed_out = "respondent.timed_out"
    # Actions + messaging
    action_request_submitted = "action_request.submitted"
    action_request_resolved = "action_request.resolved"
    respondent_action_submitted = "respondent_action.submitted"
    respondent_action_resolved = "respondent_action.resolved"
    message_posted = "message.posted"
    # Close-out + billing
    closeout_published = "closeout.published"
    invoice_issued = "invoice.issued"
    invoice_state_changed = "invoice.state_changed"


@dataclass
class Event:
    type: CanonicalEventType
    idempotency_key: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    provider_org_id: uuid.UUID | None = None  # None for system-wide events
    project_id: uuid.UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "idempotency_key": self.idempotency_key,
            "occurred_at": self.occurred_at.isoformat(),
            "provider_org_id": str(self.provider_org_id) if self.provider_org_id else None,
            "project_id": str(self.project_id) if self.project_id else None,
            "payload": self.payload,
        }
