/** Single 0–1 score as a horizontal gauge (demo). */

export function ScoreBar({ value, label }: { value: number; label?: string }) {
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100);
  return (
    <div>
      {label ? (
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{label}</span>
          <span style={{ fontSize: "0.8rem", fontVariantNumeric: "tabular-nums" }}>{pct}%</span>
        </div>
      ) : null}
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
