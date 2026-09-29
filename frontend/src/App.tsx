import { useEffect, useState } from "react";
import { api, isUnauthorized } from "./api";
import Dashboard from "./components/Dashboard";
import LoginForm from "./components/LoginForm";
import type { CurrentUser } from "./types";

type AuthState =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "error"; message: string }
  | { status: "authenticated"; user: CurrentUser };

export default function App() {
  const [auth, setAuth] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    api
      .me()
      .then((user) => setAuth({ status: "authenticated", user }))
      .catch((error: unknown) =>
        setAuth(
          isUnauthorized(error)
            ? { status: "anonymous" }
            : { status: "error", message: error instanceof Error ? error.message : String(error) },
        ),
      );
  }, []);

  const signedOut = () => setAuth({ status: "anonymous" });

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {auth.status === "loading" && <p className="p-8 text-center text-slate-500">Loading…</p>}
      {auth.status === "error" && (
        <p role="alert" className="p-8 text-center text-red-600 dark:text-red-400">
          {auth.message}
        </p>
      )}
      {auth.status === "anonymous" && (
        <LoginForm onLoggedIn={(user) => setAuth({ status: "authenticated", user })} />
      )}
      {auth.status === "authenticated" && <Dashboard user={auth.user} onSignedOut={signedOut} />}
    </div>
  );
}
