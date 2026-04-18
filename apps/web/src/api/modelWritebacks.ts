import { ApiError, apiFetch, readErrorMessage } from "./http";
import type { ModelActivityResponse, ModelWriteback, ModelWritebackListResponse } from "./types";

export async function listModelWritebacks(
  accessToken: string,
  modelId: string,
  params?: {
    artifact_kind?: string;
    verification_state?: string;
    version_id?: string;
    limit?: number;
    offset?: number;
  },
): Promise<ModelWritebackListResponse> {
  const sp = new URLSearchParams();
  if (params?.artifact_kind) sp.set("artifact_kind", params.artifact_kind);
  if (params?.verification_state) sp.set("verification_state", params.verification_state);
  if (params?.version_id) sp.set("version_id", params.version_id);
  if (params?.limit != null) sp.set("limit", String(params.limit));
  if (params?.offset != null) sp.set("offset", String(params.offset));
  const q = sp.toString();
  const path = `/api/v1/models/${encodeURIComponent(modelId)}/writebacks${q ? `?${q}` : ""}`;
  const res = await apiFetch(path, { accessToken });
  if (res.status === 404) throw new ApiError("Model not found", 404);
  if (!res.ok) throw new ApiError(await readErrorMessage(res), res.status);
  return (await res.json()) as ModelWritebackListResponse;
}

export async function createModelFinding(
  accessToken: string,
  modelId: string,
  body: { title: string; details?: string | null; model_version_id?: string | null },
): Promise<ModelWriteback> {
  const res = await apiFetch(
    `/api/v1/models/${encodeURIComponent(modelId)}/writebacks/findings`,
    { method: "POST", accessToken, jsonBody: body },
  );
  if (res.status === 404) throw new ApiError("Model not found", 404);
  if (!res.ok) throw new ApiError(await readErrorMessage(res), res.status);
  return (await res.json()) as ModelWriteback;
}

export async function patchWritebackVerification(
  accessToken: string,
  modelId: string,
  writebackId: string,
  body: { verification_state: string; review_note?: string | null },
): Promise<ModelWriteback> {
  const res = await apiFetch(
    `/api/v1/models/${encodeURIComponent(modelId)}/writebacks/${encodeURIComponent(writebackId)}/verification`,
    { method: "PATCH", accessToken, jsonBody: body },
  );
  if (res.status === 404) throw new ApiError("Not found", 404);
  if (!res.ok) throw new ApiError(await readErrorMessage(res), res.status);
  return (await res.json()) as ModelWriteback;
}

export async function fetchModelActivity(
  accessToken: string,
  modelId: string,
): Promise<ModelActivityResponse> {
  const res = await apiFetch(`/api/v1/models/${encodeURIComponent(modelId)}/activity`, {
    accessToken,
  });
  if (res.status === 404) throw new ApiError("Model not found", 404);
  if (!res.ok) throw new ApiError(await readErrorMessage(res), res.status);
  return (await res.json()) as ModelActivityResponse;
}
