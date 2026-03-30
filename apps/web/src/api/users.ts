import { ApiError, apiFetch, readErrorMessage } from "./http";

export interface UserMe {
  user_id: string;
  database_user_id: string | null;
  email: string | null;
  display_name: string | null;
}

export async function fetchCurrentUser(accessToken: string): Promise<UserMe> {
  const res = await apiFetch("/api/v1/users/me", { accessToken });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as UserMe;
}
