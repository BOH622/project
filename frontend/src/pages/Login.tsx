import { useState } from "react";

/**
 * Magic-link login — submits email, backend sends signed link to that address.
 * Wired in Task 0.4; this is the UI placeholder.
 */
export default function Login() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm bg-white rounded-xl shadow p-8">
        <h1 className="text-2xl font-semibold mb-2">UserCue Projects</h1>
        <p className="text-sm text-slate-500 mb-6">
          Sign in with a magic link.
        </p>
        {submitted ? (
          <p className="text-sm">Check your email for a sign-in link.</p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setSubmitted(true);
            }}
            className="space-y-4"
          >
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@provider.com"
              className="w-full px-3 py-2 border border-slate-300 rounded-md"
            />
            <button
              type="submit"
              className="w-full bg-brand-600 hover:bg-brand-700 text-white py-2 rounded-md font-medium"
            >
              Send magic link
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
