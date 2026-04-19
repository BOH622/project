import { useState } from "react";

import { requestMagicLink } from "@/lib/auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "sent" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("submitting");
    setErrorMessage("");
    try {
      await requestMagicLink(email);
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : "something went wrong");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm bg-white rounded-xl shadow p-8">
        <h1 className="text-2xl font-semibold mb-2">UserCue Projects</h1>
        <p className="text-sm text-slate-500 mb-6">Sign in with a magic link.</p>

        {status === "sent" ? (
          <div className="space-y-3">
            <p className="text-sm">Check your email for a sign-in link.</p>
            <p className="text-xs text-slate-500">The link expires in 15 minutes.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@provider.com"
              className="w-full px-3 py-2 border border-slate-300 rounded-md"
              disabled={status === "submitting"}
            />
            {status === "error" && (
              <p className="text-sm text-red-600">{errorMessage}</p>
            )}
            <button
              type="submit"
              disabled={status === "submitting"}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white py-2 rounded-md font-medium disabled:opacity-60"
            >
              {status === "submitting" ? "Sending..." : "Send magic link"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
