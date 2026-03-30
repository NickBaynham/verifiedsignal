/** Trailing slashes stripped; empty string → mock-only UI. */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL;
  if (raw == null || String(raw).trim() === "") return "";
  return String(raw).replace(/\/+$/, "");
}

export function isApiBackend(): boolean {
  return getApiBaseUrl() !== "";
}
