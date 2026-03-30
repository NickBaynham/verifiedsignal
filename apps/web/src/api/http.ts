import { getApiBaseUrl } from "../config";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown = undefined) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function joinApiUrl(root: string, path: string): string {
  const r = root.replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${r}${p}`;
}

function parseJsonSafe(text: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export interface ApiFetchOptions {
  method?: string;
  accessToken?: string | null;
  /** When set, body is sent as JSON (unless isFormData is true). */
  jsonBody?: unknown;
  body?: BodyInit | null;
  isFormData?: boolean;
  credentials?: RequestCredentials;
}

/**
 * `path` is absolute from API host, e.g. `/api/v1/documents` or `/auth/login`.
 */
export async function apiFetch(path: string, opts: ApiFetchOptions = {}): Promise<Response> {
  const root = getApiBaseUrl();
  if (!root) {
    throw new ApiError("VITE_API_URL is not set", 0);
  }
  const url = joinApiUrl(root, path);
  const headers = new Headers();
  if (opts.accessToken) {
    headers.set("Authorization", `Bearer ${opts.accessToken}`);
  }
  let body: BodyInit | undefined;
  if (opts.isFormData && opts.body != null) {
    body = opts.body as BodyInit;
  } else if (opts.jsonBody !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(opts.jsonBody);
  } else if (opts.body != null) {
    body = opts.body as BodyInit;
  }
  return fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body,
    // API may be on another origin (Vite dev); httpOnly refresh cookie must be sent to `/auth/*`.
    credentials: opts.credentials ?? "include",
  });
}

export async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  const parsed = parseJsonSafe(text);
  if (parsed && typeof parsed === "object" && parsed !== null && "detail" in parsed) {
    const d = (parsed as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return JSON.stringify(d);
  }
  if (typeof parsed === "string" && parsed.trim()) return parsed;
  return res.statusText || `HTTP ${res.status}`;
}
