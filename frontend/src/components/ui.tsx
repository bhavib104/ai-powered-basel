/**
 * Small shared UI primitives used across pages: cards, badges, tables,
 * loading/error states, formatters, and a data-fetching hook.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

import { ApiError } from "../api/client";

/* ---------------- Formatters ---------------- */

export function fmtMoney(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

export function fmtNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

export function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ---------------- Badges ---------------- */

export type Tone = "slate" | "green" | "red" | "amber" | "blue" | "purple";

const TONE_CLASSES: Record<Tone, string> = {
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
  green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  red: "bg-rose-50 text-rose-700 ring-rose-200",
  amber: "bg-amber-50 text-amber-800 ring-amber-200",
  blue: "bg-blue-50 text-blue-700 ring-blue-200",
  purple: "bg-violet-50 text-violet-700 ring-violet-200",
};

export function Badge({ tone = "slate", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}

export function severityTone(severity: string | null | undefined): Tone {
  switch (severity) {
    case "CRITICAL":
    case "HIGH":
      return "red";
    case "MEDIUM":
      return "amber";
    case "LOW":
      return "blue";
    default:
      return "slate";
  }
}

export function statusTone(status: string | null | undefined): Tone {
  if (!status) return "slate";
  const upper = status.toUpperCase();
  if (upper.startsWith("OK") || upper === "MATCHED" || upper === "INGESTED" || upper === "COMPLETED") {
    return "green";
  }
  if (upper.startsWith("MISMATCH") || upper.startsWith("SOURCE_ONLY") || upper.startsWith("DUPLICATE")) {
    return "amber";
  }
  if (upper.startsWith("UNSUPPORTED") || upper === "FAILED" || upper === "ERROR" || upper === "INVALID_INPUT") {
    return "red";
  }
  return "blue";
}

/* ---------------- Layout ---------------- */

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
      </div>
      {actions}
    </div>
  );
}

export function Card({
  title,
  subtitle,
  actions,
  children,
  className = "",
  padded = true,
}: {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {title || subtitle || actions ? (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
          <div>
            {title ? <h2 className="text-sm font-semibold text-slate-900">{title}</h2> : null}
            {subtitle ? <p className="text-xs text-slate-500">{subtitle}</p> : null}
          </div>
          {actions}
        </header>
      ) : null}
      <div className={padded ? "p-4" : ""}>{children}</div>
    </section>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "slate",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: Tone;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${TONE_CLASSES[tone].split(" ")[1]}`}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

/* ---------------- States ---------------- */

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-slate-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center">
      <p className="text-sm font-medium text-rose-700">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

/* ---------------- Table ---------------- */

export const thClass =
  "border-b border-slate-200 bg-slate-50 px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500";
export const tdClass = "border-b border-slate-100 px-3 py-2 text-slate-700";

export function Table({ headers, children }: { headers: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header} className={thClass}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Pagination({
  page,
  pages,
  onPage,
}: {
  page: number;
  pages: number;
  onPage: (page: number) => void;
}) {
  if (pages <= 1) return null;
  return (
    <div className="mt-4 flex items-center justify-between gap-3 text-sm text-slate-600">
      <span>
        Page {page} of {pages}
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium disabled:opacity-40"
        >
          ← Prev
        </button>
        <button
          type="button"
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
          className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium disabled:opacity-40"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

/* ---------------- JSON viewers ---------------- */

export function JsonView({ value, className = "" }: { value: unknown; className?: string }) {
  if (value === null || value === undefined) return <span className="text-slate-400">—</span>;
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return (
    <pre className={`max-h-56 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100 ${className}`}>
      {text}
    </pre>
  );
}

export function keyValueRows(record: Record<string, unknown> | null | undefined) {
  if (!record) return null;
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
      {Object.entries(record).map(([key, value]) => (
        <div key={key} className="flex justify-between gap-4 border-b border-slate-100 py-1">
          <dt className="text-slate-500">{key}</dt>
          <dd className="font-medium text-slate-800">
            {typeof value === "object" && value !== null ? JSON.stringify(value) : String(value ?? "—")}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/* ---------------- Data fetching hook ---------------- */

export function useFetch<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fnRef
      .current()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((value) => value + 1), []);

  return { data, loading, error, reload };
}