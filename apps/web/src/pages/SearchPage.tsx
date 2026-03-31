import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { listCollections } from "../api/collections";
import { searchDocuments } from "../api/search";
import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { useDemoData } from "../context/DemoDataContext";
import { isApiBackend } from "../config";
import { DEMO_COLLECTIONS, DEMO_SEARCH_FACETS, DEMO_SEARCH_HITS } from "../demo";
import type { SearchHit as DemoSearchHit } from "../demo/types";
import { SearchFacetsTable, SearchFiltersPanel } from "../components/SearchFiltersPanel";
import type { FacetBucket } from "../api/types";

type Mode = "keyword" | "semantic" | "hybrid";

function parseTagsInput(tagsInput: string): string[] {
  return tagsInput
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function filterDemoHits(
  hits: DemoSearchHit[],
  deleted: ReadonlySet<string>,
  collectionId: string,
  contentType: string,
  status: string,
  ingestSource: "" | "upload" | "url",
  tagList: string[],
): DemoSearchHit[] {
  return hits.filter((h) => {
    if (deleted.has(h.documentId)) return false;
    if (collectionId && h.collectionId !== collectionId) return false;
    const ct = (h.contentType ?? "").toLowerCase();
    if (contentType.trim() && !ct.includes(contentType.trim().toLowerCase())) return false;
    if (status.trim() && (h.status ?? "").toLowerCase() !== status.trim().toLowerCase()) return false;
    if (ingestSource && h.ingestSource !== ingestSource) return false;
    for (const tag of tagList) {
      const want = tag.toLowerCase();
      const ht = (h.tags ?? []).map((t) => t.toLowerCase());
      if (!ht.includes(want)) return false;
    }
    return true;
  });
}

export function SearchPage() {
  const { accessToken } = useAuth();
  const { deletedDocumentIds } = useDemoData();
  const api = isApiBackend();
  const [q, setQ] = useState("correlation ice cream");
  const [mode, setMode] = useState<Mode>("keyword");
  const [recent] = useState(["goverment policy", "SOC 2", "shark attacks"]);

  const [collectionId, setCollectionId] = useState("");
  const [contentType, setContentType] = useState("");
  const [status, setStatus] = useState("");
  const [ingestSource, setIngestSource] = useState<"" | "upload" | "url">("");
  const [tagsInput, setTagsInput] = useState("");
  const [includeFacets, setIncludeFacets] = useState(false);

  const [apiCollections, setApiCollections] = useState<{ id: string; name: string }[]>([]);
  const [apiHits, setApiHits] = useState<
    { document_id: string; title: string | null; snippet: string; score: number | null; status?: string }[]
  >([]);
  const [apiTotal, setApiTotal] = useState(0);
  const [apiIndexStatus, setApiIndexStatus] = useState("");
  const [apiMessage, setApiMessage] = useState<string | null>(null);
  const [apiFacets, setApiFacets] = useState<Record<string, FacetBucket[]> | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(false);

  const tagList = useMemo(() => parseTagsInput(tagsInput), [tagsInput]);

  useEffect(() => {
    if (!api || !accessToken) return;
    let cancelled = false;
    void (async () => {
      try {
        const res = await listCollections(accessToken);
        if (!cancelled) {
          setApiCollections(res.collections.map((c) => ({ id: c.id, name: c.name })));
        }
      } catch {
        if (!cancelled) setApiCollections([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, accessToken]);

  useEffect(() => {
    if (!api || !accessToken) {
      setApiLoading(false);
      return;
    }
    let cancelled = false;
    const t = window.setTimeout(() => {
      void (async () => {
        setApiLoading(true);
        setApiError(null);
        try {
          const res = await searchDocuments(accessToken, {
            q: q.trim(),
            limit: 25,
            collectionId: collectionId || undefined,
            contentType: contentType || undefined,
            status: status || undefined,
            ingestSource: ingestSource || undefined,
            tags: tagList.length ? tagList : undefined,
            includeFacets,
          });
          if (cancelled) return;
          setApiHits(res.hits);
          setApiTotal(res.total);
          setApiIndexStatus(res.index_status);
          setApiMessage(res.message ?? null);
          setApiFacets(res.facets ?? null);
        } catch (e) {
          if (!cancelled) setApiError(e instanceof ApiError ? e.message : "Search failed");
        } finally {
          if (!cancelled) setApiLoading(false);
        }
      })();
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, [api, accessToken, q, collectionId, contentType, status, ingestSource, tagList, includeFacets]);

  const demoCollections = useMemo(() => DEMO_COLLECTIONS.map((c) => ({ id: c.id, name: c.name })), []);

  const filteredDemoHits = useMemo(() => {
    const base = filterDemoHits(
      DEMO_SEARCH_HITS,
      deletedDocumentIds,
      collectionId,
      contentType,
      status,
      ingestSource,
      tagList,
    );
    const query = q.trim().toLowerCase();
    if (!query) return base;
    return base.filter(
      (h) =>
        h.title.toLowerCase().includes(query) ||
        h.snippet.toLowerCase().includes(query) ||
        (mode !== "keyword" && query.length > 2),
    );
  }, [q, mode, deletedDocumentIds, collectionId, contentType, status, ingestSource, tagList]);

  const demoFacetsToShow = useMemo(() => {
    if (!includeFacets) return null;
    return DEMO_SEARCH_FACETS;
  }, [includeFacets]);

  const typoHint = queryLooksLikeTypo(q);

  if (api) {
    return (
      <>
        <h1 className="page-title">Search</h1>
        <p className="page-sub">
          Live <code>GET /api/v1/search</code> with optional filters (<code>collection_id</code>, <code>content_type</code>,{" "}
          <code>status</code>, <code>ingest_source</code>, <code>tags</code>, <code>include_facets</code>). Mode buttons
          (keyword / semantic / hybrid) stay UI-only until the API supports retrieval modes.
        </p>
        {apiIndexStatus ? (
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 0 }}>
            Index: <code>{apiIndexStatus}</code>
            {apiMessage ? ` — ${apiMessage}` : null}
          </p>
        ) : null}

        <div className="card">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: "0.75rem" }}>
            {(["keyword", "semantic", "hybrid"] as const).map((m) => (
              <button key={m} type="button" className={mode === m ? "btn btn-primary" : "btn"} onClick={() => setMode(m)}>
                {m === "keyword" ? "Keyword" : m === "semantic" ? "Semantic" : "Hybrid"}
              </button>
            ))}
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="q">Query</label>
            <input
              id="q"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search library…"
              style={{ width: "100%", maxWidth: "560px" }}
            />
          </div>
          {typoHint ? (
            <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>
              Did you mean{" "}
              <button type="button" className="btn btn-ghost" style={{ padding: 0 }} onClick={() => setQ(typoHint)}>
                {typoHint}
              </button>
              ?
            </p>
          ) : null}
          <div style={{ marginTop: "1rem", display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Recent:</span>
            {recent.map((r) => (
              <button
                key={r}
                type="button"
                className="pill"
                style={{ border: "none", cursor: "pointer" }}
                onClick={() => setQ(r)}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <SearchFiltersPanel
          collections={apiCollections}
          collectionId={collectionId}
          onCollectionId={setCollectionId}
          contentType={contentType}
          onContentType={setContentType}
          status={status}
          onStatus={setStatus}
          ingestSource={ingestSource}
          onIngestSource={setIngestSource}
          tagsInput={tagsInput}
          onTagsInput={setTagsInput}
          includeFacets={includeFacets}
          onIncludeFacets={setIncludeFacets}
        />

        <h2 style={{ fontSize: "1.05rem", margin: "1.5rem 0 0.75rem" }}>Results</h2>
        {apiError ? <p className="error-text">{apiError}</p> : null}
        {apiLoading ? <p style={{ color: "var(--text-muted)" }}>Searching…</p> : null}
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {apiHits.map((h) => (
            <li key={h.document_id} className="card" style={{ marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                <Link to={`/documents/${h.document_id}`} style={{ fontWeight: 700 }}>
                  {h.title || h.document_id}
                </Link>
                <div style={{ display: "flex", gap: 6 }}>
                  {h.score != null ? <span className="pill">score {h.score.toFixed(2)}</span> : null}
                  {h.status ? <span className="pill pill-ok">{h.status}</span> : null}
                </div>
              </div>
              <p style={{ margin: "0.5rem 0 0", fontSize: "0.9rem", color: "var(--text-muted)" }}>{h.snippet || "—"}</p>
              <p style={{ margin: "0.35rem 0 0", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Mode: {mode} (not sent to API)
              </p>
            </li>
          ))}
        </ul>
        {!apiLoading && apiHits.length === 0 && !apiError ? (
          <p style={{ color: "var(--text-muted)" }}>No results.{apiTotal > 0 ? ` (${apiTotal} total)` : ""}</p>
        ) : null}

        <SearchFacetsTable facets={apiFacets} />
      </>
    );
  }

  return (
    <>
      <h1 className="page-title">Search</h1>
      <p className="page-sub">
        <strong>Use Case 5</strong> — mock hits with the same filter dimensions as the API (collection, content type, status,
        ingest source, tags, facet table). Mode toggles adjust mock ranking only.
      </p>

      <div className="card">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: "0.75rem" }}>
          {(["keyword", "semantic", "hybrid"] as const).map((m) => (
            <button key={m} type="button" className={mode === m ? "btn btn-primary" : "btn"} onClick={() => setMode(m)}>
              {m === "keyword" ? "Keyword" : m === "semantic" ? "Semantic" : "Hybrid"}
            </button>
          ))}
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="q-demo">Query</label>
          <input
            id="q-demo"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search library…"
            style={{ width: "100%", maxWidth: "560px" }}
          />
        </div>
        {typoHint ? (
          <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Did you mean{" "}
            <button type="button" className="btn btn-ghost" style={{ padding: 0 }} onClick={() => setQ(typoHint)}>
              {typoHint}
            </button>
            ?
          </p>
        ) : null}
        <div style={{ marginTop: "1rem", display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Recent:</span>
          {recent.map((r) => (
            <button key={r} type="button" className="pill" style={{ border: "none", cursor: "pointer" }} onClick={() => setQ(r)}>
              {r}
            </button>
          ))}
        </div>
      </div>

      <SearchFiltersPanel
        collections={demoCollections}
        collectionId={collectionId}
        onCollectionId={setCollectionId}
        contentType={contentType}
        onContentType={setContentType}
        status={status}
        onStatus={setStatus}
        ingestSource={ingestSource}
        onIngestSource={setIngestSource}
        tagsInput={tagsInput}
        onTagsInput={setTagsInput}
        includeFacets={includeFacets}
        onIncludeFacets={setIncludeFacets}
      />

      <h2 style={{ fontSize: "1.05rem", margin: "1.5rem 0 0.75rem" }}>Results</h2>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {filteredDemoHits.map((h) => (
          <li key={h.documentId} className="card" style={{ marginBottom: "0.75rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
              <Link to={`/documents/${h.documentId}`} style={{ fontWeight: 700 }}>
                {h.title}
              </Link>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <span className="pill pill-ok">F {Math.round(h.scores.factuality * 100)}%</span>
                <span className={h.scores.aiProbability >= 0.7 ? "pill pill-danger" : "pill"}>
                  AI {Math.round(h.scores.aiProbability * 100)}%
                </span>
                {h.ingestSource ? <span className="pill">{h.ingestSource}</span> : null}
              </div>
            </div>
            <p style={{ margin: "0.5rem 0 0", fontSize: "0.9rem", color: "var(--text-muted)" }}>
              {renderSnippet(h.snippet, h.highlightRanges)}
            </p>
            <p style={{ margin: "0.35rem 0 0", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Mode: {mode} (mock ranking)
            </p>
          </li>
        ))}
      </ul>
      {filteredDemoHits.length === 0 ? <p style={{ color: "var(--text-muted)" }}>No mock results for this query.</p> : null}

      <SearchFacetsTable facets={demoFacetsToShow} />
    </>
  );
}

function queryLooksLikeTypo(query: string): string | null {
  if (query.trim().toLowerCase() === "goverment policy") return "government policy";
  return null;
}

function renderSnippet(snippet: string, ranges: [number, number][]): ReactNode {
  if (!ranges.length) return snippet;
  const out: ReactNode[] = [];
  let i = 0;
  ranges
    .slice()
    .sort((a, b) => a[0] - b[0])
    .forEach(([a, b], idx) => {
      if (a > i) out.push(snippet.slice(i, a));
      out.push(
        <mark
          key={idx}
          style={{ background: "var(--highlight-search)", color: "inherit", padding: "0 2px", borderRadius: 2 }}
        >
          {snippet.slice(a, b)}
        </mark>,
      );
      i = b;
    });
  if (i < snippet.length) out.push(snippet.slice(i));
  return out.length ? out : snippet;
}
