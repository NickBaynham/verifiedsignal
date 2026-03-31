import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCollections } from "../api/collections";
import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { isApiBackend } from "../config";
import type { CollectionRow } from "../api/types";
import { DEMO_COLLECTIONS } from "../demo";

export function CollectionsPage() {
  const { accessToken } = useAuth();
  const api = isApiBackend();
  const [rows, setRows] = useState<CollectionRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!api || !accessToken) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await listCollections(accessToken);
        if (!cancelled) {
          setRows(res.collections);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Failed to load collections");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, accessToken]);

  if (api) {
    return (
      <>
        <h1 className="page-title">Collections</h1>
        <p className="page-sub">
          From <code>GET /api/v1/collections</code>. Each row links to{" "}
          <code>GET /api/v1/collections/{"{id}"}/analytics</code> for OpenSearch facet buckets (when indexed) and Postgres
          KPIs; placeholder charts remain on that page for UX.
        </p>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Documents</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>{c.name}</td>
                  <td>{c.document_count}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <Link to={`/collections/${c.id}/analytics`}>Analytics →</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && !error ? (
            <p style={{ color: "var(--text-muted)", marginTop: "1rem" }}>No collections returned for your account.</p>
          ) : null}
        </div>
      </>
    );
  }

  return (
    <>
      <h1 className="page-title">Collections</h1>
      <p className="page-sub">
        Open a collection to view analytics — <strong>Use Case 4</strong>.
      </p>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Documents</th>
              <th>Updated</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {DEMO_COLLECTIONS.map((c) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.name}</td>
                <td>{c.documentCount}</td>
                <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  {new Date(c.updatedAt).toLocaleDateString()}
                </td>
                <td>
                  <Link to={`/collections/${c.id}/analytics`}>Analytics →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
