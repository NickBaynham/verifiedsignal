import type { DemoDocument } from "../demo/types";

export function DocumentScoreBadges({ doc }: { doc: DemoDocument }) {
  const fact = doc.scores.find((s) => s.id === "factuality");
  const ai = doc.scores.find((s) => s.id === "ai");
  if (!fact && !ai) return null;
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {fact ? (
        <span className="pill pill-ok" title="Factuality (mock)">
          F {Math.round(fact.value * 100)}%
        </span>
      ) : null}
      {ai ? (
        <span className={ai.value >= 0.7 ? "pill pill-danger" : "pill"} title="AI probability (mock)">
          AI {Math.round(ai.value * 100)}%
        </span>
      ) : null}
    </div>
  );
}
