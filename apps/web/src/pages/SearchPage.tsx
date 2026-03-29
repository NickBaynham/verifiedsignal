import { useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { DEMO_SEARCH_HITS } from "../demo";

type Mode = "keyword" | "semantic" | "hybrid";

export function SearchPage() {
  const [q, setQ] = useState("correlation ice cream");
  const [mode, setMode] = useState<Mode>("keyword");
  const [recent] = useState(["goverment policy", "SOC 2", "shark attacks"]);

  const results = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return DEMO_SEARCH_HITS;
    return DEMO_SEARCH_HITS.filter(
      (h) =>
        h.title.toLowerCase().includes(query) ||
        h.snippet.toLowerCase().includes(query) ||
        (mode !== "keyword" && query.length > 2),
    );
  }, [q, mode]);

  const typoHint = queryLooksLikeTypo(q);

  return (
    <>
      <h1 className="page-title">Search</h1>
      <p className="page-sub">
        <strong>Use Case 5</strong> — keyword / semantic / hybrid modes, filters as pills, and highlighted snippets
        (mock; production: Elasticsearch BM25 + kNN).
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
            Did you mean <button type="button" className="btn btn-ghost" style={{ padding: 0 }} onClick={() => setQ(typoHint)}>{typoHint}</button>?
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
        <div style={{ marginTop: "1rem", display: "flex", flexWrap: "wrap", gap: 6 }}>
          <span className="pill">Factuality ≥ 0.5</span>
          <span className="pill">AI ≤ 0.7</span>
          <span className="pill pill-warn">Appeal to authority</span>
        </div>
      </div>

      <h2 style={{ fontSize: "1.05rem", margin: "1.5rem 0 0.75rem" }}>Results</h2>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {results.map((h) => (
          <li key={h.documentId} className="card" style={{ marginBottom: "0.75rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
              <Link to={`/documents/${h.documentId}`} style={{ fontWeight: 700 }}>
                {h.title}
              </Link>
              <div style={{ display: "flex", gap: 6 }}>
                <span className="pill pill-ok">F {Math.round(h.scores.factuality * 100)}%</span>
                <span className={h.scores.aiProbability >= 0.7 ? "pill pill-danger" : "pill"}>
                  AI {Math.round(h.scores.aiProbability * 100)}%
                </span>
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
      {results.length === 0 ? <p style={{ color: "var(--text-muted)" }}>No mock results for this query.</p> : null}
    </>
  );
}

function queryLooksLikeTypo(q: string): string | null {
  if (q.trim().toLowerCase() === "goverment policy") return "government policy";
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
  return out;
}
