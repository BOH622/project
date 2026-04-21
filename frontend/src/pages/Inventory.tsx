import { useEffect, useMemo, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import ImpersonationBanner from "@/components/ImpersonationBanner";
import Login from "@/pages/Login";
import Projects from "@/pages/Projects";
import {
  COMMITS,
  EVENT_GROUPS,
  GUARDRAILS,
  SCHEMA_AREAS,
  TASKS,
  TESTS,
} from "@/inventory/data";
import { installInventoryMocks } from "@/inventory/devMocks";

const FAKE_IMPERSONATED_ORG_ID = "6f3e2a1b-8e4d-4c2a-9b1f-a5d7e9c0f1b3";

export default function Inventory() {
  const [isImpersonating, setIsImpersonating] = useState(false);

  useEffect(() => {
    return installInventoryMocks(() => ({
      isImpersonating,
      impersonatedOrgId: FAKE_IMPERSONATED_ORG_ID,
    }));
  }, [isImpersonating]);

  return (
    <div className="min-h-screen bg-slate-50">
      <InventoryHeader />
      <div className="max-w-6xl mx-auto px-6 py-10 space-y-16">
        <LiveComponentsSection
          isImpersonating={isImpersonating}
          onToggleImpersonating={setIsImpersonating}
        />
        <SchemaSection />
        <EventsSection />
        <GuardrailsSection />
        <TestCoverageSection />
        <GitLogSection />
        <TasksSection />
      </div>
    </div>
  );
}

// ---------------- Header ----------------

function InventoryHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="max-w-6xl mx-auto px-6 py-6">
        <p className="text-xs uppercase tracking-wide text-brand-600 font-semibold">
          UserCue Projects Portal
        </p>
        <h1 className="text-3xl font-semibold mt-1">M0 inventory</h1>
        <p className="text-sm text-slate-600 mt-2 max-w-2xl">
          Everything shipped during M0: live components with mocked backend, canonical
          schema, event-bus types, security guardrails, test coverage, and the git log.
        </p>
        <div className="flex gap-6 text-sm text-slate-600 mt-4">
          <Stat label="Tests passing" value="41 / 41" />
          <Stat label="Canonical tables" value={`${SCHEMA_AREAS.reduce((n, a) => n + a.tables.length, 0)}`} />
          <Stat label="Event types" value={`${EVENT_GROUPS.reduce((n, g) => n + g.events.length, 0)}`} />
          <Stat label="M0 tasks" value={`${TASKS.length} / 6`} />
        </div>
      </div>
    </header>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-lg font-semibold text-slate-900">{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}

// ---------------- Live components ----------------

function LiveComponentsSection({
  isImpersonating,
  onToggleImpersonating,
}: {
  isImpersonating: boolean;
  onToggleImpersonating: (v: boolean) => void;
}) {
  return (
    <section>
      <SectionTitle number="1" title="Live components" />
      <p className="text-sm text-slate-600 mb-4">
        The actual components shipped in M0, rendered against mocked auth APIs. Interact
        freely — nothing here hits a real server.
      </p>

      <div className="mb-6 flex items-center gap-3 p-4 bg-white rounded-lg border border-slate-200">
        <span className="text-sm font-medium">Simulate impersonation:</span>
        <button
          onClick={() => onToggleImpersonating(!isImpersonating)}
          className={
            "px-3 py-1 rounded text-sm " +
            (isImpersonating
              ? "bg-red-600 text-white"
              : "bg-slate-200 text-slate-700")
          }
        >
          {isImpersonating ? "Impersonation ACTIVE" : "Impersonation OFF"}
        </button>
        <span className="text-xs text-slate-500">
          Banner appears at the top of the page while active.
        </span>
      </div>

      {isImpersonating && (
        <IsolatedReact>
          <div className="mb-6 border border-slate-200 rounded-lg overflow-hidden">
            <FrameLabel>ImpersonationBanner (rendered at top-of-app in production)</FrameLabel>
            <ImpersonationBanner />
          </div>
        </IsolatedReact>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ComponentFrame title="Login — magic-link request">
          <IsolatedReact>
            <Login />
          </IsolatedReact>
        </ComponentFrame>

        <ComponentFrame title="Projects — empty state">
          <IsolatedReact>
            <Projects />
          </IsolatedReact>
        </ComponentFrame>

        <AuthCallbackFrame />

        <ComponentFrame title="ImpersonationBanner (compact preview)">
          <div className="p-4 bg-slate-100">
            <IsolatedReact>
              <MockBanner />
            </IsolatedReact>
          </div>
        </ComponentFrame>
      </div>
    </section>
  );
}

function AuthCallbackFrame() {
  const [mode, setMode] = useState<"verifying" | "success" | "error">("verifying");

  return (
    <ComponentFrame title="AuthCallback — static preview of each state">
      <div className="p-3 bg-slate-100 border-b border-slate-200 flex gap-2 text-xs">
        {(["verifying", "success", "error"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={
              "px-2 py-1 rounded " +
              (mode === m ? "bg-brand-600 text-white" : "bg-white border border-slate-300")
            }
          >
            {m}
          </button>
        ))}
      </div>
      <IsolatedReact>
        <AuthCallbackVisual mode={mode} />
      </IsolatedReact>
    </ComponentFrame>
  );
}

/** Visual representation of the three AuthCallback states. Matches real component's CSS. */
function AuthCallbackVisual({ mode }: { mode: "verifying" | "success" | "error" }) {
  if (mode === "verifying") {
    return (
      <div className="min-h-[200px] flex items-center justify-center">
        <p className="text-sm text-slate-500">Signing you in...</p>
      </div>
    );
  }
  if (mode === "success") {
    return (
      <div className="min-h-[200px] flex items-center justify-center">
        <p className="text-sm text-green-700">✓ Signed in — redirecting to /projects</p>
      </div>
    );
  }
  return (
    <div className="min-h-[200px] flex items-center justify-center p-6">
      <div className="max-w-sm text-center space-y-3">
        <h1 className="text-xl font-semibold">Sign-in link is invalid</h1>
        <p className="text-sm text-slate-500">bad signature</p>
        <a href="/login" className="inline-block text-brand-600 text-sm hover:underline">
          Request a new link
        </a>
      </div>
    </div>
  );
}

function MockBanner() {
  // Compact preview that uses the real CSS but mocks the auth state.
  return (
    <div className="bg-red-600 text-white text-sm px-4 py-2 flex items-center justify-between rounded">
      <div>
        <strong>Read-only impersonation.</strong>{" "}
        Viewing org <code className="font-mono">{FAKE_IMPERSONATED_ORG_ID}</code>.
      </div>
      <button className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded">Exit impersonation</button>
    </div>
  );
}

function ComponentFrame({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-slate-200 rounded-lg bg-white overflow-hidden">
      <FrameLabel>{title}</FrameLabel>
      {children}
    </div>
  );
}

function FrameLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-100 border-b border-slate-200 px-3 py-1.5 text-xs text-slate-600 font-mono">
      {children}
    </div>
  );
}

/** Isolates a component inside its own TanStack Query provider. No nested Router —
 *  Inventory lives inside the app's BrowserRouter already. Components that need
 *  routing hooks (AuthCallback) are represented here by static visual mocks. */
function IsolatedReact({ children }: { children: React.ReactNode }) {
  const qc = useMemo(() => new QueryClient({ defaultOptions: { queries: { retry: false } } }), []);
  return (
    <div className="bg-slate-50">
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </div>
  );
}

// ---------------- Schema ----------------

function SchemaSection() {
  return (
    <section>
      <SectionTitle number="2" title={`Canonical schema (${SCHEMA_AREAS.reduce((n, a) => n + a.tables.length, 0)} tables)`} />
      <p className="text-sm text-slate-600 mb-4">
        One file per logical area. Every provider-facing query flows through{" "}
        <code className="font-mono text-xs">provider_scoped()</code>.
      </p>
      <div className="space-y-5">
        {SCHEMA_AREAS.map((area) => (
          <div key={area.title} className="bg-white border border-slate-200 rounded-lg p-5">
            <div className="flex items-baseline justify-between mb-3">
              <h3 className="font-semibold">{area.title}</h3>
              <code className="text-xs text-slate-500">{area.file}</code>
            </div>
            <div className="divide-y divide-slate-100">
              {area.tables.map((t) => (
                <div key={t.name} className="py-2 grid grid-cols-1 md:grid-cols-[180px_1fr] gap-2">
                  <code className="text-sm font-mono text-brand-600">{t.name}</code>
                  <div>
                    <div className="text-sm text-slate-700">{t.description}</div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {t.keyColumns.map((c) => (
                        <span key={c} className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------- Events ----------------

function EventsSection() {
  return (
    <section>
      <SectionTitle number="3" title={`Event types (${EVENT_GROUPS.reduce((n, g) => n + g.events.length, 0)} canonical events)`} />
      <p className="text-sm text-slate-600 mb-4">
        Every state change emits one of these onto the bus. Outbound webhook dispatcher
        subscribes as wildcard, so published events auto-fan-out to all matching{" "}
        <code className="font-mono text-xs">outbound_webhook</code> subscribers.
      </p>
      <div className="grid md:grid-cols-2 gap-4">
        {EVENT_GROUPS.map((g) => (
          <div key={g.title} className="bg-white border border-slate-200 rounded-lg p-5">
            <h3 className="font-semibold mb-3">{g.title}</h3>
            <div className="flex flex-wrap gap-1.5">
              {g.events.map((e) => (
                <code key={e} className="text-xs font-mono bg-brand-50 text-brand-700 px-2 py-1 rounded">
                  {e}
                </code>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------- Guardrails ----------------

function GuardrailsSection() {
  return (
    <section>
      <SectionTitle number="4" title="Security guardrails" />
      <p className="text-sm text-slate-600 mb-4">
        Enforced at the data layer, not just the UI. Every guardrail is anchored by a test
        or a chokepoint that cannot be trivially bypassed.
      </p>
      <ul className="space-y-3">
        {GUARDRAILS.map((g, i) => (
          <li
            key={i}
            className="bg-white border border-slate-200 rounded-lg p-4 flex items-start gap-3"
          >
            <span className="text-green-600 text-lg leading-none mt-0.5">✓</span>
            <div>
              <div className="text-sm font-medium text-slate-900">{g.rule}</div>
              <div className="text-xs text-slate-500 mt-1 font-mono">{g.enforcedBy}</div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

// ---------------- Tests ----------------

function TestCoverageSection() {
  const byFile = TESTS.reduce<Record<string, string[]>>((acc, t) => {
    (acc[t.file] ??= []).push(t.name);
    return acc;
  }, {});

  return (
    <section>
      <SectionTitle number="5" title={`Test coverage (${TESTS.length} passing)`} />
      <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-4">
        {Object.entries(byFile).map(([file, names]) => (
          <div key={file}>
            <div className="flex items-baseline justify-between mb-1">
              <code className="text-sm font-mono text-slate-900">{file}</code>
              <span className="text-xs text-slate-500">{names.length} tests</span>
            </div>
            <ul className="space-y-0.5">
              {names.map((n) => (
                <li key={n} className="text-xs font-mono text-slate-700 flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>{n}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------- Git log ----------------

function GitLogSection() {
  return (
    <section>
      <SectionTitle number="6" title="Git log — M0 commits" />
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <ul className="space-y-2">
          {COMMITS.map((c) => (
            <li key={c.sha} className="flex items-start gap-3 font-mono text-sm">
              <code className="text-amber-700">{c.sha}</code>
              <span className="text-slate-700">{c.title}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

// ---------------- Tasks ----------------

function TasksSection() {
  return (
    <section>
      <SectionTitle number="7" title="M0 tasks complete" />
      <ul className="space-y-2">
        {TASKS.map((t) => (
          <li key={t.id} className="bg-white border border-slate-200 rounded-lg p-3 flex items-start gap-3">
            <span className="text-green-600 mt-0.5">✓</span>
            <code className="text-sm font-mono text-slate-500 w-10">{t.id}</code>
            <span className="text-sm text-slate-800">{t.title}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SectionTitle({ number, title }: { number: string; title: string }) {
  return (
    <h2 className="text-xl font-semibold mb-2">
      <span className="text-brand-600 mr-2">{number}.</span>
      {title}
    </h2>
  );
}

