import type {
  BillingPlan,
  CollectionAnalytics,
  DemoCollection,
  DemoDocument,
  InvoiceRow,
  SearchHit,
  SessionRow,
  UsageSnapshot,
} from "./types";

const colResearch = "c1111111-1111-4111-8111-111111111101";
const colLegal = "c2222222-2222-4222-8222-222222222202";

const policyBriefSegments: DemoDocument["bodySegments"] = [
  {
    text: "Recent policy changes have been widely praised by independent experts. ",
  },
  {
    text: "Everyone knows that this agency has never made a mistake in its entire history.",
    highlight: {
      fallacyType: "Appeal to popularity / bandwagon",
      explanation:
        "Universal claim without evidence; classic rhetorical pressure instead of verifiable facts.",
    },
  },
  {
    text: " The published dataset shows a ",
  },
  {
    text: "correlation between ice cream sales and shark attacks",
    highlight: {
      fallacyType: "False causality (implied)",
      explanation:
        "Confounding variables (summer) would be required before drawing causal conclusions.",
    },
  },
  {
    text: ", which stakeholders should interpret cautiously.\n\n",
  },
  {
    text: "According to unnamed sources at the highest levels, the program is 100% effective.",
    highlight: {
      fallacyType: "Appeal to authority (anonymous)",
      explanation:
        "Unverifiable appeals to authority weaken provenance and factuality assessments.",
    },
  },
  {
    text: " Cross-checking against primary filings remains essential.",
  },
];

const policyBriefBody = policyBriefSegments.map((s) => s.text).join("");

export const DEMO_DOCUMENTS: DemoDocument[] = [
  {
    id: "d1000000-0000-4000-8000-000000000001",
    title: "Policy brief — summer outreach pilot",
    filename: "policy-brief-summer.pdf",
    status: "complete",
    ingestedAt: "2026-03-20T14:22:00Z",
    collectionIds: [colResearch],
    bodySegments: policyBriefSegments,
    body: policyBriefBody,
    scores: [
      {
        id: "factuality",
        label: "Factuality confidence",
        value: 0.62,
        rationale:
          "Mixed: some claims align with public records; several sentences rely on unverifiable assertions.",
      },
      {
        id: "ai",
        label: "AI generation probability",
        value: 0.81,
        rationale:
          "High perplexity regularity and generic transition phrases suggest LLM-assisted drafting.",
        detail: "Model guess: family GPT-class, mixed human edits",
      },
      {
        id: "fallacy",
        label: "Logical fallacy risk",
        value: 0.74,
        rationale:
          "Multiple passages exhibit bandwagon, implied causality, and weak authority appeals.",
      },
      {
        id: "pseudo",
        label: "Pseudoscience indicators",
        value: 0.22,
        rationale: "Limited terminology associated with pseudoscientific frameworks.",
      },
      {
        id: "fiction",
        label: "Fictional content likelihood",
        value: 0.18,
        rationale: "Reads as opinion/policy analysis rather than narrative fiction.",
      },
      {
        id: "provenance",
        label: "Source provenance",
        value: 0.45,
        rationale:
          "Author and agency identifiable; anonymous sourcing reduces provenance score.",
      },
      {
        id: "consistency",
        label: "Internal consistency",
        value: 0.58,
        rationale: "Some sections contradict the cautious tone elsewhere in the document.",
      },
      {
        id: "citations",
        label: "Citation quality",
        value: 0.51,
        rationale: "Few explicit citations to primary sources; heavy reliance on secondary summaries.",
      },
    ],
    keywords: [
      { term: "policy", weight: 0.92 },
      { term: "dataset", weight: 0.81 },
      { term: "correlation", weight: 0.77 },
      { term: "stakeholders", weight: 0.64 },
      { term: "agency", weight: 0.61 },
    ],
    author: "J. Rivera",
    sourceDomain: "internal.policy.example",
  },
  {
    id: "d1000000-0000-4000-8000-000000000002",
    title: "Vendor security questionnaire (Q1)",
    filename: "vendor-sec-q1.docx",
    status: "complete",
    ingestedAt: "2026-03-18T09:05:00Z",
    collectionIds: [colLegal],
    bodySegments: [
      {
        text: "The vendor states SOC 2 Type II is in progress with expected completion next quarter. ",
      },
      {
        text: "No known breaches have ever occurred.",
        highlight: {
          fallacyType: "Unqualified absolute",
          explanation: "Absolute claims require dated attestations and scope boundaries.",
        },
      },
      {
        text: " Encryption is used for data in transit and at rest.",
      },
    ],
    body:
      "The vendor states SOC 2 Type II is in progress with expected completion next quarter. No known breaches have ever occurred. Encryption is used for data in transit and at rest.",
    scores: [
      {
        id: "factuality",
        label: "Factuality confidence",
        value: 0.71,
        rationale: "Mostly procedural claims; a few absolutes lack supporting artifacts.",
      },
      {
        id: "ai",
        label: "AI generation probability",
        value: 0.34,
        rationale: "Template-like structure with human-specific dates and named controls.",
        detail: "Model guess: low confidence",
      },
      {
        id: "fallacy",
        label: "Logical fallacy risk",
        value: 0.41,
        rationale: "Minor rhetorical overreach in security assertions.",
      },
      {
        id: "pseudo",
        label: "Pseudoscience indicators",
        value: 0.08,
        rationale: "No pseudoscience markers detected.",
      },
      {
        id: "fiction",
        label: "Fictional content likelihood",
        value: 0.09,
        rationale: "Consistent with questionnaire genre.",
      },
      {
        id: "provenance",
        label: "Source provenance",
        value: 0.68,
        rationale: "Named vendor domain; publication timeline partially explicit.",
      },
      {
        id: "consistency",
        label: "Internal consistency",
        value: 0.72,
        rationale: "Aligned checklist responses across sections.",
      },
      {
        id: "citations",
        label: "Citation quality",
        value: 0.55,
        rationale: "References policies but not always specific control IDs.",
      },
    ],
    keywords: [
      { term: "SOC 2", weight: 0.88 },
      { term: "encryption", weight: 0.79 },
      { term: "breach", weight: 0.7 },
      { term: "vendor", weight: 0.66 },
    ],
    sourceDomain: "vendor.example.com",
  },
  {
    id: "d1000000-0000-4000-8000-000000000003",
    title: "Literature notes — climate summaries",
    filename: "lit-notes.txt",
    status: "processing",
    currentStage: "score",
    ingestedAt: "2026-03-27T11:40:00Z",
    collectionIds: [colResearch],
    bodySegments: [{ text: "Loading analysis…" }],
    body: "Loading analysis…",
    scores: [],
    keywords: [],
  },
];

export const DEMO_COLLECTIONS: DemoCollection[] = [
  {
    id: colResearch,
    name: "Research — 2026 Q1",
    documentCount: 2,
    updatedAt: "2026-03-27T10:00:00Z",
  },
  {
    id: colLegal,
    name: "Legal & vendor",
    documentCount: 1,
    updatedAt: "2026-03-18T09:05:00Z",
  },
];

export const DEMO_DASHBOARD_METRICS = {
  totalDocuments: 128,
  collections: 6,
  avgFactuality: 0.67,
  avgAiProbability: 0.39,
  suspiciousCount: 14,
  recentDocumentIds: [
    "d1000000-0000-4000-8000-000000000003",
    "d1000000-0000-4000-8000-000000000001",
    "d1000000-0000-4000-8000-000000000002",
  ],
};

export const DEMO_ANALYTICS: Record<string, CollectionAnalytics> = {
  [colResearch]: {
    collectionId: colResearch,
    kpis: {
      avgFactuality: 0.66,
      avgAiProbability: 0.52,
      avgFallacyScore: 0.48,
      suspiciousCount: 3,
    },
    factualityHistogram: [
      { bin: "0.0–0.2", count: 0 },
      { bin: "0.2–0.4", count: 1 },
      { bin: "0.4–0.6", count: 2 },
      { bin: "0.6–0.8", count: 4 },
      { bin: "0.8–1.0", count: 1 },
    ],
    aiHistogram: [
      { bin: "0.0–0.2", count: 2 },
      { bin: "0.2–0.4", count: 1 },
      { bin: "0.4–0.6", count: 1 },
      { bin: "0.6–0.8", count: 2 },
      { bin: "0.8–1.0", count: 2 },
    ],
    fallacyBreakdown: [
      { type: "Appeal to authority", count: 12 },
      { type: "False causality", count: 9 },
      { type: "Bandwagon", count: 6 },
      { type: "Straw man", count: 4 },
    ],
    trends: [
      { month: "2025-10", avgFactuality: 0.63, avgAiProbability: 0.31 },
      { month: "2025-11", avgFactuality: 0.65, avgAiProbability: 0.35 },
      { month: "2025-12", avgFactuality: 0.64, avgAiProbability: 0.38 },
      { month: "2026-01", avgFactuality: 0.66, avgAiProbability: 0.41 },
      { month: "2026-02", avgFactuality: 0.67, avgAiProbability: 0.44 },
      { month: "2026-03", avgFactuality: 0.66, avgAiProbability: 0.52 },
    ],
    sources: [
      { domain: "internal.policy.example", documents: 14, avgFactuality: 0.61, avgAiRisk: 0.55 },
      { domain: "arxiv.org", documents: 22, avgFactuality: 0.74, avgAiRisk: 0.22 },
      { domain: "news.example", documents: 31, avgFactuality: 0.58, avgAiRisk: 0.48 },
    ],
  },
  [colLegal]: {
    collectionId: colLegal,
    kpis: {
      avgFactuality: 0.71,
      avgAiProbability: 0.34,
      avgFallacyScore: 0.38,
      suspiciousCount: 1,
    },
    factualityHistogram: [
      { bin: "0.0–0.2", count: 0 },
      { bin: "0.2–0.4", count: 0 },
      { bin: "0.4–0.6", count: 1 },
      { bin: "0.6–0.8", count: 4 },
      { bin: "0.8–1.0", count: 2 },
    ],
    aiHistogram: [
      { bin: "0.0–0.2", count: 3 },
      { bin: "0.2–0.4", count: 2 },
      { bin: "0.4–0.6", count: 1 },
      { bin: "0.6–0.8", count: 1 },
      { bin: "0.8–1.0", count: 0 },
    ],
    fallacyBreakdown: [
      { type: "Unqualified absolute", count: 5 },
      { type: "Ambiguous definition", count: 3 },
    ],
    trends: [
      { month: "2025-10", avgFactuality: 0.69, avgAiProbability: 0.29 },
      { month: "2026-03", avgFactuality: 0.71, avgAiProbability: 0.34 },
    ],
    sources: [
      { domain: "vendor.example.com", documents: 8, avgFactuality: 0.7, avgAiRisk: 0.33 },
    ],
  },
};

export const DEMO_SEARCH_HITS: SearchHit[] = [
  {
    documentId: "d1000000-0000-4000-8000-000000000001",
    title: "Policy brief — summer outreach pilot",
    snippet:
      "…published dataset shows a correlation between ice cream sales and shark attacks, which stakeholders should interpret cautiously…",
    highlightRanges: [
      [40, 51],
      [52, 95],
    ],
    scores: { factuality: 0.62, aiProbability: 0.81 },
  },
  {
    documentId: "d1000000-0000-4000-8000-000000000002",
    title: "Vendor security questionnaire (Q1)",
    snippet:
      "…vendor states SOC 2 Type II is in progress… encryption is used for data in transit and at rest…",
    highlightRanges: [[12, 18]],
    scores: { factuality: 0.71, aiProbability: 0.34 },
  },
];

export const DEMO_PLANS: BillingPlan[] = [
  {
    id: "starter",
    name: "Starter",
    priceLabel: "$49/mo",
    documentsLimit: 200,
    storageGb: 5,
  },
  {
    id: "pro",
    name: "Professional",
    priceLabel: "$199/mo",
    documentsLimit: 2000,
    storageGb: 50,
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    priceLabel: "Contact us",
    documentsLimit: 100000,
    storageGb: 2000,
  },
];

export const DEMO_USAGE: UsageSnapshot = {
  documentsUsed: 128,
  documentsLimit: 2000,
  storageGbUsed: 12.4,
  storageGbLimit: 50,
};

export const DEMO_INVOICES: InvoiceRow[] = [
  { id: "inv_001", date: "2026-03-01", plan: "Professional", amount: "$199.00", status: "paid" },
  { id: "inv_002", date: "2026-02-01", plan: "Professional", amount: "$199.00", status: "paid" },
];

export const DEMO_SESSIONS: SessionRow[] = [
  {
    id: "sess_1",
    browser: "Chrome 134",
    os: "macOS 15",
    location: "Toronto, CA",
    lastActive: "Active now",
    current: true,
  },
  {
    id: "sess_2",
    browser: "Safari 18",
    os: "iOS 18",
    location: "Toronto, CA",
    lastActive: "2h ago",
    current: false,
  },
  {
    id: "sess_3",
    browser: "Firefox 136",
    os: "Windows 11",
    location: "New York, US",
    lastActive: "3d ago",
    current: false,
  },
];

export function getDocumentById(id: string): DemoDocument | undefined {
  return DEMO_DOCUMENTS.find((d) => d.id === id);
}

export function listDocumentsForCollection(collectionId: string): DemoDocument[] {
  return DEMO_DOCUMENTS.filter((d) => d.collectionIds.includes(collectionId));
}
