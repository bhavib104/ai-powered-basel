import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "../api/client";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  fmtMoney,
  fmtNumber,
  PageHeader,
  Spinner,
  StatCard,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "#be123c",
  HIGH: "#f43f5e",
  MEDIUM: "#f59e0b",
  LOW: "#3b82f6",
};

const RECON_COLORS: Record<string, string> = {
  Matched: "#10b981",
  Mismatched: "#f59e0b",
  "Only A": "#3b82f6",
  "Only B": "#94a3b8",
  Duplicates: "#8b5cf6",
};

export function DashboardPage() {
  const { data, loading, error, reload } = useFetch(() => api.dashboard(), []);

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (loading || !data) return <Spinner label="Loading dashboard…" />;

  const { exposures, rwa, data_quality: dq, reconciliation, documents, recent_runs } = data;
  const dqSummary = dq?.summary;
  const bySeverity = dqSummary?.by_severity
    ? Object.entries(dqSummary.by_severity).map(([name, value]) => ({ name, value }))
    : [];
  const byRule = dqSummary?.by_rule
    ? Object.entries(dqSummary.by_rule)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => a.name.localeCompare(b.name))
    : [];
  const reconData = reconciliation
    ? [
        { name: "Matched", value: reconciliation.matched },
        { name: "Mismatched", value: reconciliation.mismatched },
        { name: "Only A", value: reconciliation.source_only_a },
        { name: "Only B", value: reconciliation.source_only_b },
        { name: "Duplicates", value: reconciliation.duplicates },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Overview Dashboard"
        subtitle="Portfolio totals and latest engine results, computed live from the seeded database."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Exposures"
          value={fmtNumber(exposures.count)}
          hint={`≈ ${fmtMoney(exposures.total_drawn_amount)} ${exposures.currency} drawn`}
          tone="blue"
        />
        <StatCard
          label="Total RWA"
          value={rwa ? `${fmtMoney(rwa.total_rwa)}` : "—"}
          hint={rwa ? `Run ${rwa.run_ref} · rule ${rwa.rule_version}` : "Run a calculation to populate"}
          tone="purple"
        />
        <StatCard
          label="Calculation coverage"
          value={rwa ? fmtNumber(rwa.calculated + rwa.unsupported) : "—"}
          hint={
            rwa
              ? `${fmtNumber(rwa.calculated)} risk-weighted · ${fmtNumber(rwa.unsupported)} explicitly unsupported`
              : undefined
          }
          tone="green"
        />
        <StatCard
          label="Knowledge base"
          value={fmtNumber(documents.ingested)}
          hint={`${fmtNumber(documents.count)} regulatory documents indexed`}
          tone="amber"
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card
          title="Data quality findings by severity"
          subtitle={dq ? `Latest run ${dq.run_ref} · ${dq.finding_count} findings` : undefined}
        >
          {bySeverity.length === 0 ? (
            <EmptyState message="No data-quality run yet — run checks from the Data Quality page." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={bySeverity} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                  {bySeverity.map((entry) => (
                    <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? "#94a3b8"} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card
          title="Reconciliation breakdown"
          subtitle={reconciliation ? `${reconciliation.source_a} ↔ ${reconciliation.source_b}` : undefined}
        >
          {reconData.length === 0 ? (
            <EmptyState message="No reconciliation run yet — reconcile two snapshots from the Reconciliation page." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={reconData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {reconData.map((entry) => (
                    <Cell key={entry.name} fill={RECON_COLORS[entry.name] ?? "#94a3b8"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Data quality findings by rule" subtitle="Seeded anomalies surfaced by the checks">
          {byRule.length === 0 ? (
            <EmptyState message="No findings available." />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={byRule}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" name="Findings" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Latest run activity" subtitle="Most recent engine executions across every domain">
          <Table headers={["Domain", "Run reference", "Finished at", "Outcome"]}>
            <tr>
              <td className={tdClass}>
                <Badge tone="purple">RWA calculation</Badge>
              </td>
              <td className={tdClass}>{recent_runs.rwa?.[0] ?? "—"}</td>
              <td className={tdClass}>{fmtDate(recent_runs.rwa?.[1])}</td>
              <td className={tdClass}>{rwa ? <Badge tone="purple">{`rule ${rwa.rule_version}`}</Badge> : "—"}</td>
            </tr>
            <tr>
              <td className={tdClass}>
                <Badge tone="red">Data quality</Badge>
              </td>
              <td className={tdClass}>{recent_runs.data_quality?.[0] ?? "—"}</td>
              <td className={tdClass}>{fmtDate(recent_runs.data_quality?.[1])}</td>
              <td className={tdClass}>
                {dq ? (
                  <Badge tone="amber">{`${dq.finding_count} findings`}</Badge>
                ) : (
                  "—"
                )}
              </td>
            </tr>
            <tr>
              <td className={tdClass}>
                <Badge tone="blue">Reconciliation</Badge>
              </td>
              <td className={tdClass}>{recent_runs.reconciliation?.[0] ?? "—"}</td>
              <td className={tdClass}>{fmtDate(recent_runs.reconciliation?.[1])}</td>
              <td className={tdClass}>
                {reconciliation ? (
                  <Badge tone={reconciliation.mismatched === 0 ? "green" : "amber"}>
                    {`${reconciliation.mismatched} mismatches`}
                  </Badge>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          </Table>
        </Card>
      </div>
    </>
  );
}