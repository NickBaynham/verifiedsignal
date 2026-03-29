import { DEMO_INVOICES, DEMO_PLANS, DEMO_USAGE } from "../demo";

export function AccountBillingPage() {
  const u = DEMO_USAGE;
  const docPct = Math.min(100, (u.documentsUsed / u.documentsLimit) * 100);
  const storPct = Math.min(100, (u.storageGbUsed / u.storageGbLimit) * 100);
  const warn = docPct >= 80;

  return (
    <>
      <h1 className="page-title">Billing</h1>
      <p className="page-sub">
        <strong>Use Case 7</strong> — plans, usage vs limits, invoices (Stripe mocked).
      </p>

      {warn ? (
        <div className="card" style={{ borderColor: "var(--warn)", marginBottom: "1rem", background: "var(--warn-bg)" }}>
          <strong style={{ color: "var(--warn)" }}>Approaching document limit</strong>
          <p style={{ margin: "0.35rem 0 0", fontSize: "0.9rem" }}>
            You are past 80% of included documents on the Professional plan.
          </p>
        </div>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
        {DEMO_PLANS.map((p) => (
          <div
            key={p.id}
            className="card"
            style={
              p.highlighted
                ? { outline: "2px solid var(--accent)", outlineOffset: 2, position: "relative" as const }
                : undefined
            }
          >
            {p.highlighted ? (
              <span className="pill pill-ok" style={{ position: "absolute", top: 12, right: 12 }}>
                Current plan
              </span>
            ) : null}
            <h2 style={{ margin: "0 0 0.25rem", fontSize: "1.05rem" }}>{p.name}</h2>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.75rem" }}>{p.priceLabel}</div>
            <ul style={{ margin: 0, paddingLeft: "1.1rem", color: "var(--text-muted)", fontSize: "0.9rem" }}>
              <li>{p.documentsLimit.toLocaleString()} documents / mo</li>
              <li>{p.storageGb} GB storage</li>
            </ul>
            {!p.highlighted ? (
              <button type="button" className="btn" style={{ marginTop: "1rem", width: "100%" }}>
                Select (mock)
              </button>
            ) : null}
          </div>
        ))}
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <h2 style={{ margin: "0 0 1rem", fontSize: "1rem" }}>Usage</h2>
        <div style={{ marginBottom: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
            <span>Documents</span>
            <span>
              {u.documentsUsed} / {u.documentsLimit}
            </span>
          </div>
          <div className="score-bar-track" style={{ marginTop: 6 }}>
            <div className="score-bar-fill" style={{ width: `${docPct}%` }} />
          </div>
        </div>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
            <span>Storage</span>
            <span>
              {u.storageGbUsed} / {u.storageGbLimit} GB
            </span>
          </div>
          <div className="score-bar-track" style={{ marginTop: 6 }}>
            <div className="score-bar-fill" style={{ width: `${storPct}%` }} />
          </div>
        </div>
        <button type="button" className="btn btn-primary" style={{ marginTop: "1.25rem" }}>
          Update payment method (Stripe modal — mock)
        </button>
      </div>

      <div className="card" style={{ marginTop: "1rem" }}>
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Invoices</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Plan</th>
              <th>Amount</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {DEMO_INVOICES.map((inv) => (
              <tr key={inv.id}>
                <td>{inv.date}</td>
                <td>{inv.plan}</td>
                <td>{inv.amount}</td>
                <td>{inv.status}</td>
                <td>
                  <button type="button" className="btn btn-ghost" style={{ padding: "0.25rem 0" }}>
                    PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
