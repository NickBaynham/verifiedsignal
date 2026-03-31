import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCollections } from "../api/collections";
import { listDocuments } from "../api/documents";
import { useAuth } from "../context/AuthContext";
import { isApiBackend } from "../config";
import { DocumentScoreBadges } from "../components/DocumentScoreBadges";
import { DEMO_DASHBOARD_METRICS, resolveDemoDocument, visibleDashboardRecentIds } from "../demo";
import { useDemoData } from "../context/DemoDataContext";
import { ApiError } from "../api/http";
import { useApiEventSource } from "../hooks/useApiEventSource";
import type { DocumentSummary } from "../api/types";

export function DashboardPage() {
  const { accessToken } = useAuth();
  const { deletedDocumentIds } = useDemoData();
  const api = isApiBackend();
  const [items, setItems] = useState<DocumentSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [collectionCount, setCollectionCount] = useState<number | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const [liveLines, setLiveLines] = useState<string[]>([]);

  const loadDashboard = useCallback(async () => {
    if (!api || !accessToken) return;
    setLoadError(null);
    try {
      const [docRes, colRes] = await Promise.all([
        listDocuments(accessToken, { limit: 20 }),
        listCollections(accessToken),
      ]);
      setItems(docRes.items);
      setTotal(docRes.total);
      setCollectionCount(colRes.collections.length);
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Failed to load dashboard");
    }
  }, [api, accessToken]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard, refreshTick]);

  useApiEventSource(
    api && !!accessToken,
    (msg) => {
      if (msg.type === "document_queued" && msg.payload.document_id) {
        const id = String(msg.payload.document_id);
        setLiveLines((prev) => [`document_queued · ${id}`, ...prev].slice(0, 15));
        setRefreshTick((t) => t + 1);
      }
    },
    accessToken,
  );

  if (api) {
    return (
      <>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-sub">
          Documents and collections from <code>GET /api/v1/documents</code> and <code>GET /api/v1/collections</code>.
          The feed below uses <code>SSE /api/v1/events/stream</code> (same origin as <code>VITE_API_URL</code>) to refresh
          when <code>document_queued</code> fires from intake.
        </p>
        {loadError ? <p className="error-text">{loadError}</p> : null}
        {liveLines.length ? (
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>Live activity</h2>
            <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
              {liveLines.map((line, i) => (
                <li key={`${line}-${i}`}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="label">Documents</div>
            <div className="value">{total}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Collections</div>
            <div className="value">{collectionCount ?? "—"}</div>
          </div>
          <div className="kpi-card">
            <div className="label">Avg factuality</div>
            <div className="value" style={{ fontSize: "1.1rem" }}>
              —
            </div>
          </div>
          <div className="kpi-card">
            <div className="label">Avg AI probability</div>
            <div className="value" style={{ fontSize: "1.1rem" }}>
              —
            </div>
          </div>
          <div className="kpi-card">
            <div className="label">Suspicious docs</div>
            <div className="value" style={{ fontSize: "1.1rem" }}>
              —
            </div>
          </div>
        </div>
        <div className="card">
          <h2 style={{ margin: "0 0 1rem", fontSize: "1.05rem" }}>Recent documents</h2>
          {items.length === 0 && !loadError ? (
            <p style={{ color: "var(--text-muted)" }}>No documents yet. Upload from the Library page.</p>
          ) : null}
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {items.map((doc) => (
              <li
                key={doc.id}
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
                    {doc.title || doc.original_filename || doc.id}
                  </Link>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {doc.original_filename ?? "—"} · {doc.status}
                  </div>
                </div>
                <span className="pill">{doc.status}</span>
              </li>
            ))}
          </ul>
        </div>
      </>
    );
  }

  const m = DEMO_DASHBOARD_METRICS;
  const recentIds = visibleDashboardRecentIds(deletedDocumentIds);
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
          {recentIds.map((id) => {
            const doc = resolveDemoDocument(id, deletedDocumentIds);
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
