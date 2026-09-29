import { type FormEvent, useState } from "react";
import { ApiError, api, isUnauthorized } from "../api";
import type { CurrentUser } from "../types";

const COOKIE_REJECTED_MESSAGE =
  "Login succeeded but the browser rejected the session cookie. If you are using plain " +
  "HTTP, serve the app over HTTPS or set LSM_COOKIE_SECURE=false.";

export default function LoginForm({ onLoggedIn }: { onLoggedIn: (user: CurrentUser) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
      setSubmitting(false);
      return;
    }
    try {
      // Confirms the browser actually stored the session cookie.
      onLoggedIn(await api.me());
    } catch (err) {
      setError(isUnauthorized(err) ? COOKIE_REJECTED_MESSAGE : "Login failed");
      setSubmitting(false);
    }
  }

  const inputClass =
    "mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 " +
    "focus:border-teal-600 focus:outline-none dark:border-slate-700 dark:bg-slate-800";

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm space-y-4 rounded-xl bg-white p-6 shadow-sm dark:bg-slate-900"
      >
        <h1 className="text-xl font-semibold">Linux Server Manager</h1>
        <label className="block text-sm font-medium">
          Username
          <input
            className={inputClass}
            autoComplete="username"
            required
            maxLength={64}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="block text-sm font-medium">
          Password
          <input
            className={inputClass}
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-teal-700 px-3 py-2 font-medium text-white hover:bg-teal-800 disabled:opacity-60"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
