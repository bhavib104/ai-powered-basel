import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "../api/client";
import { ApiError } from "../api/client";
import type { ReconRun, ReconResultRow } from "../api/types";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  fmtNumber,
  PageHeader,
  Spinner,
  StatCard,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const SOURCES = ["SRC-A", "SRC-B"];
const STATUS_FILTERS = [
  { label: "All statuses", value: "" },
  { label: "Matched", value: "MATCHED" },
  { label: "Mismatched", value: "MISMATCHED" },
  { label: "Only in A", value: "SOURCE_ONLY_A" },
  { label: "Only in B", value: "SOURCE_ONLY_B" },
  { label: "Duplicates", value: "DUPLICATE" },
];

const STATUS_TONES: Record<string, "green" | "amber" | "blue" | "slate" | "purple"> = {
  MATCHED: "green",
  MISMATCHED: "amber",
  SOURCE_ONLY_A: "blue",
  SOURCE_ONLY_B: "slate",
  DUPLICATE: "purple",
};

const inputClass =
  "rounded-md border border-slate-300 px-2.5 py-1.5 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none";

function ResultsTable({ run }: { run: ReconRun }) {
  const [statusFilter, setStatusFilter] = useState("");
  const [showAll, setShowAll] = useState(false);

  const { data, loading, error, reload } = useFetch(
    () => api.reconciliationResults(run.id, { status: statusFilter || undefined }),
    [run.id, statusFilter],
  );

  const rows = (data?.items ?? []).slice(0, showAll ? undefined : 100);

  return (
    <Card
      title="Record-level reconciliation results"
      subtitle={`Business keys compared between ${run.source_a} and ${run.source_b}`}
      actions={
        <select className={inputClass} value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setShowAll(false); }}>
          {STATUS_FILTERS.map((item) => (
            <option key={item.value || "all"} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      }
    >
      {error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : loading || !data ? (
        <Spinner label="Loading results…" />
      ) : data.items.length === 0 ? (
        <EmptyState message="No results for this filter." />
      ) : (
        <>
          <Table headers={["Business key", "Status", "Value in A", "Value in B", "Differences"]}>
            {rows.map((row: ReconResultRow) => (
              <tr key={row.id}>
                <td className={`${tdClass} font-medium text-indigo-700`}>{row.business_key}</td>
                <td className={tdClass}>
                  <Badge tone={STATUS_TONES[row.status] ?? "slate"}>{row.status}</Badge>
                </td>
                <td className={tdClass}>
                  <pre className="max-h-24 overflow-auto text-xs">{JSON.stringify(row.source_a_value, null, 1) || "—"}</pre>
                </td>
                <td className={tdClass}>
                  <pre className="max-h-24 overflow-auto text-xs">{JSON.stringify(row.source_b_value, null, 1) || "—"}</pre>
                </td>
                <td className={tdClass}>
                  {row.differences ? (
                    <pre className="max-h-24 overflow-auto text-xs text-amber-700">
                      {JSON.stringify(row.differences, null, 1) || "—"}
                    </pre>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </Table>
          {data.items.length > 100 ? (
            <div className="mt-3 text-sm text-slate-600">
              {showAll ? `${data.items.length} rows shown.` : `Showing first 100 of ${data.items.length} rows.`}{" "}
              <button
                type="button"
                onClick={() => setShowAll((value) => !value)}
                className="font-semibold text-indigo-600 hover:text-indigo-800"
              >
                {showAll ? "Collapse" : "Show all"}
              </button>
            </div>
          ) : null}
        </>
      )}
    </Card>
  );
}

export function ReconciliationPage() {
  const [sourceA, setSourceA] = useState("SRC-A");
  const [sourceB, setSourceB] = useState("SRC-B");
  const [tolerance, setTolerance] = useState("");
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);

  const runs = useFetch(() => api.reconciliationRuns(20), []);
  const selectedRun = runs.data?.items.find((item) => item.id === selectedRunId) ?? runs.data?.items[0] ?? null;

  async function runReconciliation() {
    setRunning(true);
    setNotice(null);
    try {
      const result = await api.reconciliationRun({
        source_a: sourceA,
        source_b: sourceB,
        tolerance: tolerance === "" ? null : Number(tolerance),
      });
      setNotice(
        `Run ${result.run_ref}: ${result.matched} matched, ${result.mismatched} mismatched, ${result.duplicates} duplicates.`,
      );
      runs.reload();
      setSelectedRunId(result.id);
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  const chartData = selectedRun
    ? [
        { name: "Matched", value: selectedRun.matched, color: "#10b981" },
        { name: "Mismatched", value: selectedRun.mismatched, color: "#f59e0b" },
        { name: "Only A", value: selectedRun.source_only_a, color: "#3b82f6" },
        { name: "Only B", value: selectedRun.source_only_b, color: "#94a3b8" },
        { name: "Duplicates", value: selectedRun.duplicates, color: "#8b5cf6" },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Source Reconciliation"
        subtitle="Compare the primary ledger snapshots with the regulatory warehouse by business key and amount."
      />

      <Card title="Reconcile two snapshots" subtitle="Tolerance (optional) lets small amount differences pass as matched">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            Source A
            <select className={inputClass} value={sourceA} onChange={(event) => setSourceA(event.target.value)}>
              {SOURCES.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            Source B
            <select className={inputClass} value={sourceB} onChange={(event) => setSourceB(event.target.value)}>
              {SOURCES.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            Tolerance (currency units)
            <input
              className={inputClass}
              type="number"
              min={0}
              step="0.01"
              value={tolerance}
              onChange={(event) => setTolerance(event.target.value)}
              placeholder="none (exact match)"
            />
          </label>
          <button
            type="button"
            disabled={running || sourceA === sourceB}
            onClick={runReconciliation}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {running ? "Reconciling…" : "Run reconciliation"}
          </button>
        </div>
        {notice ? <p className="mt-3 text-sm text-slate-600">{notice}</p> : null}
      </Card>

      <div className="mt-6">
        {runs.error ? (
          <ErrorState message={runs.error} onRetry={runs.reload} />
        ) : runs.loading || !runs.data ? (
          <Spinner label="Loading reconciliation runs…" />
        ) : runs.data.items.length === 0 ? (
          <EmptyState message="No reconciliation runs yet — run one above." />
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <Card title="Reconciliation runs" padded={false}>
                <ul className="divide-y divide-slate-100">
                  {runs.data.items.map((run) => (
                    <li key={run.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedRunId(run.id)}
                        className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm transition-colors hover:bg-indigo-50/50 ${
                          selectedRun?.id === run.id ? "bg-indigo-50" : ""
                        }`}
                      >
                        <div>
                          <p className="font-semibold text-slate-900">{run.run_ref}</p>
                          <p className="text-xs text-slate-500">
                            {run.source_a} ↔ {run.source_b}
                            {run.tolerance !== "None" ? ` · tol ${run.tolerance}` : ""} · {fmtDate(run.finished_at)}
                          </p>
                        </div>
                        <Badge tone={run.status === "COMPLETED" ? "green" : "amber"}>{run.status}</Badge>
                      </button>
                    </li>
                  ))}
                </ul>
              </Card>

              {selectedRun ? (
                <Card title="Run outcome" subtitle={`Tolerance: ${selectedRun.tolerance === "None" ? "exact match" : selectedRun.tolerance}`}>
                  <div className="grid grid-cols-2 gap-3">
                    <StatCard label="Matched" value={fmtNumber(selectedRun.matched)} tone="green" />
                    <StatCard label="Mismatched" value={fmtNumber(selectedRun.mismatched)} tone="amber" />
                    <StatCard label="Only in A" value={fmtNumber(selectedRun.source_only_a)} tone="blue" />
                    <StatCard label="Only in B" value={fmtNumber(selectedRun.source_only_b)} />
                  </div>
                  <div className="mt-4">
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                          {chartData.map((entry) => (
                            <Cell key={entry.name} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              ) : (
                <Card title="Run outcome">
                  <EmptyState message="Select a run to see its outcome." />
                </Card>
              )}
            </div>

            <div className="mt-6">{selectedRun ? <ResultsTable run={selectedRun} /> : null}</div>
          </>
        )}
      </div>
    </>
  );
}