import type { ReactNode } from "react";

interface CardProps {
  title: string;
  error: string | null;
  loading: boolean;
  children: ReactNode;
}

export default function Card({ title, error, loading, children }: CardProps) {
  return (
    <section
      aria-label={title}
      className="rounded-xl bg-white p-5 shadow-sm dark:bg-slate-900"
    >
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {title}
      </h2>
      {error && (
        <p role="alert" className="mb-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
      {loading && !error ? <p className="text-sm text-slate-500">Loading…</p> : children}
    </section>
  );
}
