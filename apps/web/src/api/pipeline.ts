import { ApiError, apiFetch, readErrorMessage } from "./http";
import type { DocumentPipelineResponse } from "./types";

export async function fetchDocumentPipeline(
  accessToken: string,
  documentId: string,
): Promise<DocumentPipelineResponse> {
  const res = await apiFetch(`/api/v1/documents/${encodeURIComponent(documentId)}/pipeline`, {
    accessToken,
  });
  if (!res.ok) {
    throw new ApiError(await readErrorMessage(res), res.status);
  }
  return (await res.json()) as DocumentPipelineResponse;
}
