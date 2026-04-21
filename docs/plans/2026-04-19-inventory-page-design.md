# `/inventory` Page — Design

**Date:** 2026-04-19
**Status:** Approved by Brian — proceed to build.

## Purpose

Single dev-only React route that visualizes everything shipped in M0 (Tasks 0.1–0.6) so Brian can see the product in one place before M1 starts. The page boots on the real Vite dev server with a thin mocked backend — no Postgres required.

## Scope

Sections rendered on one scrolling page at `/inventory`:

1. **Header** — project name, "M0 foundations complete", git SHA, test count, GitHub link.
2. **Live Components** — four side-by-side frames rendering real React components:
   - `Login` (real, interactive with mocked submit)
   - `AuthCallback` (mock-driven: toggle between verifying / success / error)
   - `ImpersonationBanner` (toggle shows banner active with fake org UUID)
   - `Projects` (empty state rendering)
3. **Canonical Schema** — 22 tables grouped by area (Auth, Project, Invitation/Quote, Launch, Respondent, Messaging, Actions, Close-out, Notification, Webhooks), key columns listed.
4. **Event types** — 29 canonical events grouped by lifecycle.
5. **Security guardrails** — six data-layer rules from design §7 with ✓ linking to the enforcing test.
6. **Test coverage** — 41 tests grouped by file, all passing.
7. **Git log** — eight M0 commits with short SHA + title.
8. **Tasks complete** — M0 checklist (0.1–0.6).

## Backend mocking

`src/inventory/devMocks.ts` — installs a `fetch()` shim scoped to `/inventory` route only. Intercepts:

- `POST /auth/request` → 200 after 200ms
- `POST /auth/callback` → success path (returns a fake `CurrentUser`) or error path (401) based on whether token string contains "bad"
- `GET /auth/me` → returns a fake user; the fake user's `is_impersonating` flag comes from an in-page state toggle
- `POST /admin/impersonate/stop` → 204, flips toggle

~40 lines. Zero new dependencies.

## Static data

`src/inventory/data.ts` — hardcoded arrays for schema tables, events, tests, commits, guardrails. Data derived by reading the actual source files; stays accurate by keeping this file adjacent to the docs.

## Tests

Three smoke tests (Vitest) in `src/inventory/Inventory.test.tsx`:
- Page renders all eight section headings.
- Impersonation toggle shows and hides the banner.
- Schema section lists all 22 table names.

## Out of scope

- Backend integration (Postgres, real auth flow).
- Styling polish — Tailwind utility classes only.
- Production deploy. The route is dev-only; gated by `import.meta.env.DEV`.
- Route-level auth. It's local-dev only.

## Deliverable

`npm install` run, `npm run dev` booting on `:5173`, preview showing `/inventory` page with all sections visible and live components interactive.
