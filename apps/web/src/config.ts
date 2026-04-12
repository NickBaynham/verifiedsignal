/** Trailing slashes stripped; empty string → mock-only UI. */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL;
  if (raw == null || String(raw).trim() === "") return "";
  return String(raw).replace(/\/+$/, "");
}

export function isApiBackend(): boolean {
  return getApiBaseUrl() !== "";
}

/**
 * Vite dev server + API mode: prefill login with the same defaults as the API’s
 * VERIFIEDSIGNAL_DEV_BOOTSTRAP_AUTH_* (see root `.env.example`). Optional overrides:
 * VITE_DEV_LOGIN_EMAIL, VITE_DEV_LOGIN_PASSWORD.
 */
export function getDevLoginPrefill(): { email: string; password: string } | null {
  if (!import.meta.env.DEV || !isApiBackend()) return null;
  const envEmail = String(import.meta.env.VITE_DEV_LOGIN_EMAIL ?? "").trim();
  const envPassword = String(import.meta.env.VITE_DEV_LOGIN_PASSWORD ?? "").trim();
  return {
    email: envEmail || "dev@example.com",
    password: envPassword || "devpassword123",
  };
}
