# HTTP remote document scorer

When **`ENQUEUE_SCORE_AFTER_PIPELINE=true`**, the pipeline can enqueue the ARQ job **`score_document`**. That job writes an extra **`document_scores`** row using either:

- **`SCORE_ASYNC_BACKEND=stub`** — non-canonical placeholder (**`verifiedsignal_stub`**), or  
- **`SCORE_ASYNC_BACKEND=http`** — POST to **`SCORE_HTTP_URL`** (**`verifiedsignal_http`**).

The pipeline’s **`score`** stage **always** writes a **canonical** heuristic row (**`verifiedsignal_heuristic`**) first. The async job **adds** a second opinion unless you promote the HTTP row (see below).

## Environment variables

| Variable | Meaning |
|----------|---------|
| **`ENQUEUE_SCORE_AFTER_PIPELINE`** | If **`true`**, enqueue **`score_document`** after the scaffold pipeline. |
| **`SCORE_ASYNC_BACKEND`** | **`stub`** (default) or **`http`**. |
| **`SCORE_HTTP_URL`** | HTTPS (or HTTP in dev) endpoint for **`POST`** JSON. Required for real HTTP scoring. If **`http`** and empty, the worker falls back to a stub row with an explanatory note. |
| **`SCORE_HTTP_BEARER_TOKEN`** | Optional **`Authorization: Bearer …`** sent to the remote service. |
| **`SCORE_HTTP_TIMEOUT_S`** | Client timeout seconds (default **120**). |
| **`SCORE_HTTP_MAX_BODY_CHARS`** | Truncate **`body_text`** in the request (default **12000**). |
| **`SCORE_HTTP_SCORER_VERSION`** | Stored on each row as **`scorer_version`** (default **`1.0.0`**). Bump when your remote contract changes. |
| **`SCORE_API_PROMOTE_CANONICAL`** | If **`true`**, a **successful** HTTP score **demotes all existing scores** for the document and sets the new HTTP row **`is_canonical=true`**. Default **`false`**. |

## ARQ retries

The **`score_document`** task is registered with **`max_tries=5`**. **Transient** failures (timeouts, connection errors, HTTP **408**, **429**, **5xx**) **roll back** the DB session and **re-raise** so ARQ retries. **Permanent** failures (HTTP **4xx** except retryable codes, invalid JSON, schema mismatch) insert a **`failed_terminal`** row and **complete** the job without retry.

## Idempotency

Before calling the remote service, the worker checks for an existing **`verifiedsignal_http`** row whose **`score_payload.content_fingerprint`** matches the current document and whose **`score_payload.job_status`** is **`completed`** or **`failed_terminal`**. If found, the job **skips** the HTTP call (safe when ARQ retries after a successful commit).

**Fingerprint:** `documents.content_sha256` (hex) when set; otherwise **SHA-256** of UTF-8 **`body_text`**.

## Request JSON (`schema_version` **1**)

```json
{
  "schema_version": 1,
  "document_id": "uuid",
  "title": "string or null",
  "body_text": "possibly truncated",
  "body_text_truncated": false,
  "content_type": "string or null",
  "content_fingerprint": "64-char hex"
}
```

## Response JSON (`schema_version` **1**)

HTTP **200** with a JSON object:

| Field | Type | Notes |
|-------|------|--------|
| **`schema_version`** | int | Must be **1**. |
| **`factuality_score`** | number \| omit | **[0, 1]** |
| **`ai_generation_probability`** | number \| omit | **[0, 1]** |
| **`fallacy_score`** | number \| omit | **[0, 1]** |
| **`confidence_score`** | number \| omit | **[0, 1]** |
| **`metadata`** | object \| omit | Stored under **`score_payload.response.remote_metadata`**. |

Any other top-level keys are copied into **`score_payload.response`**.

## `score_payload` semantics (HTTP rows)

| Path | Meaning |
|------|---------|
| **`kind`** | **`http_remote_v1`** |
| **`job_status`** | **`completed`** \| **`failed_terminal`** |
| **`content_fingerprint`** | Idempotency key (see above). |
| **`latency_ms`** | Round-trip time when **`completed`**. |
| **`error`** | Message when **`failed_terminal`**. |
| **`request`** | Subset of outbound request (schema version, truncation flag). |
| **`response`** | Parsed extras + **`parsed_scores`** mirror of column mapping. |

Stub rows use **`kind: stub`**, **`job_status: completed`**, and **`note`**.

## Recommended next scorers

1. **OpenAI / Anthropic** — Chat Completions or Responses API with a fixed JSON schema; map model output into the same scalar columns + **`metadata.model`**.  
2. **Provider-specific REST** — e.g. Hive, GPTZero, Copyleaks; wrap each as a small adapter that normalizes to this response shape.  
3. **On-prem / Hugging Face** — Run a sidecar HTTP service (transformers + GPU) exposing this contract; keeps the app worker thin and testable.  
4. **Batch / queue** — For large corpora, enqueue scoring jobs with **`content_fingerprint`** only and let an external batch system callback or poll (still use the same persistence model).

## Tests

- **Unit:** `tests/unit/test_score_http_remote.py`  
- **Integration (Postgres + mocked HTTP):** `tests/integration/test_score_http_worker.py`
