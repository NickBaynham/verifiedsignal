import { ApiError, apiFetch, readErrorMessage } from "./http";

export interface AccessTokenPayload {
  access_token: string;
  expires_in: number;
  token_type?: string;
}

export async function loginWithPassword(
  email: string,
  password: string,
): Promise<AccessTokenPayload> {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    jsonBody: { email, password },
    credentials: "include",
  });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as AccessTokenPayload;
}

export async function refreshAccessToken(): Promise<AccessTokenPayload | null> {
  const res = await apiFetch("/auth/refresh", {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) return null;
  return (await res.json()) as AccessTokenPayload;
}

export async function logoutSession(): Promise<void> {
  const res = await apiFetch("/auth/logout", {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok && res.status !== 204) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
}
