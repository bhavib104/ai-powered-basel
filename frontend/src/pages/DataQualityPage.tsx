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
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  fmtNumber,
  Pagination,
  PageHeader,
  severityTone,
  Spinner,
  StatCard,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const RULE_CODES = ["DQ-001", "DQ-002", "DQ-003", "DQ-004", "DQ-005", "DQ-006", "DQ-007", "DQ-008", "DQ-009"];
const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const PAGE_SIZE = 100;

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "#be123c",
  HIGH: "#f43f5e",
  MEDIUM: "#f59e0b",
  LOW: "#3b82f6",
};

const inputClass =
  "rounded-md border border-slate-300 px-2.5 py-1.5 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none";

export function DataQualityPage() {
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [severity, setSeverity] = useState("");
  const [ruleCode, setRuleCode] = useState("");
  const [page, setPage] = useState(1);

  const runs = useFetch(() => api.qualityRuns(20), []);
  const findings = useFetch(
    () =>
      api.qualityFindings({
        severity: severity || undefined,
        rule_code: ruleCode || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
    [severity, ruleCode, page],
  );
  const dashboard = useFetch(() => api.dashboard(), [runs.data?.items[0]?.id]);

  async function runChecks() {
    setRunning(true);
    setNotice(null);
    try {
      const result = await api.qualityRun("ALL");
      setNotice(`Run ${result.run_ref} completed with ${result.finding_count} findings across ${result.rule_count} rules.`);
      runs.reload();
      findings.reload();
      setPage(1);
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  const summary = dashboard.data?.data_quality?.summary;
  const bySeverity = summary?.by_severity
    ? Object.entries(summary.by_severity).map(([name, value]) => ({ name, value }))
    : [];
  const byRule = summary?.by_rule
    ? Object.entries(summary.by_rule)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => a.name.localeCompare(b.name))
    : [];
  const latestRun = runs.data?.items[0];

  return (
    <>
      <PageHeader
        title="Data Quality"
        subtitle="Deterministic checks over the exposure and source-snapshot layers, with seeded anomalies for demonstration."
        actions={
          <button
            type="button"
            disabled={running}
            onClick={runChecks}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {running ? "Running checks…" : "Run checks"}
          </button>
        }
      />

      {notice ? (
        <div className="mb-4 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
          {notice}
        </div>
      ) : null}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Latest finding count" value={latestRun ? fmtNumber(latestRun.finding_count) : "—"} hint={latestRun ? latestRun.run_ref : "Run checks to populate"} tone="red" />
        <StatCard label="Rules executed" value={latestRun ? fmtNumber(latestRun.rule_count) : "—"} hint="Versioned rules, all deterministic" />
        <StatCard label="High / critical findings" value={bySeverity.length ? fmtNumber((bySeverity.find((s) => s.name === "HIGH")?.value ?? 0) + (bySeverity.find((s) => s.name === "CRITICAL")?.value ?? 0)) : "—"} tone="red" />
        <StatCard label="Target data layer" value="Master + snapshots" hint="Invalid records split from missing/duplicate anomalies" tone="blue" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card title="Findings by severity" subtitle={summary ? `Latest run ${dashboard.data?.data_quality?.run_ref}` : undefined}>
          {bySeverity.length === 0 ? (
            <EmptyState message="Run the checks to see severity distribution." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={bySeverity}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {bySeverity.map((entry) => (
                    <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? "#94a3b8"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Findings by rule" subtitle="One bar per DQ check - the codes map to documented rules">
          {byRule.length === 0 ? (
            <EmptyState message="Run the checks to see per-rule findings." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={byRule}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Card
          title="Findings register"
          subtitle="Record-level anomalies detected by the latest checks"
          actions={
            <div className="flex gap-2">
              <select className={inputClass} value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
                <option value="">All severities</option>
                {SEVERITIES.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
              <select className={inputClass} value={ruleCode} onChange={(e) => { setRuleCode(e.target.value); setPage(1); }}>
                <option value="">All rules</option>
                {RULE_CODES.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </div>
          }
        >
          {findings.error ? (
            <ErrorState message={findings.error} onRetry={findings.reload} />
          ) : findings.loading || !findings.data ? (
            <Spinner label="Loading findings…" />
          ) : findings.data.items.length === 0 ? (
            <EmptyState message="No findings match the current filters." />
          ) : (
            <>
              <Table
                headers={["When", "Rule", "Severity", "Entity", "Record key", "Field", "Description", "Detected value"]}
              >
                {findings.data.items.map((finding) => (
                  <tr key={finding.id}>
                    <td className={tdClass}>{fmtDate(finding.created_at)}</td>
                    <td className={tdClass}>
                      <Badge tone="purple">{finding.rule_code}</Badge>
                    </td>
                    <td className={tdClass}>
                      <Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge>
                    </td>
                    <td className={tdClass}>{finding.entity_type}</td>
                    <td className={`${tdClass} font-medium`}>{finding.record_key}</td>
                    <td className={tdClass}>{finding.field ?? "—"}</td>
                    <td className={tdClass}>{finding.description}</td>
                    <td className={tdClass}>{finding.detected_value ?? "—"}</td>
                  </tr>
                ))}
              </Table>
              <Pagination page={page} pages={findings.data.page.pages} onPage={setPage} />
            </>
          )}
        </Card>
      </div>
    </>
  );
}