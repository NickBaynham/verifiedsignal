import { ApiError, apiFetch, readErrorMessage } from "./http";
import type { DocumentDetail, DocumentListResponse, IntakeResponse, UrlIntakeResponse } from "./types";

export async function listDocuments(
  accessToken: string,
  params: { limit?: number; offset?: number } = {},
): Promise<DocumentListResponse> {
  const sp = new URLSearchParams();
  if (params.limit != null) sp.set("limit", String(params.limit));
  if (params.offset != null) sp.set("offset", String(params.offset));
  const q = sp.toString();
  const path = q ? `/api/v1/documents?${q}` : "/api/v1/documents";
  const res = await apiFetch(path, { accessToken });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as DocumentListResponse;
}

export async function getDocument(accessToken: string, documentId: string): Promise<DocumentDetail> {
  const res = await apiFetch(`/api/v1/documents/${encodeURIComponent(documentId)}`, { accessToken });
  if (res.status === 404) {
    throw new ApiError("Document not found", 404);
  }
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as DocumentDetail;
}

export async function uploadDocumentFile(
  accessToken: string,
  file: File,
  options: { collectionId?: string; title?: string } = {},
): Promise<IntakeResponse> {
  const fd = new FormData();
  fd.append("file", file, file.name);
  if (options.collectionId) fd.append("collection_id", options.collectionId);
  if (options.title) fd.append("title", options.title);
  const res = await apiFetch("/api/v1/documents", {
    method: "POST",
    accessToken,
    body: fd,
    isFormData: true,
  });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as IntakeResponse;
}

export async function ingestDocumentFromUrl(
  accessToken: string,
  payload: { url: string; collection_id?: string | null; title?: string | null },
): Promise<UrlIntakeResponse> {
  const res = await apiFetch("/api/v1/documents/from-url", {
    method: "POST",
    accessToken,
    jsonBody: payload,
  });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as UrlIntakeResponse;
}
