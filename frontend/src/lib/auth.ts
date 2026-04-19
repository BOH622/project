import { api } from "./api";

export type CurrentUser = {
  id: string;
  email: string;
  name: string;
  org_id: string;
  role: string;
  is_super_admin: boolean;
  is_impersonating: boolean;
  impersonated_org_id: string | null;
};

export async function requestMagicLink(email: string): Promise<void> {
  await api("/auth/request", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function completeAuthCallback(token: string): Promise<CurrentUser> {
  return api<CurrentUser>("/auth/callback", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    return await api<CurrentUser>("/auth/me");
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  await api("/auth/logout", { method: "POST" });
}
