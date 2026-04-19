# UserCue Projects Portal

Provider-facing portal at `projects.tryusercue.com`. Replaces email-based project coordination with UserCue's ~30 provider partners across bid, quote, launch, in-field, and close-out.

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres 16
- **Frontend:** React 18 + TypeScript + Vite + TanStack Query + Tailwind
- **Infra:** AWS ECS Fargate + RDS Postgres + SES + S3 + CloudFront
- **Auth:** magic-link email (signed token, 15-min TTL)

## Design docs

Authoritative specs live in the Operations repo:
- `Operations/docs/plans/2026-04-19-provider-portal-design.md` — skeleton, page-by-page detail, guardrails
- `Operations/docs/plans/2026-04-19-provider-portal-data-dictionary.md` — canonical schema
- `Operations/docs/plans/2026-04-19-provider-portal-build-plan.md` — milestone breakdown

## Local development

**Requirements:**
- Python 3.12 (`brew install python@3.12`)
- Node 20+ (`brew install node`)
- Docker Desktop (for Postgres + docker-compose) OR local Postgres 16 (`brew install postgresql@16`)

**First-time setup:**
```sh
cp .env.example .env     # fill in secrets
make install             # install backend + frontend deps
make db.up               # start Postgres (docker-compose)
make db.migrate          # run Alembic migrations
make seed                # seed sample data
```

**Run dev:**
```sh
make dev                 # backend :8000 + frontend :5173
```

**Test:**
```sh
make test                # backend + frontend
make test.backend
make test.frontend
```

## Repo layout

```
backend/        FastAPI app
  app/
    models/     SQLAlchemy canonical schema (see data dictionary)
    routes/    HTTP endpoints
    auth/      Magic link + impersonation
    events/    Internal event bus
    workers/   Background jobs (webhooks, email)
  alembic/     Migrations
  tests/
frontend/       Vite React
  src/
    pages/     Top-level routes
    components/Shared components
    lib/       API client, utilities
infrastructure/
  terraform/   AWS infra (not applied by CI)
.github/workflows/  CI + staging auto-deploy
docs/adrs/     Architecture decision records
```

## Guardrails (enforced at data layer, not UI — see design doc §7)

- `Respondent.qc_*` returns `null` until `CloseoutPacket.state == 'finalized'`
- No per-respondent duration, active-time, or message-count ever exposed
- `QuotaSegment.visible_to_providers == false` → stripped from API response
- All provider-scoped queries filter by `provider_org_id` unconditionally
- Client identity (`client_name`) does not exist in the provider-visible schema
- Impersonation sessions are read-only and audit-logged
