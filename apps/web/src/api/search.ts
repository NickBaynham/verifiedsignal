import { ApiError, apiFetch, readErrorMessage } from "./http";
import type { SearchResponse } from "./types";

export type SearchDocumentsParams = {
  q: string;
  limit?: number;
  collectionId?: string;
  contentType?: string;
  status?: string;
  ingestSource?: "" | "upload" | "url";
  tags?: string[];
  includeFacets?: boolean;
};

export async function searchDocuments(
  accessToken: string | null,
  params: SearchDocumentsParams,
): Promise<SearchResponse> {
  const sp = new URLSearchParams();
  sp.set("q", params.q);
  if (params.limit != null) sp.set("limit", String(params.limit));
  if (params.collectionId) sp.set("collection_id", params.collectionId);
  if (params.contentType?.trim()) sp.set("content_type", params.contentType.trim());
  if (params.status?.trim()) sp.set("status", params.status.trim());
  if (params.ingestSource) sp.set("ingest_source", params.ingestSource);
  for (const t of params.tags ?? []) {
    const s = t.trim();
    if (s) sp.append("tags", s);
  }
  if (params.includeFacets) sp.set("include_facets", "true");

  const res = await apiFetch(`/api/v1/search?${sp.toString()}`, {
    accessToken: accessToken ?? undefined,
  });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as SearchResponse;
}
