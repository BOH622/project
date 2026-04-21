/**
 * Static inventory data — hand-derived from the real codebase.
 * When the schema/events/tests change, update this file.
 */

export type TableDef = {
  name: string;
  description: string;
  keyColumns: string[];
};

export type SchemaArea = {
  title: string;
  file: string;
  tables: TableDef[];
};

export const SCHEMA_AREAS: SchemaArea[] = [
  {
    title: "Auth & Provider Org",
    file: "app/models/provider.py",
    tables: [
      { name: "provider_org", description: "A partner org (Sermo, Third Bridge, etc.)", keyColumns: ["legal_name", "display_name", "default_currency", "email_mirror_default"] },
      { name: "app_user", description: "User inside a provider org", keyColumns: ["org_id", "email", "role", "status", "is_super_admin"] },
      { name: "magic_link_token", description: "Single-use signed auth token", keyColumns: ["email", "token_hash", "expires_at", "used_at"] },
      { name: "impersonation_session", description: "Super-admin viewing as a provider (read-only)", keyColumns: ["super_admin_user_id", "impersonated_org_id", "scope", "audit_events"] },
    ],
  },
  {
    title: "Project",
    file: "app/models/project.py",
    tables: [
      { name: "project", description: "Shared project record — no client identity ever", keyColumns: ["code", "name", "lifecycle_stage", "loi_minutes", "total_n_target"] },
      { name: "quota_segment", description: "Per-project quota; visible_to_providers gates exposure", keyColumns: ["project_id", "segment_group", "label", "quota_target_n", "visible_to_providers"] },
    ],
  },
  {
    title: "Invitation / Quote / Assignment",
    file: "app/models/invitation.py",
    tables: [
      { name: "invitation", description: "Bid request from UserCue to a provider", keyColumns: ["project_id", "provider_org_id", "state", "bid_brief", "quote_deadline"] },
      { name: "quote", description: "Provider's response with commitments + CPI", keyColumns: ["invitation_id", "n_commit", "cpi", "pm_fee", "state", "revision_history"] },
      { name: "assignment", description: "Accepted quote → working record", keyColumns: ["project_id", "provider_org_id", "state", "team_member_ids"] },
      { name: "screener", description: "Qualifying questions — file upload v1, auto-extract v2", keyColumns: ["type", "file_ref", "source_study_id", "version"] },
      { name: "screener_block", description: "Structured screener question", keyColumns: ["screener_id", "order_index", "type", "question", "logic"] },
    ],
  },
  {
    title: "Launch",
    file: "app/models/launch.py",
    tables: [
      { name: "redirect_url", description: "Complete/Terminate/QuotaFull/QualityRejected/Timeout URLs", keyColumns: ["assignment_id", "outcome", "url_template"] },
      { name: "test_exchange", description: "Provider-submitted test ID + ops verification", keyColumns: ["assignment_id", "test_id_value", "test_outcome", "verified_by_ops"] },
    ],
  },
  {
    title: "Respondent (most security-sensitive)",
    file: "app/models/respondent.py",
    tables: [
      { name: "respondent", description: "Per-ID. NO active_time / total_duration / message_count. QC gated.", keyColumns: ["assignment_id", "provider_user_id", "status", "progression_pct", "termination_question_id", "qc_status (gated)"] },
    ],
  },
  {
    title: "Messaging",
    file: "app/models/messaging.py",
    tables: [
      { name: "message_thread", description: "One per project × provider", keyColumns: ["project_id", "provider_org_id", "email_mirror_enabled"] },
      { name: "message", description: "Portal or inbound-email origin", keyColumns: ["thread_id", "sender_user_id", "body", "source", "email_message_id"] },
    ],
  },
  {
    title: "Actions",
    file: "app/models/actions.py",
    tables: [
      { name: "action_request", description: "v1: id_reset, invoice_dispute. Quota/pause/resume deferred.", keyColumns: ["assignment_id", "type", "payload", "state", "reason_code"] },
      { name: "respondent_action", description: "v2: followup_interview, clarification_question. Ops-gated.", keyColumns: ["assignment_id", "target_respondent_id", "type", "state", "routed_to"] },
    ],
  },
  {
    title: "Close-out & Billing",
    file: "app/models/closeout.py",
    tables: [
      { name: "closeout_packet", description: "QC reveal + final accepted-IDs + outstanding items", keyColumns: ["assignment_id", "state", "published_at", "final_accepted_n", "final_charge_amount"] },
      { name: "invoice", description: "Provider-uploaded invoice + payment tracking", keyColumns: ["closeout_id", "invoice_number", "amount", "po_reference", "payment_state"] },
    ],
  },
  {
    title: "Notifications",
    file: "app/models/notification.py",
    tables: [
      { name: "notification", description: "In-portal feed + email dispatch tracking", keyColumns: ["user_id", "event_type", "payload", "read_at", "email_sent_at"] },
    ],
  },
  {
    title: "Webhooks",
    file: "app/models/webhooks.py",
    tables: [
      { name: "outbound_webhook", description: "Subscriber URL for canonical events (adapter layer)", keyColumns: ["provider_org_id", "url", "event_types", "hmac_secret", "is_active"] },
      { name: "inbound_webhook", description: "Audit log + idempotency for received calls", keyColumns: ["source", "event_type", "idempotency_key", "signature_valid"] },
    ],
  },
];

export type EventGroup = { title: string; events: string[] };

export const EVENT_GROUPS: EventGroup[] = [
  {
    title: "Invitations & Quotes",
    events: [
      "invitation.published",
      "invitation.viewed",
      "invitation.declined",
      "quote.submitted",
      "quote.revised",
      "quote.withdrawn",
      "quote.accepted",
      "quote.declined",
      "quote.revision_requested",
    ],
  },
  {
    title: "Launch",
    events: [
      "assignment.created",
      "redirects.published",
      "test_id.submitted",
      "test_id.verified",
      "sl.requested",
      "sl.granted",
      "fl.requested",
      "fl.granted",
    ],
  },
  {
    title: "In-field & Actions",
    events: [
      "respondent.started",
      "respondent.progressed",
      "respondent.completed",
      "respondent.terminated",
      "respondent.quota_full",
      "respondent.timed_out",
      "action_request.submitted",
      "action_request.resolved",
      "respondent_action.submitted",
      "respondent_action.resolved",
      "message.posted",
    ],
  },
  {
    title: "Close-out & Billing",
    events: ["closeout.published", "invoice.issued", "invoice.state_changed"],
  },
];

export type Guardrail = { rule: string; enforcedBy: string };

export const GUARDRAILS: Guardrail[] = [
  {
    rule: "QC status / reason return null until CloseoutPacket.state == 'finalized'",
    enforcedBy: "Respondent schema gating + close-out flip endpoint",
  },
  {
    rule: "No per-respondent duration, active-time, message-count — ever",
    enforcedBy: "test_respondent_has_no_duration_fields",
  },
  {
    rule: "QuotaSegment.visible_to_providers == false → stripped from API response",
    enforcedBy: "Query-layer filter (wired per tab in M1+)",
  },
  {
    rule: "All provider reads scoped by provider_org_id",
    enforcedBy: "provider_scoped() helper raises on missing org_id — test_provider_scoping",
  },
  {
    rule: "No client_name / client_visible anywhere in provider-visible schema",
    enforcedBy: "test_project_has_no_client_identity_fields",
  },
  {
    rule: "Portal never contacts respondents directly — all respondent actions are ops-gated",
    enforcedBy: "RespondentAction routes through ops review (v2)",
  },
];

export type TestEntry = { file: string; name: string };

export const TESTS: TestEntry[] = [
  { file: "test_health.py", name: "test_healthz_returns_ok" },
  { file: "test_models_metadata.py", name: "test_all_canonical_tables_registered" },
  { file: "test_models_metadata.py", name: "test_respondent_has_no_duration_fields" },
  { file: "test_models_metadata.py", name: "test_project_has_no_client_identity_fields" },
  { file: "test_models_metadata.py", name: "test_quota_segment_has_visible_to_providers_toggle" },
  { file: "test_provider_scoping.py", name: "test_provider_scoped_rejects_missing_org_id" },
  { file: "test_provider_scoping.py", name: "test_provider_scoped_rejects_model_without_scope_column" },
  { file: "test_provider_scoping.py", name: "test_provider_scoped_builds_filtered_query" },
  { file: "test_auth_session.py", name: "test_round_trip_user_only" },
  { file: "test_auth_session.py", name: "test_round_trip_with_impersonation" },
  { file: "test_auth_session.py", name: "test_tampered_cookie_rejected" },
  { file: "test_auth_session.py", name: "test_gibberish_cookie_rejected" },
  { file: "test_auth_tokens.py", name: "test_issue_persists_row_and_returns_signed_token" },
  { file: "test_auth_tokens.py", name: "test_consume_rejects_bad_signature" },
  { file: "test_auth_tokens.py", name: "test_consume_rejects_expired_token" },
  { file: "test_auth_tokens.py", name: "test_consume_rejects_unknown_token" },
  { file: "test_auth_tokens.py", name: "test_consume_rejects_already_used_token" },
  { file: "test_auth_tokens.py", name: "test_consume_success_marks_used_and_returns_email" },
  { file: "test_auth_tokens.py", name: "test_hash_is_deterministic_and_collision_resistant" },
  { file: "test_impersonation_middleware.py", name: "test_write_without_impersonation_cookie_is_not_short_circuited" },
  { file: "test_impersonation_middleware.py", name: "test_write_with_impersonation_cookie_is_rejected" },
  { file: "test_impersonation_middleware.py", name: "test_stop_impersonation_is_exempt" },
  { file: "test_impersonation_middleware.py", name: "test_get_requests_always_pass_middleware" },
  { file: "test_events_bus.py", name: "test_subscriber_receives_matching_event" },
  { file: "test_events_bus.py", name: "test_subscriber_does_not_receive_other_event_types" },
  { file: "test_events_bus.py", name: "test_wildcard_subscriber_receives_all_events" },
  { file: "test_events_bus.py", name: "test_subscriber_error_does_not_poison_other_subscribers" },
  { file: "test_events_bus.py", name: "test_event_to_json_shape" },
  { file: "test_events_bus.py", name: "test_bus_clear_removes_subscribers" },
  { file: "test_webhooks_hmac.py", name: "test_sign_and_verify_round_trip" },
  { file: "test_webhooks_hmac.py", name: "test_signature_with_wrong_secret_rejected" },
  { file: "test_webhooks_hmac.py", name: "test_signature_with_tampered_body_rejected" },
  { file: "test_webhooks_hmac.py", name: "test_expired_timestamp_rejected" },
  { file: "test_webhooks_hmac.py", name: "test_future_timestamp_rejected" },
  { file: "test_webhooks_hmac.py", name: "test_signature_without_scheme_prefix_rejected" },
  { file: "test_webhooks_hmac.py", name: "test_signature_is_constant_time_comparison" },
  { file: "test_webhooks_inbound.py", name: "test_missing_idempotency_key_rejected" },
  { file: "test_webhooks_inbound.py", name: "test_bad_signature_rejected" },
  { file: "test_webhooks_inbound.py", name: "test_valid_signature_accepted" },
  { file: "test_webhooks_inbound.py", name: "test_replay_returns_200_without_processing" },
  { file: "test_webhooks_inbound.py", name: "test_invalid_body_still_persists_and_rejects" },
];

export type Commit = { sha: string; title: string };

export const COMMITS: Commit[] = [
  { sha: "bfada2b", title: "m0: event bus + webhook infra (Task 0.6)" },
  { sha: "b2fd624", title: "m0: super-admin impersonation (Task 0.5)" },
  { sha: "091c005", title: "m0: magic-link auth (Task 0.4)" },
  { sha: "a617dcb", title: "m0: fix UUID assertion in provider-scope test" },
  { sha: "bf6d67b", title: "m0: Terraform infra + GitHub Actions CI/deploy (not applied)" },
  { sha: "1a3d8ed", title: "m0: canonical schema (22 models + initial migration + scope enforcement)" },
  { sha: "ecb3c1e", title: "m0: repo scaffold (FastAPI + Vite React + Postgres)" },
];

export type Task = { id: string; title: string };

export const TASKS: Task[] = [
  { id: "0.1", title: "Repo scaffold — FastAPI + Vite React + Postgres + Makefile + docker-compose" },
  { id: "0.2", title: "Terraform infra + GitHub Actions CI/deploy (scaffolded, not applied)" },
  { id: "0.3", title: "Canonical schema — 22 SQLAlchemy models + Alembic initial migration + scope helper" },
  { id: "0.4", title: "Magic-link auth — signed tokens, session cookies, FastAPI deps, SES sender" },
  { id: "0.5", title: "Super-admin impersonation — read-only middleware, audit logging, banner" },
  { id: "0.6", title: "Event bus + HMAC webhook infra — 29 event types, inbound endpoint, dispatcher" },
];
