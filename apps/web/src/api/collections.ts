import { ApiError, apiFetch, readErrorMessage } from "./http";
import type { CollectionAnalyticsResponse, CollectionListResponse } from "./types";

export async function listCollections(accessToken: string): Promise<CollectionListResponse> {
  const res = await apiFetch("/api/v1/collections", { accessToken });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as CollectionListResponse;
}

export async function fetchCollectionAnalytics(
  accessToken: string,
  collectionId: string,
): Promise<CollectionAnalyticsResponse> {
  const res = await apiFetch(
    `/api/v1/collections/${encodeURIComponent(collectionId)}/analytics`,
    { accessToken },
  );
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as CollectionAnalyticsResponse;
}
