import { Link, useParams } from "react-router-dom";
import { DEMO_ANALYTICS, DEMO_COLLECTIONS } from "../demo";

export function CollectionAnalyticsPage() {
  const { collectionId } = useParams();
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
