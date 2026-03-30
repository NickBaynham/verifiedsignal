import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchCollectionAnalytics, listCollections } from "../api/collections";
import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { isApiBackend } from "../config";
import type { CollectionAnalyticsResponse } from "../api/types";
import { DEMO_ANALYTICS, DEMO_COLLECTIONS } from "../demo";

export function CollectionAnalyticsPage() {
  const { collectionId } = useParams();
  const { accessToken } = useAuth();
  const api = isApiBackend();
  const [apiName, setApiName] = useState<string | null>(null);
  const [apiDocCount, setApiDocCount] = useState<number | null>(null);
  const [apiCreated, setApiCreated] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiLoaded, setApiLoaded] = useState(false);
  const [analytics, setAnalytics] = useState<CollectionAnalyticsResponse | null>(null);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  useEffect(() => {
    if (!api || !accessToken || !collectionId) return;
    let cancelled = false;
    setApiLoaded(false);
    (async () => {
      try {
        const res = await listCollections(accessToken);
        const match = res.collections.find((c) => c.id === collectionId);
        if (cancelled) return;
        if (!match) {
          setApiError(null);
          setApiName(null);
          setApiDocCount(null);
          setApiCreated(null);
        } else {
          setApiName(match.name);
          setApiDocCount(match.document_count);
          setApiCreated(match.created_at);
          setApiError(null);
        }
      } catch (e) {
        if (!cancelled) setApiError(e instanceof ApiError ? e.message : "Failed to load collection");
      } finally {
        if (!cancelled) setApiLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, collectionId]);

  useEffect(() => {
    if (!api || !accessToken || !collectionId || !apiName) return;
    let cancelled = false;
    setAnalyticsError(null);
    void (async () => {
      try {
        const a = await fetchCollectionAnalytics(accessToken, collectionId);
        if (!cancelled) setAnalytics(a);
      } catch (e) {
        if (!cancelled) {
          setAnalytics(null);
          setAnalyticsError(e instanceof ApiError ? e.message : "Failed to load analytics");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, collectionId, apiName]);

  if (api) {
    if (!collectionId) {
      return (
        <>
          <h1 className="page-title">Collection not found</h1>
          <p className="page-sub">
            <Link to="/collections">Back to collections</Link>
          </p>
        </>
      );
    }
    if (apiError) {
      return (
        <>
          <h1 className="page-title">Error</h1>
          <p className="error-text">{apiError}</p>
          <p className="page-sub">
            <Link to="/collections">Back to collections</Link>
          </p>
        </>
      );
    }
    if (!apiLoaded) {
      return (
        <>
          <p className="page-sub">Loading…</p>
        </>
      );
    }
    if (apiName == null) {
      return (
        <>
          <h1 className="page-title">Collection not found</h1>
          <p className="page-sub">
            <Link to="/collections">Back to collections</Link>
          </p>
        </>
      );
    }

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link to="/collections" style={{ fontSize: "0.9rem" }}>
            ← Collections
          </Link>
        </div>
        <h1 className="page-title">{apiName}</h1>
        <p className="page-sub">
          <code>GET /api/v1/collections/{"{id}"}/analytics</code> — OpenSearch facet buckets (when indexed) plus Postgres
          rollups on canonical <code>document_scores</code>. Demo-mode charts below are unchanged when{" "}
          <code>VITE_API_URL</code> is unset.
        </p>
        {analyticsError ? <p className="error-text">{analyticsError}</p> : null}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="label">Documents (collection)</div>
            <div className="value">{apiDocCount ?? "—"}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Indexed (search)</div>
            <div className="value">{analytics?.index_total ?? "—"}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Avg factuality</div>
            <div className="value" style={{ fontSize: "1.1rem" }}>
              {analytics?.postgres.avg_factuality != null ? analytics.postgres.avg_factuality.toFixed(2) : "—"}
            </div>
          </div>
          <div className="kpi-card">
            <div className="label">Avg AI probability</div>
            <div className="value" style={{ fontSize: "1.1rem" }}>
              {analytics?.postgres.avg_ai_probability != null ? analytics.postgres.avg_ai_probability.toFixed(2) : "—"}
            </div>
          </div>
          <div className="kpi-card">
            <div className="label">Suspicious</div>
            <div className="value">{analytics?.postgres.suspicious_count ?? "—"}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Created</div>
            <div className="value" style={{ fontSize: "0.95rem" }}>
              {apiCreated ? new Date(apiCreated).toLocaleString() : "—"}
            </div>
          </div>
        </div>
        {analytics?.facets && Object.keys(analytics.facets).length ? (
          <div className="card" style={{ marginTop: "1rem" }}>
            <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Index facets</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 0 }}>
              Index: <code>{analytics.index_status}</code>
              {analytics.index_message ? ` — ${analytics.index_message}` : ""}
            </p>
            {Object.entries(analytics.facets).map(([name, buckets]) => (
              <div key={name} style={{ marginTop: "1rem" }}>
                <h3 style={{ fontSize: "0.9rem", margin: "0 0 0.35rem" }}>{name}</h3>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Key</th>
                      <th>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {buckets.map((b, i) => (
                      <tr key={`${name}-${i}`}>
                        <td>{b.key ?? "—"}</td>
                        <td>{b.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        ) : null}
        <div className="card" style={{ marginTop: "1rem" }}>
          <p style={{ margin: 0, color: "var(--text-muted)" }}>
            Use <Link to="/search">Search</Link> to open documents. Scores on each document come from the heuristic scorer
            after the worker pipeline runs.
          </p>
        </div>
      </>
    );
  }

  const col = DEMO_COLLECTIONS.find((c) => c.id === collectionId);
  const data = collectionId ? DEMO_ANALYTICS[collectionId] : undefined;

  const maxFact = data ? Math.max(...data.factualityHistogram.map((b) => b.count), 1) : 1;
  const maxAi = data ? Math.max(...data.aiHistogram.map((b) => b.count), 1) : 1;
  const maxFall = data ? Math.max(...data.fallacyBreakdown.map((b) => b.count), 1) : 1;
  const maxTrendF = data ? Math.max(...data.trends.map((t) => t.avgFactuality), 0.01) : 1;
  const maxTrendA = data ? Math.max(...data.trends.map((t) => t.avgAiProbability), 0.01) : 1;

  if (!col || !data) {
    return (
      <>
        <h1 className="page-title">Collection not found</h1>
        <p className="page-sub">
          <Link to="/collections">Back to collections</Link>
        </p>
      </>
    );
  }

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/collections" style={{ fontSize: "0.9rem" }}>
          ← Collections
        </Link>
      </div>
      <h1 className="page-title">{col.name}</h1>
      <p className="page-sub">
        <strong>Use Case 4</strong> — KPIs, histograms, fallacy breakdown, trends, and sources (mock aggregations;
        production: OpenSearch / Elasticsearch).
      </p>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="label">Avg factuality</div>
          <div className="value">{data.kpis.avgFactuality.toFixed(2)}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Avg AI probability</div>
          <div className="value">{data.kpis.avgAiProbability.toFixed(2)}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Avg fallacy score</div>
          <div className="value">{data.kpis.avgFallacyScore.toFixed(2)}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Suspicious docs</div>
          <div className="value">{data.kpis.suspiciousCount}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        <div className="card">
          <h2 style={{ margin: 0, fontSize: "1rem" }}>Factuality distribution</h2>
          <div className="histogram">
            {data.factualityHistogram.map((b) => (
              <div key={b.bin} className="histogram-bar-wrap">
                <div
                  className="histogram-bar"
                  style={{ height: `${(b.count / maxFact) * 100}px` }}
                  title={`${b.bin}: ${b.count}`}
                />
                <div className="histogram-label">{b.bin}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h2 style={{ margin: 0, fontSize: "1rem" }}>AI probability distribution</h2>
          <div className="histogram">
            {data.aiHistogram.map((b) => (
              <div key={b.bin} className="histogram-bar-wrap">
                <div
                  className="histogram-bar"
                  style={{
                    height: `${(b.count / maxAi) * 100}px`,
                    borderColor: "rgba(244,114,182,0.45)",
                    background: "rgba(244,114,182,0.12)",
                  }}
                  title={`${b.bin}: ${b.count}`}
                />
                <div className="histogram-label">{b.bin}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: "1rem" }}>
        <h2 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>Fallacy breakdown</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 0 }}>
          Clicking a type would filter the library — not wired in demo.
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {data.fallacyBreakdown.map((row) => (
            <div key={row.type}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
                <span>{row.type}</span>
                <span style={{ color: "var(--text-muted)" }}>{row.count}</span>
              </div>
              <div className="score-bar-track" style={{ marginTop: 4 }}>
                <div className="score-bar-fill" style={{ width: `${(row.count / maxFall) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginTop: "1rem" }}>
        <h2 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>Trends (month over month)</h2>
        <div className="trend-chart">
          {data.trends.map((t) => (
            <div key={t.month} className="trend-col">
              <div className="trend-bars">
                <div
                  className="trend-bar f"
                  style={{ height: `${(t.avgFactuality / maxTrendF) * 100}px` }}
                  title={`Factuality ${t.avgFactuality}`}
                />
                <div
                  className="trend-bar a"
                  style={{ height: `${(t.avgAiProbability / maxTrendA) * 100}px` }}
                  title={`AI ${t.avgAiProbability}`}
                />
              </div>
              <span className="histogram-label">{t.month.slice(5)}</span>
            </div>
          ))}
        </div>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          <span style={{ color: "#4ade80" }}>■</span> factuality · <span style={{ color: "#f472b6" }}>■</span> AI
          probability
        </div>
      </div>

      <div className="card" style={{ marginTop: "1rem" }}>
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Sources</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Domain</th>
              <th>Docs</th>
              <th>Avg factuality</th>
              <th>Avg AI risk</th>
            </tr>
          </thead>
          <tbody>
            {data.sources.map((s) => (
              <tr key={s.domain}>
                <td>{s.domain}</td>
                <td>{s.documents}</td>
                <td>{s.avgFactuality.toFixed(2)}</td>
                <td>{s.avgAiRisk.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <button type="button" className="btn" style={{ marginTop: "0.75rem" }}>
          Export JSON (mock)
        </button>
      </div>
    </>
  );
}
