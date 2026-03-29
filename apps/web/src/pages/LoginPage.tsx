import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useDemoAuth } from "../context/DemoAuthContext";

export function LoginPage() {
  const { user, login } = useDemoAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/dashboard";

  const [email, setEmail] = useState("demo@verifiedsignal.io");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (user) {
    return <Navigate to={from} replace />;
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 3) {
      setError("Use any password with at least 3 characters (demo validation).");
      return;
    }
    login(email, password);
    navigate(from, { replace: true });
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>Sign in</h1>
        <p className="sub">
          Demo login — no server call. Matches the <code>/login</code> flow from the product spec; production will use
          FastAPI + Supabase with httpOnly refresh.
        </p>
        <form onSubmit={onSubmit}>
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
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>
            Continue to dashboard
          </button>
        </form>
        <p style={{ marginTop: "1.25rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
          Forgot password — hook to Supabase reset via <code>VITE_SUPABASE_*</code> when wired.
        </p>
      </div>
    </div>
  );
}
