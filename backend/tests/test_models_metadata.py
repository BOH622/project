"""Sanity tests — metadata loads, all 22 tables register, critical guardrails hold."""
from __future__ import annotations

from app.models import Base


def test_all_canonical_tables_registered() -> None:
    expected = {
        "provider_org",
        "app_user",
        "magic_link_token",
        "impersonation_session",
        "project",
        "quota_segment",
        "invitation",
        "quote",
        "assignment",
        "screener",
        "screener_block",
        "redirect_url",
        "test_exchange",
        "respondent",
        "message_thread",
        "message",
        "action_request",
        "respondent_action",
        "closeout_packet",
        "invoice",
        "notification",
        "outbound_webhook",
        "inbound_webhook",
    }
    actual = set(Base.metadata.tables.keys())
    missing = expected - actual
    extra = actual - expected
    assert not missing, f"missing canonical tables: {missing}"
    assert not extra, f"unexpected extra tables: {extra}"


def test_respondent_has_no_duration_fields() -> None:
    """Guardrail: active_time, total_duration, message_count must never leak into canonical schema."""
    respondent_cols = {c.name for c in Base.metadata.tables["respondent"].columns}
    forbidden = {"active_time_minutes", "total_duration_minutes", "message_count"}
    leaked = respondent_cols & forbidden
    assert not leaked, f"Respondent must not store duration fields. Found: {leaked}"


def test_project_has_no_client_identity_fields() -> None:
    """Guardrail: client_name / client_visible must not exist on the canonical schema."""
    project_cols = {c.name for c in Base.metadata.tables["project"].columns}
    forbidden = {"client_name", "client_visible", "project_length_bid", "project_length_actual_agg"}
    leaked = project_cols & forbidden
    assert not leaked, f"Project must not store client identity or project-length fields. Found: {leaked}"


def test_quota_segment_has_visible_to_providers_toggle() -> None:
    seg_cols = {c.name for c in Base.metadata.tables["quota_segment"].columns}
    assert "visible_to_providers" in seg_cols
