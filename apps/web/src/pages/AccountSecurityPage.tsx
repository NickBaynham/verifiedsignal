import { useState } from "react";
import { DEMO_SESSIONS } from "../demo";

export function AccountSecurityPage() {
  const [sessions, setSessions] = useState(DEMO_SESSIONS);

  return (
    <>
      <h1 className="page-title">Security</h1>
      <p className="page-sub">
        <strong>Use Case 8</strong> — password, 2FA, active sessions with revoke (mock; refresh cookies per{" "}
        <code>docs/auth-supabase.md</code> when wired).
      </p>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h2 style={{ margin: "0 0 1rem", fontSize: "1rem" }}>Change password</h2>
        <div className="field">
          <label htmlFor="cur">Current password</label>
          <input id="cur" type="password" autoComplete="current-password" />
        </div>
        <div className="field">
          <label htmlFor="new">New password</label>
          <input id="new" type="password" autoComplete="new-password" />
        </div>
        <div className="field">
          <label htmlFor="new2">Confirm new password</label>
          <input id="new2" type="password" autoComplete="new-password" />
        </div>
        <button type="button" className="btn btn-primary">
          Update password (mock)
        </button>
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Two-factor authentication</h2>
        <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginTop: 0 }}>
          TOTP or email OTP — enable flow not wired in demo.
        </p>
        <button type="button" className="btn">
          Enable 2FA (mock)
        </button>
        <span className="pill" style={{ marginLeft: 12 }}>
          Disabled
        </span>
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <h2 style={{ margin: 0, fontSize: "1rem" }}>Active sessions</h2>
          <button type="button" className="btn btn-danger">
            Sign out all others (mock)
          </button>
        </div>
        <table className="table" style={{ marginTop: "0.75rem" }}>
          <thead>
            <tr>
              <th>Browser</th>
              <th>OS</th>
              <th>Location</th>
              <th>Last active</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>
                  {s.browser}
                  {s.current ? (
                    <span className="pill pill-ok" style={{ marginLeft: 8 }}>
                      This device
                    </span>
                  ) : null}
                </td>
                <td>{s.os}</td>
                <td>{s.location}</td>
                <td>{s.lastActive}</td>
                <td>
                  {!s.current ? (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ padding: "0.25rem 0" }}
                      onClick={() => setSessions((prev) => prev.filter((x) => x.id !== s.id))}
                    >
                      Revoke
                    </button>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
