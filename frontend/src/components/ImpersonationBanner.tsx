import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

/** Red banner visible while a UserCue super-admin is impersonating a provider org. */
export default function ImpersonationBanner() {
  const { data: user } = useAuth();
  const qc = useQueryClient();

  const stop = useMutation({
    mutationFn: () => api("/admin/impersonate/stop", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth", "me"] }),
  });

  if (!user?.is_impersonating) return null;

  return (
    <div className="bg-red-600 text-white text-sm px-4 py-2 flex items-center justify-between sticky top-0 z-50">
      <div>
        <strong>Read-only impersonation.</strong>{" "}
        Viewing org <code className="font-mono">{user.impersonated_org_id}</code>. All write
        actions are blocked.
      </div>
      <button
        onClick={() => stop.mutate()}
        disabled={stop.isPending}
        className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded"
      >
        {stop.isPending ? "Exiting..." : "Exit impersonation"}
      </button>
    </div>
  );
}
