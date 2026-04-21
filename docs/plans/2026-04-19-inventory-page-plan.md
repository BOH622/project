# `/inventory` Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship a `/inventory` dev-only React route that renders every component, schema table, event type, test result, and commit from M0 so Brian can see the whole M0 surface in one page.

**Architecture:** New route in existing Vite + React app. Static data imported from a single `.ts` file. Thin `fetch` mock scoped to the `/inventory` route intercepts auth API calls. No backend, no new deps.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind, Vitest.

**Design doc:** `docs/plans/2026-04-19-inventory-page-design.md`

---

### Task 1: Install frontend deps

**Files:** `frontend/package.json` (unchanged), `frontend/node_modules/` (new).

**Steps:**
1. `cd frontend && npm install` — takes 1-2 minutes.
2. Verify: `ls node_modules | wc -l` prints a number > 100.

### Task 2: Static inventory data

**Files:**
- Create: `frontend/src/inventory/data.ts`

**Content:** exported constants — `SCHEMA_AREAS` (10 areas × 22 tables), `EVENT_GROUPS` (4 groups × 29 events), `GUARDRAILS` (6 rules), `TESTS` (41 entries), `COMMITS` (8 M0 commits), `TASKS` (6 M0 tasks).

Source of truth for the values: read from actual code in `backend/app/models/`, `backend/app/events/types.py`, `git log`, etc. during authoring. If anything changes later, update this file.

**Commit:** `m0: inventory page — static data`

### Task 3: Dev mocks

**Files:**
- Create: `frontend/src/inventory/devMocks.ts`

**Behavior:**
- `installInventoryMocks(getImpersonationState)` — patches `window.fetch`.
- Only intercepts when the request URL matches `/auth/request`, `/auth/callback`, `/auth/me`, `/admin/impersonate/stop`. Everything else falls through to real `fetch`.
- `/auth/me` returns a fake `CurrentUser` with `is_impersonating` sourced from `getImpersonationState()` callback so the page toggle controls it.
- `/auth/callback` success if token doesn't contain "bad", 401 otherwise.
- 200 ms artificial delay on each.

**Commit:** `m0: inventory page — dev-only fetch mocks`

### Task 4: Inventory page skeleton

**Files:**
- Create: `frontend/src/pages/Inventory.tsx`
- Modify: `frontend/src/App.tsx` — add `<Route path="/inventory" element={<Inventory />} />` gated by `import.meta.env.DEV`.

**Page structure:**
- `<InventoryHeader />` — title, test count, git SHA, GitHub link.
- `<LiveComponentsSection />` — 4 frames with real components.
- `<SchemaSection />` — renders `SCHEMA_AREAS`.
- `<EventsSection />` — renders `EVENT_GROUPS`.
- `<GuardrailsSection />` — renders `GUARDRAILS` with ✓ chips.
- `<TestCoverageSection />` — renders `TESTS` grouped by file.
- `<GitLogSection />` — renders `COMMITS`.
- `<TasksSection />` — renders `TASKS`.

**Commit:** `m0: inventory page — sections scaffolded`

### Task 5: Live Components frames

**Files:**
- Modify: `frontend/src/pages/Inventory.tsx`

Wrap each of `Login`, `AuthCallback`, `ImpersonationBanner`, `Projects` in a bordered frame with a label. For `AuthCallback`, put a dropdown to switch between "verifying" / "success" / "error" states (uses React state to control query params). For `ImpersonationBanner`, add a toggle button that flips a shared impersonation state.

**Commit:** `m0: inventory page — live components interactive`

### Task 6: Vitest smoke tests

**Files:**
- Create: `frontend/src/inventory/Inventory.test.tsx`

**Tests:**
1. Renders all 8 section headings.
2. Impersonation toggle shows/hides the banner.
3. Schema section lists all 22 canonical tables.

**Commands:**
- `npm test` (from `frontend/`) → all green.

**Commit:** `m0: inventory page — smoke tests`

### Task 7: Boot dev server + verify in preview

**Commands:**
- `npm run dev` from `frontend/` (background process).
- `preview_start` pointing to the Vite URL.
- Click through: Login submit, Projects empty state, toggle impersonation, scroll through schema/events/guardrails/tests/commits.

**Done when:** preview shows all 8 sections, live components interactive, no console errors, all smoke tests pass.

### Task 8: Final commit + push

**Commands:**
- `git push`
- Report completion to Brian.
