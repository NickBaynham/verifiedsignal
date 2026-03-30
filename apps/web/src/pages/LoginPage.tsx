import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { getApiBaseUrl, isApiBackend } from "../config";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/dashboard";
  const apiMode = isApiBackend();

  const [email, setEmail] = useState("demo@verifiedsignal.io");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to={from} replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!apiMode) {
      if (password.length < 3) {
        setError("Use any password with at least 3 characters (demo validation).");
        return;
      }
      await login(email, password);
      navigate(from, { replace: true });
      return;
    }
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Sign-in failed. Check the API and your credentials.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>Sign in</h1>
        <p className="sub">
          {apiMode ? (
            <>
              Live API at <code>{getApiBaseUrl()}</code> — uses <code>POST /auth/login</code> (Supabase-backed)
              and httpOnly refresh on <code>/auth</code>. Ensure <code>CORS_ORIGINS</code> includes this SPA origin.
            </>
          ) : (
            <>
              Demo login — no server call. Matches the <code>/login</code> flow from the product spec; set{" "}
              <code>VITE_API_URL</code> to use FastAPI session auth.
            </>
          )}
        </p>
        <form onSubmit={(e) => void onSubmit(e)}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {error ? <div className="error-text">{error}</div> : null}
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
            {submitting ? "Signing in…" : "Continue to dashboard"}
          </button>
        </form>
        <p style={{ marginTop: "1.25rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
          Forgot password — use Supabase reset via <code>POST /auth/reset-password</code> (see API docs).
        </p>
      </div>
    </div>
  );
}
