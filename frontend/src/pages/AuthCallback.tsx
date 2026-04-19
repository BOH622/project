import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { completeAuthCallback } from "@/lib/auth";

export default function AuthCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [state, setState] = useState<"verifying" | "error">("verifying");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setState("error");
      setErrorMessage("no token in URL");
      return;
    }
    completeAuthCallback(token)
      .then((user) => {
        qc.setQueryData(["auth", "me"], user);
        navigate("/projects", { replace: true });
      })
      .catch((err) => {
        setState("error");
        setErrorMessage(err instanceof Error ? err.message : "invalid link");
      });
  }, [params, navigate, qc]);

  if (state === "verifying") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-slate-500">Signing you in...</p>
      </div>
    );
  }
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-sm text-center space-y-3">
        <h1 className="text-xl font-semibold">Sign-in link is invalid</h1>
        <p className="text-sm text-slate-500">{errorMessage}</p>
        <a href="/login" className="inline-block text-brand-600 text-sm hover:underline">
          Request a new link
        </a>
      </div>
    </div>
  );
}
