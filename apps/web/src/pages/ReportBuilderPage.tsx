import { useState } from "react";
import { DEMO_COLLECTIONS } from "../demo";

const SECTIONS = [
  "Executive summary (LLM)",
  "Score distributions",
  "Top fallacies",
  "Suspicious documents table",
  "Source breakdown",
  "Keyword trends",
] as const;

export function ReportBuilderPage() {
  const [collectionId, setCollectionId] = useState(DEMO_COLLECTIONS[0]?.id ?? "");
  const [picked, setPicked] = useState<Record<string, boolean>>(
    Object.fromEntries(SECTIONS.map((s) => [s, true])) as Record<string, boolean>,
  );
  const [phase, setPhase] = useState<"config" | "preview">("config");

  return (
    <>
      <h1 className="page-title">New report</h1>
      <p className="page-sub">
        <strong>Use Case 6</strong> — scope, sections, mock generation progress, HTML preview (PDF would stream from
        server).
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(260px, 340px) 1fr", gap: "1.25rem" }}>
        <div className="card">
          <h2 style={{ margin: "0 0 1rem", fontSize: "1rem" }}>Configuration</h2>
          <div className="field">
            <label htmlFor="scope">Collection</label>
            <select
              id="scope"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              style={{
                padding: "0.55rem",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
                background: "var(--bg-root)",
                color: "var(--text)",
              }}
            >
              {DEMO_COLLECTIONS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="report-name">Report name</label>
            <input id="report-name" defaultValue="Q1 intelligence summary" />
          </div>
          <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
            <legend style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: 8 }}>Sections</legend>
            {SECTIONS.map((s) => (
              <label key={s} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6, fontSize: "0.9rem" }}>
                <input
                  type="checkbox"
                  checked={picked[s]}
                  onChange={() => setPicked((p) => ({ ...p, [s]: !p[s] }))}
                />
                {s}
              </label>
            ))}
          </fieldset>
          <button
            type="button"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "1rem" }}
            onClick={() => setPhase("preview")}
          >
            Generate (mock)
          </button>
        </div>

        <div className="card">
          <h2 style={{ margin: "0 0 1rem", fontSize: "1rem" }}>Preview</h2>
          {phase === "config" ? (
            <p style={{ color: "var(--text-muted)", margin: 0 }}>
              Configure scope and sections, then generate. SSE would stream aggregation + LLM summary progress.
            </p>
          ) : (
            <div style={{ fontSize: "0.95rem", lineHeight: 1.6 }}>
              <h3 style={{ marginTop: 0 }}>Executive summary</h3>
              <p style={{ color: "var(--text-muted)" }}>
                Mock narrative: the selected collection shows elevated AI-assistance signals in policy drafts while
                technical questionnaires remain comparatively grounded. Fallacy hotspots cluster around anonymous
                sourcing and implied causality.
              </p>
              {picked["Score distributions"] ? (
                <>
                  <h3>Score distributions</h3>
                  <p style={{ color: "var(--text-muted)" }}>[Histogram placeholders — same data as analytics view.]</p>
                </>
              ) : null}
              {picked["Suspicious documents table"] ? (
                <>
                  <h3>Suspicious documents</h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>AI</th>
                        <th>Factuality</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Policy brief — summer outreach pilot</td>
                        <td>0.81</td>
                        <td>0.62</td>
                      </tr>
                    </tbody>
                  </table>
                </>
              ) : null}
              <div style={{ marginTop: "1.25rem", display: "flex", gap: 8 }}>
                <button type="button" className="btn btn-primary">
                  Download PDF (mock)
                </button>
                <button type="button" className="btn" onClick={() => setPhase("config")}>
                  Edit configuration
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
