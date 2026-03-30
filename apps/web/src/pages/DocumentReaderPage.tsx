import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { getDocument } from "../api/documents";
import type { DocumentDetail } from "../api/types";
import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { isApiBackend } from "../config";
import { getDocumentById } from "../demo";
import { ScoreBar } from "../components/ScoreBar";

function highlightTermInText(text: string, term: string): ReactNode {
  const t = term.trim();
  if (!t) return text;
  const lower = text.toLowerCase();
  const tl = t.toLowerCase();
  const parts: ReactNode[] = [];
  let start = 0;
  let idx = lower.indexOf(tl, start);
  let key = 0;
  while (idx !== -1) {
    if (idx > start) parts.push(text.slice(start, idx));
    parts.push(
      <mark
        key={`m-${key++}`}
        style={{ background: "var(--highlight-search)", color: "inherit", padding: "0 1px", borderRadius: 2 }}
      >
        {text.slice(idx, idx + t.length)}
      </mark>,
    );
    start = idx + t.length;
    idx = lower.indexOf(tl, start);
  }
  if (start < text.length) parts.push(text.slice(start));
  return parts.length ? parts : text;
}

export function DocumentReaderPage() {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const api = isApiBackend();
  const [apiDoc, setApiDoc] = useState<DocumentDetail | null>(null);
  const [apiErr, setApiErr] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(false);

  useEffect(() => {
    if (!api || !accessToken || !id) {
      setApiDoc(null);
      setApiErr(null);
      setApiLoading(false);
      return;
    }
    let cancelled = false;
    setApiLoading(true);
    setApiErr(null);
    setApiDoc(null);
    void (async () => {
      try {
        const d = await getDocument(accessToken, id);
        if (!cancelled) setApiDoc(d);
      } catch (e) {
        if (!cancelled) {
          if (e instanceof ApiError && e.status === 404) setApiErr("notfound");
          else setApiErr(e instanceof ApiError ? e.message : "Failed to load document");
        }
      } finally {
        if (!cancelled) setApiLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, id]);

  if (api) {
    if (!id) {
      return (
        <>
          <h1 className="page-title">Document not found</h1>
          <p className="page-sub">
            <Link to="/dashboard">Back to dashboard</Link>
          </p>
        </>
      );
    }
    if (apiLoading) {
      return <p className="page-sub">Loading document…</p>;
    }
    if (apiErr === "notfound") {
      return (
        <>
          <h1 className="page-title">Document not found</h1>
          <p className="page-sub">
            Unknown id or no access. <Link to="/dashboard">Back to dashboard</Link>
          </p>
        </>
      );
    }
    if (apiErr) {
      return (
        <>
          <h1 className="page-title">Error</h1>
          <p className="error-text">{apiErr}</p>
          <p className="page-sub">
            <Link to="/dashboard">Back to dashboard</Link>
          </p>
        </>
      );
    }
    if (!apiDoc) return null;

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link to="/dashboard" style={{ fontSize: "0.9rem" }}>
            ← Library
          </Link>
        </div>
        <h1 className="page-title">{apiDoc.title || apiDoc.original_filename || apiDoc.id}</h1>
        <p className="page-sub">
          <strong>API document</strong> — Status <code>{apiDoc.status}</code>
          {apiDoc.content_type ? (
            <>
              {" "}
              · <code>{apiDoc.content_type}</code>
            </>
          ) : null}
          . Canonical scores come from <code>document_scores</code> (pipeline heuristic until ML models ship). Segment-level
          highlights remain demo-only.
        </p>
        {apiDoc.canonical_score &&
        (apiDoc.canonical_score.factuality_score != null ||
          apiDoc.canonical_score.ai_generation_probability != null) ? (
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Scores</h2>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 0 }}>
              {apiDoc.canonical_score.scorer_name} {apiDoc.canonical_score.scorer_version}
            </p>
            {apiDoc.canonical_score.factuality_score != null ? (
              <div style={{ marginBottom: "0.75rem" }}>
                <ScoreBar value={apiDoc.canonical_score.factuality_score} label="Factuality (heuristic)" />
              </div>
            ) : null}
            {apiDoc.canonical_score.ai_generation_probability != null ? (
              <ScoreBar value={apiDoc.canonical_score.ai_generation_probability} label="AI-style proxy (heuristic)" />
            ) : null}
          </div>
        ) : null}
        <div className="card">
          <pre
            style={{
              margin: 0,
              whiteSpace: "pre-wrap",
              fontFamily: "var(--font-sans, system-ui, sans-serif)",
              fontSize: "0.95rem",
              lineHeight: 1.5,
            }}
          >
            {apiDoc.body_text || "(No extracted text yet — pipeline may still be running.)"}
          </pre>
        </div>
        {apiDoc.sources.length ? (
          <div className="card" style={{ marginTop: "1rem" }}>
            <h2 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>Sources</h2>
            <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
              {apiDoc.sources.map((s) => (
                <li key={s.id} style={{ fontSize: "0.9rem" }}>
                  <code>{s.source_kind}</code> — {s.locator}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </>
    );
  }

  const doc = id ? getDocumentById(id) : undefined;
  const [panelTab, setPanelTab] = useState<"scores" | "keywords">("scores");
  const [focusMode, setFocusMode] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);

  const aiScore = doc?.scores.find((s) => s.id === "ai");
  const factScore = doc?.scores.find((s) => s.id === "factuality");
  const showDangerBar = (aiScore && aiScore.value > 0.75) || (factScore && factScore.value <= 0.4);

  if (!doc) {
    return (
      <>
        <h1 className="page-title">Document not found</h1>
        <p className="page-sub">
          Unknown id in demo data. <Link to="/dashboard">Back to dashboard</Link>
        </p>
      </>
    );
  }

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/dashboard" style={{ fontSize: "0.9rem" }}>
          ← Library
        </Link>
      </div>
      <h1 className="page-title">{doc.title}</h1>
      <p className="page-sub">
        <strong>Use Case 3</strong> — reader with score panel, inline fallacy highlights, and keyword tab (mock).
      </p>

      {showDangerBar ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            flexWrap: "wrap",
            padding: "0.65rem 1rem",
            borderRadius: "var(--radius-sm)",
            background: "var(--danger-bg)",
            border: "1px solid rgba(248,113,113,0.35)",
            marginBottom: "1rem",
          }}
        >
          <strong style={{ color: "var(--danger)" }}>Alert</strong>
          <span style={{ fontSize: "0.9rem" }}>
            Thresholds exceeded (spec): high AI probability and/or low factuality. Review highlighted passages.
          </span>
          {aiScore ? <span className="pill pill-danger">AI {Math.round(aiScore.value * 100)}%</span> : null}
          {factScore ? <span className="pill pill-warn">Factuality {Math.round(factScore.value * 100)}%</span> : null}
        </div>
      ) : null}

      <div style={{ marginBottom: "1rem", display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" className={focusMode ? "btn btn-primary" : "btn"} onClick={() => setFocusMode((f) => !f)}>
          {focusMode ? "Exit focus mode" : "Focus mode"}
        </button>
      </div>

      <div className="reader-grid">
        <div className="card">
          <div className={`reader-doc ${focusMode ? "focus-mode" : ""}`}>
            {doc.bodySegments.map((seg, i) => {
              const content =
                selectedKeyword && !seg.highlight ? highlightTermInText(seg.text, selectedKeyword) : seg.text;
              return seg.highlight ? (
                <span key={i} className="hl" title={`${seg.highlight.fallacyType}: ${seg.highlight.explanation}`}>
                  {seg.text}
                </span>
              ) : (
                <span key={i}>{content}</span>
              );
            })}
          </div>
          {doc.author || doc.sourceDomain ? (
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "1rem" }}>
              Provenance (mock): {doc.author ? <>{doc.author} · </> : null}
              {doc.sourceDomain}
            </p>
          ) : null}
        </div>

        <div className="card" style={{ position: focusMode ? "sticky" : undefined, top: 12 }}>
          <div className="tabs">
            <button type="button" className={panelTab === "scores" ? "active" : ""} onClick={() => setPanelTab("scores")}>
              Scores
            </button>
            <button
              type="button"
              className={panelTab === "keywords" ? "active" : ""}
              onClick={() => setPanelTab("keywords")}
            >
              Keywords
            </button>
          </div>

          {panelTab === "scores" ? (
            <div>
              {doc.scores.length === 0 ? (
                <p style={{ color: "var(--text-muted)" }}>Scores appear when processing completes.</p>
              ) : (
                doc.scores.map((s) => (
                  <div key={s.id} style={{ marginBottom: "1rem" }}>
                    <ScoreBar value={s.value} label={s.label} />
                    {s.detail ? (
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>{s.detail}</div>
                    ) : null}
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ marginTop: 6, padding: "0.2rem 0", fontSize: "0.8rem" }}
                      onClick={() => setExpanded((e) => ({ ...e, [s.id]: !e[s.id] }))}
                    >
                      {expanded[s.id] ? "Hide rationale" : "Show rationale"}
                    </button>
                    {expanded[s.id] ? (
                      <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: "0.35rem 0 0" }}>{s.rationale}</p>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          ) : (
            <div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 0 }}>
                TF-IDF terms (mock). In production, clicking would highlight occurrences in the document body.
              </p>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {doc.keywords.map((k) => (
                  <li key={k.term} style={{ marginBottom: 8 }}>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ padding: "0.25rem 0", fontWeight: 600 }}
                      onClick={() => setSelectedKeyword((cur) => (cur === k.term ? null : k.term))}
                    >
                      {k.term}
                    </button>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginLeft: 8 }}>
                      {(k.weight * 100).toFixed(0)}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
