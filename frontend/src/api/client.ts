/**
 * Typed HTTP client for the backend API.
 *
 * Only real endpoints are called.  When the backend is unavailable the
 * helpers throw a descriptive ``ApiError`` so the UI can show an honest
 * error state rather than fake data.
 */
import type {
  AssistantRequestDetail,
  AssistantResponse,
  AuditEvent,
  CalculateRequest,
  DocumentMeta,
  DashboardSummary,
  ExposureDetail,
  ExposureListResponse,
  HealthResponse,
  QualityFindingsResponse,
  QualityRun,
  QualityRunResponse,
  ReconRequest,
  ReconResultsResponse,
  ReconRun,
  RiskResultsResponse,
  RiskRun,
  SearchRequest,
  SearchResponse,
  SimpleList,
} from "./types";

// The backend (uvicorn) listens on IPv4 127.0.0.1 by default, so we default to
// that exact address to avoid IPv6/IPv4 localhost ambiguity in browsers.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  public readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function buildQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        Accept: "application/json",
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
      ...init,
    });
  } catch {
    throw new ApiError(
      `Could not reach the backend at ${API_BASE_URL}. Start it with: .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000`,
    );
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string | Array<{ msg?: string }> };
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        detail = body.detail.map((item) => item.msg ?? JSON.stringify(item)).join("; ");
      }
    } catch {
      // keep the default message
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),

  dashboard: () => request<DashboardSummary>("/api/v1/dashboard/summary"),

  exposures: (params: {
    page?: number;
    page_size?: number;
    search?: string;
    exposure_class?: string;
    rating_grade?: string;
    currency?: string;
    portfolio_code?: string;
    is_defaulted?: boolean;
  }) => request<ExposureListResponse>(`/api/v1/exposures${buildQuery(params)}`),

  exposureDetail: (id: number) =>
    request<ExposureDetail>(`/api/v1/exposures/${id}`),

  riskCalculate: (payload: CalculateRequest) =>
    postJson<RiskRun>("/api/v1/risk/calculate", payload),

  riskRuns: (limit = 50) =>
    request<SimpleList<RiskRun>>(`/api/v1/risk/runs${buildQuery({ limit })}`),

  riskRunResults: (runId: number, params: { status?: string; page?: number; page_size?: number }) =>
    request<RiskResultsResponse>(
      `/api/v1/risk/runs/${runId}/results${buildQuery(params)}`,
    ),

  qualityRun: (scope = "ALL") =>
    postJson<QualityRunResponse>("/api/v1/quality/run", { scope }),

  qualityRuns: (limit = 20) =>
    request<SimpleList<QualityRun>>(`/api/v1/quality/runs${buildQuery({ limit })}`),

  qualityFindings: (params: {
    severity?: string;
    rule_code?: string;
    record_key?: string;
    page?: number;
    page_size?: number;
  }) => request<QualityFindingsResponse>(`/api/v1/quality/findings${buildQuery(params)}`),

  reconciliationRun: (payload: ReconRequest) =>
    postJson<ReconRun>("/api/v1/reconciliation/run", payload),

  reconciliationRuns: (limit = 20) =>
    request<SimpleList<ReconRun>>(`/api/v1/reconciliation/runs${buildQuery({ limit })}`),

  reconciliationResults: (runId: number, params: { status?: string }) =>
    request<ReconResultsResponse>(`/api/v1/reconciliation/runs/${runId}/results${buildQuery(params)}`),

  documents: () => request<SimpleList<DocumentMeta>>("/api/v1/documents"),

  documentSearch: (payload: SearchRequest) =>
    postJson<SearchResponse>("/api/v1/documents/search", payload),

  documentIngest: (form: FormData) =>
    request<DocumentMeta>("/api/v1/documents/ingest", { method: "POST", body: form }),

  assistantQuery: (question: string) =>
    postJson<AssistantResponse>("/api/v1/assistant/query", { question }),

  assistantRequests: (limit = 30) =>
    request<SimpleList<{ id: number; request_ref: string; question: string; provider: string; status: string; answer: string | null; insufficient_evidence: boolean; latency_ms: number | null; created_at: string }>>(
      `/api/v1/assistant/requests${buildQuery({ limit })}`,
    ),

  assistantRequestDetail: (requestRef: string) =>
    request<AssistantRequestDetail>(`/api/v1/assistant/requests/${requestRef}`),

  auditEvents: (eventType?: string, limit = 150) =>
    request<SimpleList<AuditEvent>>(
      `/api/v1/audit/events${buildQuery({ event_type: eventType, limit })}`,
    ),
};