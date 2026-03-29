/** Types for the UI demo; replace with OpenAPI-generated types when wiring the API. */

export type PipelineStage =
  | "ingest"
  | "extract"
  | "enrich"
  | "score"
  | "index"
  | "finalize";

export interface ScoreDimension {
  id: string;
  label: string;
  value: number;
  rationale: string;
  /** Optional extra line (e.g. model guess for AI). */
  detail?: string;
}

export interface TextSegment {
  text: string;
  highlight?: { fallacyType: string; explanation: string };
}

export interface DemoDocument {
  id: string;
  title: string;
  filename: string;
  status: "complete" | "processing" | "queued" | "failed";
  currentStage?: PipelineStage;
  ingestedAt: string;
  collectionIds: string[];
  /** Reader view: alternating plain and highlighted spans. */
  bodySegments: TextSegment[];
  /** Joined plain text for mock search snippets. */
  body: string;
  scores: ScoreDimension[];
  keywords: { term: string; weight: number }[];
  author?: string;
  sourceDomain?: string;
  isDuplicate?: boolean;
}

export interface DemoCollection {
  id: string;
  name: string;
  documentCount: number;
  updatedAt: string;
}

export interface FallacyBreakdownRow {
  type: string;
  count: number;
}

export interface DomainSourceRow {
  domain: string;
  documents: number;
  avgFactuality: number;
  avgAiRisk: number;
}

export interface TrendPoint {
  month: string;
  avgFactuality: number;
  avgAiProbability: number;
}

export interface CollectionAnalytics {
  collectionId: string;
  kpis: {
    avgFactuality: number;
    avgAiProbability: number;
    avgFallacyScore: number;
    suspiciousCount: number;
  };
  factualityHistogram: { bin: string; count: number }[];
  aiHistogram: { bin: string; count: number }[];
  fallacyBreakdown: FallacyBreakdownRow[];
  trends: TrendPoint[];
  sources: DomainSourceRow[];
}

export interface SearchHit {
  documentId: string;
  title: string;
  snippet: string;
  /** Character offsets within snippet for mock yellow highlight */
  highlightRanges: [number, number][];
  scores: { factuality: number; aiProbability: number };
}

export interface BillingPlan {
  id: string;
  name: string;
  priceLabel: string;
  documentsLimit: number;
  storageGb: number;
  highlighted?: boolean;
}

export interface UsageSnapshot {
  documentsUsed: number;
  documentsLimit: number;
  storageGbUsed: number;
  storageGbLimit: number;
}

export interface InvoiceRow {
  id: string;
  date: string;
  plan: string;
  amount: string;
  status: "paid" | "open";
}

export interface SessionRow {
  id: string;
  browser: string;
  os: string;
  location: string;
  lastActive: string;
  current: boolean;
}
