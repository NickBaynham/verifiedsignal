import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/http";
import * as sessionAuth from "../api/sessionAuth";
import { useAuth } from "../context/AuthContext";
import { getApiBaseUrl, getDevLoginPrefill, isApiBackend } from "../config";

function initialEmail(apiMode: boolean): string {
  const p = getDevLoginPrefill();
  if (p) return p.email;
  if (!apiMode) return "demo@verifiedsignal.io";
  return "";
}

function initialPassword(): string {
  const p = getDevLoginPrefill();
  if (p) return p.password;
  return "";
}

type ApiAuthPanel = "signin" | "signup";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/dashboard";
  const apiMode = isApiBackend();

  const [panel, setPanel] = useState<ApiAuthPanel>("signin");
  const [email, setEmail] = useState(() => initialEmail(apiMode));
  const [password, setPassword] = useState(() => initialPassword());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to={from} replace />;
  }

  function setApiPanel(next: ApiAuthPanel) {
    setPanel(next);
    setError(null);
    setSuccess(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
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
      if (panel === "signup") {
        const { message } = await sessionAuth.signupWithPassword(email.trim(), password);
        setSuccess(message);
        await login(email.trim(), password);
        navigate(from, { replace: true });
        return;
      }
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Sign-in failed. Check the API and your credentials.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  const title = !apiMode ? "Sign in" : panel === "signup" ? "Create account" : "Sign in";
  const submitLabel = submitting
    ? panel === "signup"
      ? "Creating account…"
      : "Signing in…"
    : panel === "signup"
      ? "Create account & sign in"
      : "Continue to dashboard";

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>{title}</h1>
        <p className="sub">
          {apiMode ? (
            <>
              Live API at <code>{getApiBaseUrl()}</code> — <code>POST /auth/login</code> /{" "}
              <code>POST /auth/signup</code> (Supabase). httpOnly refresh on <code>/auth</code>.{" "}
              <code>CORS_ORIGINS</code> must include this origin (e.g. <code>http://127.0.0.1:5173</code>).
            </>
          ) : (
            <>
              Demo login — no server call. Matches the <code>/login</code> flow from the product spec; set{" "}
              <code>VITE_API_URL</code> to use FastAPI session auth.
            </>
          )}
        </p>
        {apiMode ? (
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              marginBottom: "1rem",
            }}
            role="tablist"
            aria-label="Authentication"
          >
            <button
              type="button"
              className={panel === "signin" ? "btn btn-primary" : "btn btn-ghost"}
              style={{ flex: 1 }}
              onClick={() => setApiPanel("signin")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={panel === "signup" ? "btn btn-primary" : "btn btn-ghost"}
              style={{ flex: 1 }}
              onClick={() => setApiPanel("signup")}
            >
              Sign up
            </button>
          </div>
        ) : null}
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
              autoComplete={apiMode && panel === "signup" ? "new-password" : "current-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {success ? <div className="success-text">{success}</div> : null}
            {error ? <div className="error-text">{error}</div> : null}
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
            {submitLabel}
          </button>
        </form>
        {apiMode && panel === "signin" ? (
          <p style={{ marginTop: "1.25rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Forgot password — use Supabase reset via <code>POST /auth/reset-password</code> (see API docs).
          </p>
        ) : null}
        {apiMode && panel === "signup" ? (
          <p style={{ marginTop: "1.25rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            After sign-up we sign you in immediately when Supabase allows password login. If email confirmation
            is required, check Inbucket / your mail catcher, then use <strong>Sign in</strong>.
          </p>
        ) : null}
      </div>
    </div>
  );
}
