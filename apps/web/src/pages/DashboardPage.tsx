import { Link } from "react-router-dom";
import { DEMO_DASHBOARD_METRICS, getDocumentById } from "../demo";
import { DocumentScoreBadges } from "../components/DocumentScoreBadges";

export function DashboardPage() {
  const m = DEMO_DASHBOARD_METRICS;

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-sub">
        KPI metrics and recent documents — spec <strong>Use Case 1</strong> (live SSE would attach here in production).
      </p>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="label">Documents</div>
          <div className="value">{m.totalDocuments}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Collections</div>
          <div className="value">{m.collections}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Avg factuality</div>
          <div className="value">{m.avgFactuality.toFixed(2)}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Avg AI probability</div>
          <div className="value">{m.avgAiProbability.toFixed(2)}</div>
        </div>
        <div className="kpi-card">
          <div className="label">Suspicious docs</div>
          <div className="value">{m.suspiciousCount}</div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ margin: "0 0 1rem", fontSize: "1.05rem" }}>Recent documents</h2>
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {m.recentDocumentIds.map((id) => {
            const doc = getDocumentById(id);
            if (!doc) return null;
            return (
              <li
                key={id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "1rem",
                  padding: "0.65rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <Link to={`/documents/${doc.id}`} style={{ fontWeight: 600 }}>
                    {doc.title}
                  </Link>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {doc.filename} · {doc.status}
                  </div>
                </div>
                <DocumentScoreBadges doc={doc} />
              </li>
            );
          })}
        </ul>
      </div>
    </>
  );
}
