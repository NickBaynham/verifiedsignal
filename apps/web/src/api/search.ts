import { ApiError, apiFetch, readErrorMessage } from "./http";
import type { SearchResponse } from "./types";

export async function searchDocuments(
  accessToken: string | null,
  params: { q: string; limit?: number; collectionId?: string },
): Promise<SearchResponse> {
  const sp = new URLSearchParams();
  sp.set("q", params.q);
  if (params.limit != null) sp.set("limit", String(params.limit));
  if (params.collectionId) sp.set("collection_id", params.collectionId);
  const res = await apiFetch(`/api/v1/search?${sp.toString()}`, {
    accessToken: accessToken ?? undefined,
  });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as SearchResponse;
}
