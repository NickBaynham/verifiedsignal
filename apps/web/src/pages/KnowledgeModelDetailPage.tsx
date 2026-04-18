import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  fetchKnowledgeModelDetail,
  listKnowledgeModelVersionAssets,
  listKnowledgeModelVersions,
} from "../api/knowledgeModels";
import {
  createModelFinding,
  fetchModelActivity,
  listModelWritebacks,
  patchWritebackVerification,
} from "../api/modelWritebacks";
import { ApiError } from "../api/http";
import type {
  KnowledgeModelAsset,
  KnowledgeModelDetail,
  KnowledgeModelVersion,
  ModelActivityItem,
  ModelWriteback,
} from "../api/types";
import { isApiBackend } from "../config";
import { useAuth } from "../context/AuthContext";
import { knowledgeModelTypeLabel } from "../lib/knowledgeModelUi";
import { statusBadgeClass, writebackVerificationBadgeClass } from "../lib/statusBadge";

type DetailView = "overview" | "versions" | "documents" | "writeback" | "activity";

function parseView(raw: string | null): DetailView {
  if (raw === "versions" || raw === "documents" || raw === "writeback" || raw === "activity")
    return raw;
  return "overview";
}

function safeJsonPreview(value: Record<string, unknown> | null): string {
  if (value == null) return "—";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function KnowledgeModelDetailPage() {
  const { modelId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const view = parseView(searchParams.get("view"));
  const { accessToken } = useAuth();
  const api = isApiBackend();

  const [detail, setDetail] = useState<KnowledgeModelDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [versions, setVersions] = useState<KnowledgeModelVersion[] | null>(null);
  const [versionsError, setVersionsError] = useState<string | null>(null);

  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [assets, setAssets] = useState<KnowledgeModelAsset[] | null>(null);
  const [assetsError, setAssetsError] = useState<string | null>(null);
  const [assetsLoading, setAssetsLoading] = useState(false);

  const [writebacks, setWritebacks] = useState<ModelWriteback[] | null>(null);
  const [writebacksError, setWritebacksError] = useState<string | null>(null);
  const [writebacksLoading, setWritebacksLoading] = useState(false);
  const [kindFilter, setKindFilter] = useState<string>("");
  const [verificationFilter, setVerificationFilter] = useState<string>("");
  const [newTitle, setNewTitle] = useState("");
  const [newDetails, setNewDetails] = useState("");
  const [createBusy, setCreateBusy] = useState(false);
  const [createFeedback, setCreateFeedback] = useState<string | null>(null);
  const [writebackRefresh, setWritebackRefresh] = useState(0);

  const [activityItems, setActivityItems] = useState<ModelActivityItem[] | null>(null);
  const [activityError, setActivityError] = useState<string | null>(null);
  const [activityLoading, setActivityLoading] = useState(false);

  const setView = useCallback(
    (next: DetailView) => {
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          if (next === "overview") p.delete("view");
          else p.set("view", next);
          return p;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  useEffect(() => {
    if (!api || !accessToken || !modelId) return;
    let cancelled = false;
    setDetailLoading(true);
    setDetailError(null);
    void fetchKnowledgeModelDetail(accessToken, modelId)
      .then((d) => {
        if (!cancelled) {
          setDetail(d);
          setSelectedVersionId(d.latest_version?.id ?? null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setDetail(null);
          setDetailError(e instanceof ApiError ? e.message : "Failed to load model");
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, modelId]);

  useEffect(() => {
    if (!api || !accessToken || !modelId) return;
    let cancelled = false;
    setVersionsError(null);
    void listKnowledgeModelVersions(accessToken, modelId)
      .then((r) => {
        if (!cancelled) setVersions(r.items);
      })
      .catch((e) => {
        if (!cancelled) {
          setVersions(null);
          setVersionsError(e instanceof ApiError ? e.message : "Failed to load versions");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, modelId]);

  useEffect(() => {
    if (!versions?.length) return;
    setSelectedVersionId((prev) => {
      if (prev && versions.some((v) => v.id === prev)) return prev;
      return detail?.latest_version?.id ?? versions[0]?.id ?? null;
    });
  }, [versions, detail?.latest_version?.id]);

  useEffect(() => {
    if (!api || !accessToken || !modelId || !selectedVersionId) return;
    if (view !== "documents") return;
    let cancelled = false;
    setAssetsLoading(true);
    setAssetsError(null);
    void listKnowledgeModelVersionAssets(accessToken, modelId, selectedVersionId)
      .then((r) => {
        if (!cancelled) setAssets(r.items);
      })
      .catch((e) => {
        if (!cancelled) {
          setAssets(null);
          setAssetsError(e instanceof ApiError ? e.message : "Failed to load included documents");
        }
      })
      .finally(() => {
        if (!cancelled) setAssetsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, modelId, selectedVersionId, view]);

  useEffect(() => {
    if (!api || !accessToken || !modelId || view !== "writeback") return;
    let cancelled = false;
    setWritebacksLoading(true);
    setWritebacksError(null);
    void listModelWritebacks(accessToken, modelId, {
      artifact_kind: kindFilter || undefined,
      verification_state: verificationFilter || undefined,
      limit: 100,
    })
      .then((r) => {
        if (!cancelled) setWritebacks(r.items);
      })
      .catch((e) => {
        if (!cancelled) {
          setWritebacks(null);
          setWritebacksError(e instanceof ApiError ? e.message : "Failed to load write-backs");
        }
      })
      .finally(() => {
        if (!cancelled) setWritebacksLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, modelId, view, kindFilter, verificationFilter, writebackRefresh]);

  useEffect(() => {
    if (!api || !accessToken || !modelId || view !== "activity") return;
    let cancelled = false;
    setActivityLoading(true);
    setActivityError(null);
    void fetchModelActivity(accessToken, modelId)
      .then((r) => {
        if (!cancelled) setActivityItems(r.items);
      })
      .catch((e) => {
        if (!cancelled) {
          setActivityItems(null);
          setActivityError(e instanceof ApiError ? e.message : "Failed to load activity");
        }
      })
      .finally(() => {
        if (!cancelled) setActivityLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api, accessToken, modelId, view]);

  if (!modelId) {
    return (
      <>
        <h1 className="page-title">Model not found</h1>
        <p className="page-sub">
          <Link to="/collections">Back to collections</Link>
        </p>
      </>
    );
  }

  if (!api) {
    return (
      <>
        <h1 className="page-title">Knowledge model</h1>
        <p className="page-sub">
          Model inspection requires API mode. <Link to="/collections">Back to collections</Link>
        </p>
      </>
    );
  }

  if (detailError) {
    return (
      <>
        <h1 className="page-title">Error</h1>
        <p className="error-text">{detailError}</p>
        <p className="page-sub">
          <Link to="/collections">Back to collections</Link>
        </p>
      </>
    );
  }

  if (detailLoading && !detail) {
    return <p className="page-sub">Loading…</p>;
  }

  if (!detail) {
    return (
      <>
        <h1 className="page-title">Model not found</h1>
        <p className="page-sub">
          <Link to="/collections">Back to collections</Link>
        </p>
      </>
    );
  }

  const collectionLink = `/collections/${detail.collection_id}?tab=models`;
  const lv = detail.latest_version;

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to={collectionLink} style={{ fontSize: "0.9rem" }}>
          ← Collection models
        </Link>
      </div>

      <header style={{ marginBottom: "1rem" }}>
        <h1 className="page-title" style={{ marginBottom: "0.35rem" }}>
          {detail.name}
        </h1>
        <p className="page-sub" style={{ marginTop: 0 }}>
          {knowledgeModelTypeLabel(detail.model_type)}
          {lv ? (
            <>
              {" "}
              · <span className={statusBadgeClass(lv.build_status)}>{lv.build_status}</span>
              {lv.version_number != null ? ` · v${lv.version_number}` : null}
            </>
          ) : null}
        </p>
        {detail.description ? (
          <p style={{ fontSize: "0.95rem", maxWidth: 720 }}>{detail.description}</p>
        ) : null}
      </header>

      <div
        role="tablist"
        aria-label="Model sections"
        style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: "1rem" }}
      >
        {(
          [
            ["overview", "Overview"],
            ["versions", "Versions"],
            ["documents", "Included documents"],
            ["writeback", "Write-back"],
            ["activity", "Activity"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={view === key}
            className={view === key ? "btn btn-primary" : "btn"}
            onClick={() => setView(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {view === "overview" ? (
        <section className="card" style={{ padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Summary</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Latest build output (<code>summary_json</code>). Future tabs can surface entities, claims,
            risks, and test artifacts.
          </p>
          <pre
            style={{
              marginTop: "0.75rem",
              padding: "0.75rem",
              borderRadius: 8,
              background: "var(--bg-root)",
              border: "1px solid var(--border)",
              fontSize: "0.8rem",
              overflow: "auto",
              maxHeight: 420,
            }}
          >
            {safeJsonPreview(detail.summary_json)}
          </pre>
        </section>
      ) : null}

      {view === "versions" ? (
        <section className="card" style={{ padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Versions</h2>
          {versionsError ? <p className="error-text">{versionsError}</p> : null}
          {!versions && !versionsError ? <p className="page-sub">Loading…</p> : null}
          {versions && versions.length === 0 ? (
            <p className="page-sub">No versions.</p>
          ) : null}
          {versions && versions.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Assets</th>
                  <th>Created</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {versions.map((v) => (
                  <tr key={v.id}>
                    <td>v{v.version_number}</td>
                    <td>
                      <span className={statusBadgeClass(v.build_status)}>{v.build_status}</span>
                    </td>
                    <td>{v.asset_count}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                      {new Date(v.created_at).toLocaleString()}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn"
                        onClick={() => {
                          setSelectedVersionId(v.id);
                          setView("documents");
                        }}
                      >
                        Included docs
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </section>
      ) : null}

      {view === "documents" ? (
        <section className="card" style={{ padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Included documents</h2>
          <label style={{ display: "block", marginBottom: "0.75rem", fontSize: "0.9rem" }}>
            Version{" "}
            <select
              value={selectedVersionId ?? ""}
              onChange={(e) => setSelectedVersionId(e.target.value || null)}
              style={{
                marginLeft: 8,
                padding: "0.35rem 0.5rem",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--bg-elevated)",
                color: "var(--text)",
              }}
            >
              {(versions ?? []).map((v) => (
                <option key={v.id} value={v.id}>
                  v{v.version_number} ({v.build_status})
                </option>
              ))}
            </select>
          </label>
          {assetsError ? <p className="error-text">{assetsError}</p> : null}
          {assetsLoading ? <p className="page-sub">Loading…</p> : null}
          {assets && assets.length === 0 && !assetsLoading ? (
            <p className="page-sub">No assets for this version.</p>
          ) : null}
          {assets && assets.length > 0 ? (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {assets.map((a) => (
                <li
                  key={a.id}
                  style={{
                    borderBottom: "1px solid var(--border)",
                    padding: "0.65rem 0",
                    fontSize: "0.9rem",
                  }}
                >
                  <Link to={`/documents/${a.document_id}`} style={{ fontWeight: 600 }}>
                    {a.title || a.original_filename || a.document_id.slice(0, 8)}
                  </Link>
                  <div style={{ color: "var(--text-muted)", marginTop: 4, fontSize: "0.85rem" }}>
                    {a.inclusion_reason ? `${a.inclusion_reason} · ` : null}
                    added {new Date(a.created_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {view === "writeback" ? (
        <section className="card" style={{ padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Write-back</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Findings, risks, and other artifacts stored in Postgres. New entries default to{" "}
            <strong>proposed</strong> until reviewed.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: "1rem" }}>
            <label style={{ fontSize: "0.85rem" }}>
              Type{" "}
              <select
                value={kindFilter}
                onChange={(e) => setKindFilter(e.target.value)}
                style={{
                  marginLeft: 6,
                  padding: "0.35rem 0.5rem",
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                  background: "var(--bg-elevated)",
                  color: "var(--text)",
                }}
              >
                <option value="">All</option>
                <option value="finding">finding</option>
                <option value="risk">risk</option>
                <option value="test_artifact">test_artifact</option>
                <option value="execution_result">execution_result</option>
                <option value="evidence_note">evidence_note</option>
                <option value="contradiction">contradiction</option>
              </select>
            </label>
            <label style={{ fontSize: "0.85rem" }}>
              Verification{" "}
              <select
                value={verificationFilter}
                onChange={(e) => setVerificationFilter(e.target.value)}
                style={{
                  marginLeft: 6,
                  padding: "0.35rem 0.5rem",
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                  background: "var(--bg-elevated)",
                  color: "var(--text)",
                }}
              >
                <option value="">All</option>
                <option value="proposed">proposed</option>
                <option value="accepted">accepted</option>
                <option value="rejected">rejected</option>
                <option value="auto_ingested">auto_ingested</option>
                <option value="superseded">superseded</option>
              </select>
            </label>
          </div>
          {writebacksError ? <p className="error-text">{writebacksError}</p> : null}
          {writebacksLoading ? <p className="page-sub">Loading…</p> : null}
          {writebacks && writebacks.length === 0 && !writebacksLoading ? (
            <p className="page-sub">No artifacts match the filters.</p>
          ) : null}
          {writebacks && writebacks.length > 0 ? (
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1.25rem" }}>
              {writebacks.map((w) => (
                <li
                  key={w.id}
                  style={{
                    borderBottom: "1px solid var(--border)",
                    padding: "0.65rem 0",
                    fontSize: "0.9rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{w.title}</div>
                  <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <span className="vs-badge">{w.artifact_kind}</span>
                    <span className={writebackVerificationBadgeClass(w.verification_state)}>
                      {w.verification_state}
                    </span>
                    <span className="vs-badge">{w.origin_type}</span>
                  </div>
                  {w.summary ? (
                    <div style={{ color: "var(--text-muted)", marginTop: 6 }}>{w.summary}</div>
                  ) : null}
                  <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {w.verification_state === "proposed" ? (
                      <>
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => {
                            if (!accessToken || !modelId) return;
                            void patchWritebackVerification(accessToken, modelId, w.id, {
                              verification_state: "accepted",
                            })
                              .then(() => setWritebackRefresh((x) => x + 1))
                              .catch((e) =>
                                setCreateFeedback(
                                  e instanceof ApiError ? e.message : "Review update failed",
                                ),
                              );
                          }}
                        >
                          Accept
                        </button>
                        <button
                          type="button"
                          className="btn"
                          onClick={() => {
                            if (!accessToken || !modelId) return;
                            void patchWritebackVerification(accessToken, modelId, w.id, {
                              verification_state: "rejected",
                            })
                              .then(() => setWritebackRefresh((x) => x + 1))
                              .catch((e) =>
                                setCreateFeedback(
                                  e instanceof ApiError ? e.message : "Review update failed",
                                ),
                              );
                          }}
                        >
                          Reject
                        </button>
                      </>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          ) : null}

          <h3 style={{ fontSize: "0.95rem" }}>Add finding</h3>
          {createFeedback ? <p className="error-text">{createFeedback}</p> : null}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 480 }}>
            <input
              type="text"
              placeholder="Title"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              style={{
                padding: "0.5rem 0.65rem",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--bg-elevated)",
                color: "var(--text)",
              }}
            />
            <textarea
              placeholder="Details (optional)"
              value={newDetails}
              onChange={(e) => setNewDetails(e.target.value)}
              rows={3}
              style={{
                padding: "0.5rem 0.65rem",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--bg-elevated)",
                color: "var(--text)",
              }}
            />
            <button
              type="button"
              className="btn btn-primary"
              disabled={createBusy || !newTitle.trim()}
              onClick={() => {
                if (!accessToken || !modelId) return;
                setCreateBusy(true);
                setCreateFeedback(null);
                void createModelFinding(accessToken, modelId, {
                  title: newTitle.trim(),
                  details: newDetails.trim() || null,
                  model_version_id: selectedVersionId,
                })
                  .then(() => {
                    setNewTitle("");
                    setNewDetails("");
                    setWritebackRefresh((x) => x + 1);
                  })
                  .catch((e) =>
                    setCreateFeedback(e instanceof ApiError ? e.message : "Create failed"),
                  )
                  .finally(() => setCreateBusy(false));
              }}
            >
              {createBusy ? "Saving…" : "Save finding"}
            </button>
          </div>
        </section>
      ) : null}

      {view === "activity" ? (
        <section className="card" style={{ padding: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1rem" }}>Activity</h2>
          {activityError ? <p className="error-text">{activityError}</p> : null}
          {activityLoading ? <p className="page-sub">Loading…</p> : null}
          {activityItems && activityItems.length === 0 && !activityLoading ? (
            <p className="page-sub">No activity.</p>
          ) : null}
          {activityItems && activityItems.length > 0 ? (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {activityItems.map((a) => (
                <li
                  key={a.id}
                  style={{
                    borderBottom: "1px solid var(--border)",
                    padding: "0.65rem 0",
                    fontSize: "0.9rem",
                  }}
                >
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    {new Date(a.occurred_at).toLocaleString()} · {a.event_type}
                  </div>
                  <div style={{ fontWeight: 600, marginTop: 4 }}>{a.title}</div>
                  {a.summary ? (
                    <div style={{ color: "var(--text-muted)", marginTop: 4 }}>{a.summary}</div>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}
    </>
  );
}
