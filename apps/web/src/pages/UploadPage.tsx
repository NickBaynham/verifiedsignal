import { useCallback, useRef, useState } from "react";
import type { PipelineStage } from "../demo/types";

const STAGES: PipelineStage[] = ["ingest", "extract", "enrich", "score", "index", "finalize"];

interface MockFile {
  id: string;
  name: string;
  sizeLabel: string;
  duplicate: boolean;
}

function simulateFiles(files: FileList | null): MockFile[] {
  if (!files?.length) return [];
  return Array.from(files).map((f, i) => ({
    id: `tmp-${i}-${f.name}`,
    name: f.name,
    sizeLabel: `${(f.size / 1024).toFixed(1)} KB`,
    duplicate: f.name.toLowerCase().includes("copy") || f.name.toLowerCase().includes("dup"),
  }));
}

export function UploadPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [tab, setTab] = useState<"files" | "url">("files");
  const [selected, setSelected] = useState<MockFile[]>([]);
  const [processing, setProcessing] = useState(false);
  const [stageIndexById, setStageIndexById] = useState<Record<string, number>>({});

  const onPick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const onFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelected(simulateFiles(e.target.files));
    e.target.value = "";
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setSelected(simulateFiles(e.dataTransfer.files));
  };

  const startPipeline = () => {
    if (!selected.length) return;
    setProcessing(true);
    const initial: Record<string, number> = {};
    selected.forEach((f) => {
      initial[f.id] = 0;
    });
    setStageIndexById(initial);

    const interval = window.setInterval(() => {
      setStageIndexById((prev) => {
        const next = { ...prev };
        let anyRunning = false;
        selected.forEach((f) => {
          const idx = next[f.id] ?? 0;
          if (idx < STAGES.length) {
            anyRunning = true;
            next[f.id] = idx + 1;
          }
        });
        if (!anyRunning) {
          window.clearInterval(interval);
          setProcessing(false);
        }
        return next;
      });
    }, 600);
  };

  return (
    <>
      <h1 className="page-title">Upload</h1>
      <p className="page-sub">
        <strong>Use Case 2</strong> — file drop zone, duplicate hint, and simulated pipeline stages (SSE would stream
        progress in production).
      </p>

      <div className="tabs">
        <button type="button" className={tab === "files" ? "active" : ""} onClick={() => setTab("files")}>
          File upload
        </button>
        <button type="button" className={tab === "url" ? "active" : ""} onClick={() => setTab("url")}>
          URL submission
        </button>
      </div>

      {tab === "files" ? (
        <div className="card">
          <div
            className="dropzone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            role="presentation"
          >
            <p>
              <strong>Drag and drop</strong> PDF, DOCX, TXT, HTML, MD (demo accepts any file).
            </p>
            <p style={{ margin: "0.75rem 0" }}>or</p>
            <button type="button" className="btn btn-primary" onClick={onPick}>
              Choose files
            </button>
            <input ref={inputRef} type="file" multiple hidden onChange={onFiles} />
          </div>

          {selected.length ? (
            <>
              <h3 style={{ marginTop: "1.25rem", fontSize: "0.95rem" }}>Selected</h3>
              {selected.map((f) => (
                <div key={f.id} className="file-row">
                  <div>
                    <div style={{ fontWeight: 600 }}>{f.name}</div>
                    <div className="meta">{f.sizeLabel}</div>
                  </div>
                  {f.duplicate ? <span className="pill pill-warn">Possible duplicate</span> : <span className="pill">New</span>}
                </div>
              ))}
              <div style={{ marginTop: "1rem", display: "flex", gap: 8 }}>
                <button type="button" className="btn btn-primary" disabled={processing} onClick={startPipeline}>
                  {processing ? "Processing…" : "Start ingestion (mock)"}
                </button>
                <button
                  type="button"
                  className="btn"
                  disabled={processing}
                  onClick={() => {
                    setSelected([]);
                    setStageIndexById({});
                  }}
                >
                  Clear
                </button>
              </div>
            </>
          ) : null}

          {selected.length && Object.keys(stageIndexById).length ? (
            <div style={{ marginTop: "1.5rem" }}>
              <h3 style={{ fontSize: "0.95rem" }}>Pipeline progress</h3>
              {selected.map((f) => {
                const idx = stageIndexById[f.id] ?? 0;
                return (
                  <div key={f.id} className="pipeline-row">
                    <div>
                      <div style={{ fontWeight: 600 }}>{f.name}</div>
                      <div className="pipeline-stages">
                        {STAGES.map((s, i) => (
                          <span
                            key={s}
                            className={`stage-pill ${i < idx ? "done" : ""} ${i === idx && idx < STAGES.length ? "current" : ""}`}
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                    {idx >= STAGES.length ? <span className="pill pill-ok">Complete</span> : null}
                  </div>
                );
              })}
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "1rem" }}>
                Presigned S3 upload and <code>POST /documents/ingest</code> would run here; scores would stream per
                dimension as in the spec.
              </p>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="card">
          <p style={{ color: "var(--text-muted)", marginTop: 0 }}>
            URL ingestion UI placeholder — paste a URL and enqueue (mock). Backend not wired.
          </p>
          <div className="field">
            <label htmlFor="url">Document URL</label>
            <input id="url" type="url" placeholder="https://example.com/report.pdf" />
          </div>
          <button type="button" className="btn btn-primary">
            Queue URL (mock)
          </button>
        </div>
      )}
    </>
  );
}
