import { useState } from "react";

import { api } from "../api/client";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  PageHeader,
  Spinner,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const EVENT_TYPES = ["risk", "data_quality", "reconciliation", "assistant", "document"];

const EVENT_TONES: Record<string, "purple" | "red" | "blue" | "green" | "amber" | "slate"> = {
  risk: "purple",
  data_quality: "red",
  reconciliation: "blue",
  assistant: "green",
  document: "amber",
};

export function AuditPage() {
  const [eventType, setEventType] = useState<string>("");
  const { data, loading, error, reload } = useFetch(
    () => api.auditEvents(eventType || undefined, 200),
    [eventType],
  );

  return (
    <>
      <PageHeader
        title="Audit & Runs"
        subtitle="Append-only audit trail of every engine run, document ingest and assistant exchange. Nothing in this table can be edited or deleted."
        actions={
          <div className="flex flex-wrap gap-1">
            <button
              type="button"
              onClick={() => setEventType("")}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                eventType === "" ? "bg-slate-900 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-300 hover:bg-slate-50"
              }`}
            >
              All
            </button>
            {EVENT_TYPES.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setEventType(eventType === item ? "" : item)}
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  eventType === item ? "bg-slate-900 text-white" : "bg-white text-slate-600 ring-1 ring-inset ring-slate-300 hover:bg-slate-50"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        }
      />

      {error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : loading || !data ? (
        <Spinner label="Loading audit trail…" />
      ) : data.items.length === 0 ? (
        <EmptyState message="No audit events recorded for this filter yet." />
      ) : (
        <Card padded={false}>
          <Table headers={["Timestamp", "Event", "Action", "Entity", "Actor", "Details"]}>
            {data.items.map((event) => (
              <tr key={event.id}>
                <td className={`${tdClass} whitespace-nowrap`}>{fmtDate(event.created_at)}</td>
                <td className={tdClass}>
                  <Badge tone={EVENT_TONES[event.event_type] ?? "slate"}>{event.event_type}</Badge>
                </td>
                <td className={`${tdClass} font-medium`}>{event.action}</td>
                <td className={tdClass}>
                  <span className="text-xs text-slate-500">{event.entity_type}</span>{" "}
                  <span className="font-mono text-xs text-indigo-700">{event.entity_id}</span>
                </td>
                <td className={tdClass}>{event.actor}</td>
                <td className={tdClass}>
                  {event.details ? (
                    <pre className="max-h-24 overflow-auto rounded bg-slate-50 p-1.5 text-[11px]">
                      {JSON.stringify(event.details)}
                    </pre>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </>
  );
}