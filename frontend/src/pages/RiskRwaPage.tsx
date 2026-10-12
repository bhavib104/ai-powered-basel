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
import type { RiskRun, RiskRunResultRow } from "../api/types";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  fmtMoney,
  fmtPct,
  PageHeader,
  Spinner,
  StatCard,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const inputClass =
  "rounded-md border border-slate-300 px-2.5 py-1.5 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none";

const STATUS_FILTERS = [
  { label: "All statuses", value: "" },
  { label: "OK", value: "OK" },
  { label: "Unsupported class", value: "UNSUPPORTED_EXPOSURE_CLASS" },
  { label: "Unsupported rating", value: "UNSUPPORTED_RATING" },
  { label: "No applicable rule", value: "NO_APPLICABLE_RULE" },
  { label: "Invalid input", value: "INVALID_INPUT" },
];

function ResultsTable({ run }: { run: RiskRun }) {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data, loading, error, reload } = useFetch(
    () =>
      api.riskRunResults(run.id, {
        status: statusFilter || undefined,
        page,
        page_size: 100,
      }),
    [run.id, statusFilter, page],
  );

  return (
    <Card
      title="Exposure-level calculation breakdown"
      subtitle={`Run ${run.run_ref} · ${data ? `${data.items.length} rows shown` : "loading"}`}
      actions={
        <select className={inputClass} value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
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
        <Spinner label="Loading breakdown…" />
      ) : data.items.length === 0 ? (
        <EmptyState message="No breakdown rows for this filter." />
      ) : (
        <>
          <Table
            headers={[
              "Exposure",
              "Class",
              "Rating",
              "Amount (reporting)",
              "Collateral credit",
              "Eligible amount",
              "Risk weight",
              "RWA",
              "Status",
            ]}
          >
            {data.items.map((row: RiskRunResultRow) => (
              <Row key={row.id} row={row} expanded={expandedId === row.id} onToggle={() => setExpandedId(expandedId === row.id ? null : row.id)} />
            ))}
          </Table>
          {data.items.length >= 100 ? (
            <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
              <span>Showing page {page}</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium disabled:opacity-40"
                >
                  ← Prev
                </button>
                <button
                  type="button"
                  onClick={() => setPage(page + 1)}
                  className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium"
                >
                  Next →
                </button>
              </div>
            </div>
          ) : null}
        </>
      )}
    </Card>
  );
}

function Row({
  row,
  expanded,
  onToggle,
}: {
  row: RiskRunResultRow;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr onClick={onToggle} className={`cursor-pointer transition-colors hover:bg-indigo-50/50 ${expanded ? "bg-indigo-50" : ""}`}>
        <td className={`${tdClass} font-medium text-indigo-700`}>{row.exposure_ref}</td>
        <td className={tdClass}>{row.exposure_class}</td>
        <td className={tdClass}>{row.rating_grade}</td>
        <td className={tdClass}>{fmtMoney(row.amount_reporting)}</td>
        <td className={tdClass}>{fmtMoney(row.collateral_credit)}</td>
        <td className={tdClass}>{fmtMoney(row.eligible_amount)}</td>
        <td className={tdClass}>{fmtPct(row.risk_weight)}</td>
        <td className={tdClass}>{fmtMoney(row.rwa)}</td>
        <td className={tdClass}>
          <Badge tone={row.status === "OK" ? "green" : "red"}>{row.status}</Badge>
        </td>
      </tr>
      {expanded ? (
        <tr>
          <td colSpan={9} className="bg-slate-50 px-3 py-3">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Explanation</p>
            <pre className="max-h-48 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
              {JSON.stringify(row.explanation, null, 2)}
            </pre>
          </td>
        </tr>
      ) : null}
    </>
  );
}

export function RiskRwaPage() {
  const [ruleVersion, setRuleVersion] = useState("2024.1");
  const [asOf, setAsOf] = useState("");
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);

  const runs = useFetch(() => api.riskRuns(50), []);
  const selectedRun = runs.data?.items.find((item) => item.id === selectedRunId) ?? runs.data?.items[0] ?? null;

  async function runCalculation() {
    setRunning(true);
    setNotice(null);
    try {
      const result = await api.riskCalculate({
        rule_version: ruleVersion || undefined,
        as_of_date: asOf || null,
      });
      setNotice(`Run ${result.run_ref} finished: ${result.calculated} risk-weighted, ${result.unsupported} unsupported.`);
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
        { name: "Calculated (OK)", value: selectedRun.calculated },
        { name: "Unsupported", value: selectedRun.unsupported },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Risk & RWA Calculation"
        subtitle="Deterministic risk-weight assignment with auditable, per-exposure explanations."
      />

      <Card title="Run a new calculation" subtitle="Applies the selected rule version to every exposure in the register">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            Rule version
            <input
              className={inputClass}
              value={ruleVersion}
              onChange={(event) => setRuleVersion(event.target.value)}
              placeholder="2024.1"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            As-of date (optional)
            <input className={inputClass} type="date" value={asOf} onChange={(event) => setAsOf(event.target.value)} />
          </label>
          <button
            type="button"
            disabled={running}
            onClick={runCalculation}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {running ? "Calculating…" : "Run calculation"}
          </button>
        </div>
        {notice ? <p className="mt-3 text-sm text-slate-600">{notice}</p> : null}
      </Card>

      <div className="mt-6">
        {runs.error ? (
          <ErrorState message={runs.error} onRetry={runs.reload} />
        ) : runs.loading || !runs.data ? (
          <Spinner label="Loading calculation runs…" />
        ) : runs.data.items.length === 0 ? (
          <EmptyState message="No calculation runs yet — run one above." />
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <Card title="Calculation runs" subtitle="Click a run to inspect its breakdown" padded={false}>
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
                            rule {run.rule_version} · {fmtDate(run.finished_at)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge tone={run.status === "COMPLETED" ? "green" : "amber"}>{run.status}</Badge>
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              </Card>

              {selectedRun ? (
                <Card title="Run outcome" subtitle={`Reporting currency ${selectedRun.reporting_currency}`}>
                  <div className="grid grid-cols-2 gap-3">
                    <StatCard label="Total RWA" value={fmtMoney(selectedRun.total_rwa)} tone="purple" />
                    <StatCard
                      label="Total eligible amount"
                      value={fmtMoney(selectedRun.total_eligible_amount)}
                    />
                    <StatCard label="Risk-weighted" value={String(selectedRun.calculated)} hint={`of ${selectedRun.exposure_count} exposures`} tone="green" />
                    <StatCard label="Unsupported" value={String(selectedRun.unsupported)} hint="Explicit non-guessed outcomes" tone="red" />
                  </div>
                  {chartData.length === 2 ? (
                    <div className="mt-4">
                      <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                            {chartData.map((entry) => (
                              <Cell key={entry.name} fill={entry.name === "Calculated (OK)" ? "#10b981" : "#f43f5e"} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : null}
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