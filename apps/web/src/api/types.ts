export interface DocumentSummary {
  id: string;
  collection_id: string;
  title: string | null;
  status: string;
  original_filename: string | null;
  content_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentSummary[];
  total: number;
}

export interface DocumentSource {
  id: string;
  document_id: string;
  source_kind: string;
  locator: string;
  mime_type: string | null;
  byte_length: number | null;
  created_at: string;
  updated_at: string;
}

export interface CanonicalScore {
  factuality_score: number | null;
  ai_generation_probability: number | null;
  fallacy_score: number | null;
  confidence_score: number | null;
  scorer_name: string | null;
  scorer_version: string | null;
}

export interface DocumentDetail extends DocumentSummary {
  sources: DocumentSource[];
  body_text: string | null;
  canonical_score?: CanonicalScore | null;
}

export interface PipelineEvent {
  id: string;
  step_index: number;
  event_type: string;
  stage: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface PipelineRun {
  id: string;
  document_id: string;
  status: string;
  stage: string;
  started_at: string | null;
  completed_at: string | null;
  error_detail: Record<string, unknown> | null;
  run_metadata: Record<string, unknown>;
}

export interface DocumentPipelineResponse {
  document_id: string;
  document_status: string;
  run: PipelineRun | null;
  events: PipelineEvent[];
}

export interface FacetBucket {
  key: string | null;
  count: number;
}

export interface CollectionPostgresStats {
  document_count: number;
  scored_documents: number;
  avg_factuality: number | null;
  avg_ai_probability: number | null;
  suspicious_count: number;
}

export interface CollectionAnalyticsResponse {
  collection_id: string;
  index_total: number;
  index_status: string;
  index_message?: string | null;
  facets: Record<string, FacetBucket[]> | null;
  postgres: CollectionPostgresStats;
}

export interface CollectionRow {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  document_count: number;
  created_at: string;
}

export interface CollectionListResponse {
  collections: CollectionRow[];
}

export interface SearchHit {
  document_id: string;
  title: string | null;
  score: number | null;
  snippet: string;
  collection_id?: string;
  ingest_source?: string;
  content_type?: string | null;
  status?: string;
  tags?: string[];
}

export interface SearchResponse {
  query: string;
  limit: number;
  hits: SearchHit[];
  total: number;
  index_status: string;
  message?: string | null;
}

export interface IntakeResponse {
  document_id: string;
  status: string;
  storage_key: string;
  job_id?: string | null;
  enqueue_error?: string | null;
}

export interface UrlIntakeResponse {
  document_id: string;
  status: string;
  source_url: string;
  job_id?: string | null;
  enqueue_error?: string | null;
}
