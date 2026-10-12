/**
 * Response and request types for the backend REST API.
 * These mirror the serialized shapes returned by `app/api/routes/*`.
 */

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  checks: Record<string, string>;
}

export interface PageInfo {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SimpleList<T> {
  items: T[];
}

/* ---------------- Dashboard ---------------- */

export interface ExposureSummaryBlock {
  count: number;
  total_drawn_amount: number;
  currency: string;
}

export interface RwaSummaryBlock {
  run_ref: string;
  rule_version: string;
  total_rwa: number;
  total_eligible_amount: number;
  calculated: number;
  unsupported: number;
}

export interface QualitySummary {
  finding_count: number;
  by_severity: Record<string, number>;
  by_rule: Record<string, number>;
}

export interface DqSummaryBlock {
  run_ref: string;
  finding_count: number;
  summary: QualitySummary | null;
}

export interface ReconSummaryBlock {
  run_ref: string;
  source_a: string;
  source_b: string;
  matched: number;
  mismatched: number;
  source_only_a: number;
  source_only_b: number;
  duplicates: number;
}

export interface DashboardSummary {
  exposures: ExposureSummaryBlock;
  rwa: RwaSummaryBlock | null;
  data_quality: DqSummaryBlock | null;
  reconciliation: ReconSummaryBlock | null;
  documents: { count: number; ingested: number };
  recent_runs: {
    rwa: [string, string] | null;
    data_quality: [string, string] | null;
    reconciliation: [string, string] | null;
  };
}

/* ---------------- Exposures ---------------- */

export interface ExposureListItem {
  id: number;
  exposure_ref: string;
  counterparty: string | null;
  counterparty_type: string | null;
  portfolio_code: string | null;
  exposure_class: string;
  product_type: string;
  currency: string;
  original_amount: number;
  drawn_amount: number;
  undrawn_amount: number;
  issue_date: string;
  maturity_date: string;
  is_defaulted: boolean;
  rating_grade: string;
  source_system: string;
}

export interface ExposureListResponse {
  items: ExposureListItem[];
  page: PageInfo;
}

export interface CollateralLink {
  collateral_ref: string | null;
  collateral_type: string | null;
  allocated_amount: number;
  eligible: boolean;
}

export interface LatestCalculation {
  status: string;
  eligible_amount: number;
  risk_weight: number | null;
  rwa: number | null;
  explanation: Record<string, unknown> | null;
}

export interface ExposureDetail extends ExposureListItem {
  collateral: CollateralLink[];
  collateral_credit?: number;
  latest_calculation?: LatestCalculation;
}

/* ---------------- Risk / RWA ---------------- */

export interface RiskRun {
  id: number;
  run_ref: string;
  rule_version: string;
  as_of_date: string;
  reporting_currency: string;
  status: string;
  exposure_count: number;
  calculated: number;
  unsupported: number;
  total_eligible_amount: number;
  total_rwa: number;
  started_at: string;
  finished_at: string | null;
}

export interface RiskRunResultRow {
  id: number;
  exposure_ref: string;
  exposure_class: string;
  rating_grade: string;
  currency: string;
  original_amount: number;
  amount_reporting: number;
  collateral_credit: number;
  eligible_amount: number;
  risk_weight: number | null;
  rwa: number | null;
  status: string;
  explanation: Record<string, unknown> | null;
}

export interface RiskResultsResponse {
  run_id: number;
  items: RiskRunResultRow[];
  count: number;
}

/* ---------------- Data quality ---------------- */

export interface QualityRun {
  id: number;
  run_ref: string;
  status: string;
  rule_count: number;
  finding_count: number;
  started_at: string;
  finished_at: string | null;
}

export interface QualityRunResponse extends QualityRun {
  summary: QualitySummary;
}

export interface QualityFinding {
  id: number;
  run_id: number;
  rule_code: string;
  severity: string;
  entity_type: string;
  record_key: string;
  field: string | null;
  description: string;
  detected_value: string | null;
  created_at: string;
}

export interface QualityFindingsResponse {
  items: QualityFinding[];
  page: PageInfo;
}

/* ---------------- Reconciliation ---------------- */

export interface ReconRun {
  id: number;
  run_ref: string;
  source_a: string;
  source_b: string;
  tolerance: string;
  status: string;
  matched: number;
  mismatched: number;
  source_only_a: number;
  source_only_b: number;
  duplicates: number;
  started_at: string;
  finished_at: string | null;
}

export interface ReconResultRow {
  id: number;
  business_key: string;
  status: string;
  source_a_value: Record<string, unknown> | null;
  source_b_value: Record<string, unknown> | null;
  differences: Record<string, unknown> | null;
}

export interface ReconResultsResponse {
  run_id: number;
  items: ReconResultRow[];
  count: number;
}

/* ---------------- Documents ---------------- */

export interface DocumentMeta {
  id: number;
  title: string;
  document_identifier: string | null;
  issuing_authority: string | null;
  publication_date: string | null;
  document_version: string | null;
  source_url: string | null;
  file_name: string;
  file_type: string;
  file_checksum: string;
  page_count: number;
  chunk_count: number;
  status: string;
  error_message: string | null;
  is_sample: boolean;
  ingested_at: string;
}

export interface SearchHit {
  chunk_id: number;
  document_id: number;
  document_title: string;
  page: number | null;
  section: string | null;
  snippet: string;
  score: number | null;
}

export interface SearchResponse {
  hits: SearchHit[];
  insufficient_evidence: boolean;
}

/* ---------------- AI Assistant ---------------- */

export interface ToolExecution {
  tool_name: string;
  arguments: Record<string, unknown>;
  status: string;
  result_summary: string | null;
  error: string | null;
  duration_ms: number | null;
}

export interface Citation {
  index: number;
  chunk_id: number;
  document_id: number;
  document_title: string;
  page: number | null;
  section: string | null;
  snippet: string;
  score: number | null;
}

export interface AssistantResponse {
  request_ref: string;
  answer: string;
  citations: Citation[];
  insufficient_evidence: boolean;
  tool_executions: ToolExecution[];
  provider: string;
  model: string | null;
}

export interface AssistantHistoryItem {
  id: number;
  request_ref: string;
  question: string;
  provider: string;
  status: string;
  answer: string | null;
  insufficient_evidence: boolean;
  latency_ms: number | null;
  created_at: string;
}

export interface AssistantRequestDetail extends AssistantHistoryItem {
  model: string | null;
  citations: Citation[];
  error: string | null;
  tool_executions: ToolExecution[];
}

/* ---------------- Audit ---------------- */

export interface AuditEvent {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

/* ---------------- Requests ---------------- */

export interface CalculateRequest {
  rule_version?: string;
  as_of_date?: string | null;
  limit?: number | null;
}

export interface ReconRequest {
  source_a: string;
  source_b: string;
  tolerance?: number | null;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  min_score?: number | null;
}