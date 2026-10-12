import { useState } from "react";

import { api } from "../api/client";
import { ApiError } from "../api/client";
import type {
  AssistantRequestDetail,
  AssistantResponse,
  Citation,
  ToolExecution,
} from "../api/types";
import {
  Badge,
  Card,
  EmptyState,
  fmtDate,
  PageHeader,
  Spinner,
  useFetch,
} from "../components/ui";

interface AnswerViewProps {
  answer: string | null;
  citations: Citation[];
  toolExecutions: ToolExecution[];
  insufficientEvidence: boolean;
  provider?: string;
  model?: string | null;
  requestRef?: string;
  latencyMs?: number | null;
}

function AnswerView({
  answer,
  citations,
  toolExecutions,
  insufficientEvidence,
  provider,
  model,
  requestRef,
  latencyMs,
}: AnswerViewProps) {
  return (
    <div className="space-y-4">
      {insufficientEvidence ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <strong>Insufficient evidence.</strong> No indexed regulatory passage or structured evidence matched this
          question, so the answer below is refrained rather than invented.
        </div>
      ) : null}

      <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-800">
        {answer
          ? answer.split("\n").map((paragraph, index) => <p key={index} className="mb-2 last:mb-0">{paragraph}</p>)
          : <em>No answer produced.</em>}
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {provider ? (
          <Badge tone="blue">{`provider: ${provider}${model ? ` · ${model}` : ""}`}</Badge>
        ) : null}
        {requestRef ? <Badge tone="slate">{requestRef}</Badge> : null}
        {latencyMs !== null && latencyMs !== undefined ? (
          <Badge tone="slate">{`${latencyMs} ms`}</Badge>
        ) : null}
      </div>

      {citations.length > 0 ? (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-900">Citations</h3>
          <ol className="space-y-2">
            {citations.map((citation) => (
              <li key={citation.index} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-900">
                    [{citation.index}] {citation.document_title}
                  </p>
                  <Badge tone="blue">{citation.score !== null ? `${(citation.score * 100).toFixed(1)}%` : "—"}</Badge>
                </div>
                <p className="text-xs text-slate-500">
                  {citation.page !== null ? `Page ${citation.page}` : "No page"}
                  {citation.section ? ` · ${citation.section}` : ""}
                  <span className="ml-1 text-slate-400">(chunk {citation.chunk_id}, doc {citation.document_id})</span>
                </p>
                <p className="mt-1 text-sm text-slate-600">{citation.snippet}…</p>
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      {toolExecutions.length > 0 ? (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-900">Tool executions</h3>
          <ul className="space-y-2">
            {toolExecutions.map((execution, index) => (
              <li key={`${execution.tool_name}-${index}`} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-indigo-700">{execution.tool_name}</p>
                  <div className="flex items-center gap-2">
                    {execution.duration_ms !== null && execution.duration_ms !== undefined ? (
                      <Badge tone="slate">{`${execution.duration_ms} ms`}</Badge>
                    ) : null}
                    <Badge tone={execution.status === "OK" ? "green" : "red"}>{execution.status}</Badge>
                  </div>
                </div>
                <pre className="mt-2 max-h-32 overflow-auto rounded-md bg-slate-900 p-2 text-[11px] text-slate-100">
                  {JSON.stringify(execution.arguments, null, 1)}
                </pre>
                {execution.result_summary ? (
                  <p className="mt-1 text-xs text-slate-500">{execution.result_summary}</p>
                ) : null}
                {execution.error ? <p className="mt-1 text-xs text-rose-600">{execution.error}</p> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssistantResponse | null>(null);
  const [historyDetail, setHistoryDetail] = useState<AssistantRequestDetail | null>(null);

  const history = useFetch(() => api.assistantRequests(30), []);

  async function ask() {
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    setHistoryDetail(null);
    try {
      const response = await api.assistantQuery(trimmed);
      setResult(response);
      setQuestion("");
      history.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory(ref: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setHistoryDetail(await api.assistantRequestDetail(ref));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const view = historyDetail
    ? {
        answer: historyDetail.answer,
        citations: historyDetail.citations,
        toolExecutions: historyDetail.tool_executions,
        insufficientEvidence: historyDetail.insufficient_evidence,
        provider: historyDetail.provider,
        model: historyDetail.model,
        requestRef: historyDetail.request_ref,
        latencyMs: historyDetail.latency_ms,
      }
    : result
      ? {
          answer: result.answer,
          citations: result.citations,
          toolExecutions: result.tool_executions,
          insufficientEvidence: result.insufficient_evidence,
          provider: result.provider,
          model: result.model,
          requestRef: result.request_ref,
          latencyMs: null,
        }
      : null;

  return (
    <>
      <PageHeader
        title="AI Risk Assistant"
        subtitle="Ask questions in plain English. The intent router picks deterministic read-only tools, and every answer is evidence-based with citations or an explicit 'insufficient evidence' response."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <div className="flex flex-col gap-3">
              <textarea
                rows={3}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:border-indigo-500 focus:outline-none"
                placeholder="e.g. What is the total RWA for corporate exposures? Or: what does Basel say about retail mortgages?"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void ask();
                  }
                }}
              />
              <div className="flex items-center justify-between gap-3">
                <button
                  type="button"
                  disabled={loading || !question.trim()}
                  onClick={ask}
                  className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {loading ? "Thinking…" : "Ask"}
                </button>
                <p className="text-xs text-slate-500">Tools are read-only and audited. The LLM never writes to the database.</p>
              </div>
            </div>
          </Card>

          <div className="mt-6">
            {error ? (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
            ) : loading ? (
              <Spinner label="Routing intent and gathering evidence…" />
            ) : view ? (
              <AnswerView {...view} />
            ) : (
              <EmptyState message="Ask a question above. The response will show its tool trail, citations and any insufficient-evidence refusals." />
            )}
          </div>
        </div>

        <Card title="Request history" subtitle="Click a past question to re-open its full answer, citations and tool trail">
          {history.error ? (
            <p className="text-sm text-rose-700">{history.error}</p>
          ) : history.loading || !history.data ? (
            <Spinner label="Loading history…" />
          ) : history.data.items.length === 0 ? (
            <EmptyState message="No questions asked yet in this database." />
          ) : (
            <ul className="space-y-2">
              {history.data.items.map((item) => (
                <li key={item.request_ref}>
                  <button
                    type="button"
                    onClick={() => void loadHistory(item.request_ref)}
                    className={`w-full rounded-lg border px-3 py-2 text-left transition-colors hover:border-indigo-300 hover:bg-indigo-50/50 ${
                      historyDetail?.request_ref === item.request_ref ? "border-indigo-300 bg-indigo-50" : "border-slate-200"
                    }`}
                  >
                    <p className="line-clamp-2 text-sm font-medium text-slate-800">{item.question}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {fmtDate(item.created_at)} · {item.provider}
                      {item.insufficient_evidence ? " · insufficient evidence" : ""}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}