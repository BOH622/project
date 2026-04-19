# ADR 0001 — New repo alongside UserCue app, not inside the monorepo

**Date:** 2026-04-19
**Status:** Accepted

## Context

The Provider Portal is a new product surface that sits alongside UserCue's
existing application. We debated (a) adding it as a new frontend/service inside
the UserCue monorepo vs (b) a new standalone repo sharing only a canonical data
contract.

## Decision

Standalone new repo at `usercue-projects-portal`.

## Rationale

- **Security model is disjoint.** Portal is provider-scoped; UserCue app is
  employee-scoped. Keeping the codebases separate makes cross-scope leakage
  physically harder — a bug in UserCue can't accidentally expose provider
  data because they don't share a schema, auth system, or deploy.
- **Deployment independence.** Portal can ship daily without touching
  UserCue's release cadence.
- **No shared state pollution.** UserCue's existing models evolved around
  research ops; the portal's canonical schema is a deliberate reset
  (see data dictionary).
- **Integration still works.** Portal and UserCue communicate via
  HMAC-signed webhooks, not shared DB access. This is exactly the contract
  we need for future provider-native API adapters anyway.

## Consequences

- Provider-scoping tests live in the portal repo, not UserCue's.
- UserCue engineering owns the outbound webhook calls that publish
  invitations, respondent state, closeout flips. They maintain their side;
  we maintain ours.
- Local dev has two repos running, but `docker-compose` scopes nicely.
