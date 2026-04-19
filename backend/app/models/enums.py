"""Canonical enum types referenced across models."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class UserStatus(str, enum.Enum):
    pending_invite = "pending_invite"
    active = "active"
    disabled = "disabled"


class ImpersonationScope(str, enum.Enum):
    read_only = "read_only"


class ProjectLifecycleStage(str, enum.Enum):
    quoting = "quoting"
    pre_launch = "pre_launch"
    soft_launch = "soft_launch"
    full_launch = "full_launch"
    paused = "paused"
    closeout = "closeout"
    closed = "closed"


class InvitationState(str, enum.Enum):
    new = "new"
    viewed = "viewed"
    quote_submitted = "quote_submitted"
    quote_revised = "quote_revised"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class DeclineReason(str, enum.Enum):
    infeasible_audience = "infeasible_audience"
    rate_too_low = "rate_too_low"
    timeline_too_tight = "timeline_too_tight"
    capacity = "capacity"
    other = "other"


class QuoteState(str, enum.Enum):
    submitted = "submitted"
    revised = "revised"
    accepted = "accepted"
    declined = "declined"
    withdrawn = "withdrawn"


class AssignmentState(str, enum.Enum):
    pre_launch = "pre_launch"
    testing = "testing"
    soft_launch = "soft_launch"
    full_launch = "full_launch"
    paused = "paused"
    closeout = "closeout"
    closed = "closed"


class ScreenerType(str, enum.Enum):
    file = "file"
    builder = "builder"
    auto_extracted = "auto_extracted"


class ScreenerBlockType(str, enum.Enum):
    single_select = "single_select"
    multi_select = "multi_select"
    numeric = "numeric"
    open_end = "open_end"
    grid = "grid"


class RedirectOutcome(str, enum.Enum):
    complete = "complete"
    terminate = "terminate"
    quota_full = "quota_full"
    quality_rejected = "quality_rejected"
    timeout = "timeout"


class TestOutcome(str, enum.Enum):
    terminated_at_screener = "terminated_at_screener"
    completed = "completed"
    terminated_at_question = "terminated_at_question"


class RespondentStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    terminated = "terminated"
    quota_full = "quota_full"
    timed_out = "timed_out"
    reset_pending = "reset_pending"
    reset_completed = "reset_completed"
    quality_rejected = "quality_rejected"  # only surfaced after closeout flip


class QcStatus(str, enum.Enum):
    accepted = "accepted"
    removed = "removed"


class MessageSource(str, enum.Enum):
    portal = "portal"
    email_inbound = "email_inbound"


class ActionRequestType(str, enum.Enum):
    id_reset = "id_reset"
    invoice_dispute = "invoice_dispute"
    other = "other"
    # Deferred: quota_change, pause, resume, mid_field_bump


class ActionRequestState(str, enum.Enum):
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    resolved = "resolved"


class RespondentActionType(str, enum.Enum):
    followup_interview = "followup_interview"
    clarification_question = "clarification_question"
    # Direct expert outreach is explicitly out of scope.


class RespondentActionState(str, enum.Enum):
    submitted = "submitted"
    in_review = "in_review"
    scheduled = "scheduled"
    completed = "completed"
    rejected = "rejected"


class CloseoutState(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    finalized = "finalized"


class PaymentState(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"


class NotificationEventType(str, enum.Enum):
    new_invitation = "new_invitation"
    quote_accepted = "quote_accepted"
    quote_declined = "quote_declined"
    quote_revision_requested = "quote_revision_requested"
    redirects_published = "redirects_published"
    sl_greenlight = "sl_greenlight"
    fl_greenlight = "fl_greenlight"
    new_message = "new_message"
    reset_resolved = "reset_resolved"
    respondent_action_resolved = "respondent_action_resolved"
    closeout_published = "closeout_published"
    invoice_state_change = "invoice_state_change"
