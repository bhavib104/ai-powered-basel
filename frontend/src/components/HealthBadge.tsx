import { useEffect, useState } from "react";

import { ApiError, api } from "../api/client";

type State =
  | { kind: "loading" }
  | { kind: "ok"; version: string }
  | { kind: "error"; message: string };

/** Small live indicator showing whether the backend API is reachable. */
export function HealthBadge() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then((h) => {
        if (!cancelled) setState({ kind: "ok", version: h.version });
      })
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.message : "Unknown error";
        if (!cancelled) setState({ kind: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
        <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
        Checking API…
      </span>
    );
  }

  if (state.kind === "error") {
    return (
      <span
        title={state.message}
        className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700"
      >
        <span className="h-2 w-2 rounded-full bg-red-500" />
        API offline
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
      <span className="h-2 w-2 rounded-full bg-emerald-500" />
      API online · v{state.version}
    </span>
  );
}
