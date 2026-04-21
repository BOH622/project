/**
 * Thin fetch mock for the /inventory route — intercepts auth API calls so the
 * real components render against believable data with no backend running.
 *
 * Scope: only intercepts while `active` is true. Calling `install()` wires it;
 * `uninstall()` restores the native fetch. Per-request path match is narrow —
 * any URL we don't recognize falls through to the real fetch.
 */

export type InventoryAuthState = {
  isImpersonating: boolean;
  impersonatedOrgId: string;
};

const FAKE_USER = (state: InventoryAuthState) => ({
  id: "00000000-0000-0000-0000-000000000001",
  email: "brian@tryusercue.com",
  name: "Brian O'Hara",
  org_id: "00000000-0000-0000-0000-0000000000ff",
  role: "admin",
  is_super_admin: true,
  is_impersonating: state.isImpersonating,
  impersonated_org_id: state.isImpersonating ? state.impersonatedOrgId : null,
});

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

let originalFetch: typeof fetch | null = null;

export function installInventoryMocks(
  getState: () => InventoryAuthState,
): () => void {
  if (originalFetch !== null) return () => {}; // already installed
  originalFetch = window.fetch.bind(window);

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    const method = init?.method?.toUpperCase() ?? "GET";

    if (url.endsWith("/auth/me") && method === "GET") {
      await delay(120);
      return Response.json(FAKE_USER(getState()));
    }
    if (url.endsWith("/auth/request") && method === "POST") {
      await delay(200);
      return Response.json({ status: "accepted" }, { status: 202 });
    }
    if (url.endsWith("/auth/callback") && method === "POST") {
      await delay(200);
      const body = init?.body ? JSON.parse(init.body as string) : {};
      if (typeof body.token === "string" && body.token.includes("bad")) {
        return Response.json({ detail: "bad signature" }, { status: 401 });
      }
      return Response.json(FAKE_USER(getState()));
    }
    if (url.endsWith("/auth/logout") && method === "POST") {
      await delay(60);
      return new Response(null, { status: 204 });
    }
    if (url.endsWith("/admin/impersonate/stop") && method === "POST") {
      await delay(80);
      return new Response(null, { status: 204 });
    }

    // Anything else: fall through to real network.
    return originalFetch!(input, init);
  };

  return () => {
    if (originalFetch) {
      window.fetch = originalFetch;
      originalFetch = null;
    }
  };
}
