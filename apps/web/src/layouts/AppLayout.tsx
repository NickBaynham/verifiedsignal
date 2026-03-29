import { NavLink, Outlet } from "react-router-dom";
import { useDemoAuth } from "../context/DemoAuthContext";

const nav = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/library/upload", label: "Upload" },
  { to: "/collections", label: "Collections" },
  { to: "/search", label: "Search" },
  { to: "/reports/new", label: "Reports" },
  { to: "/account/billing", label: "Billing" },
  { to: "/account/security", label: "Security" },
];

export function AppLayout() {
  const { user, logout } = useDemoAuth();

  return (
    <div className="layout-root">
      <aside className="sidebar">
        <div className="sidebar-brand">
          Verified<span>Signal</span>
        </div>
        <nav className="sidebar-nav">
          {nav.map(({ to, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : "")}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div style={{ marginBottom: 8 }}>{user?.email}</div>
          <button type="button" className="btn btn-ghost" style={{ padding: "0.35rem 0" }} onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <div className="main-wrap">
        <div className="demo-banner">
          <strong>UI demo</strong> — Data is mocked for stakeholder review. Wire to{" "}
          <code style={{ fontFamily: "var(--font-mono)" }}>VITE_API_URL</code> when backend endpoints are ready
          (see use case spec API section).
        </div>
        <div className="main-inner">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
