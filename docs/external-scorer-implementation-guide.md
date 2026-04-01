# External HTTP document scorer — implementation guide

This document is the **integration brief** for teams building a remote scorer that VerifiedSignal calls via **`SCORE_HTTP_URL`**. Operator-facing configuration, env vars, and persistence details live in **[`scoring-http.md`](scoring-http.md)**; this guide focuses on **contract**, **behavior**, and **checklists** for implementers.

---

## 1. Role in the system

- The **pipeline** always writes a **local heuristic** row first (`verifiedsignal_heuristic`).
- If **`ENQUEUE_SCORE_AFTER_PIPELINE=true`** and **`SCORE_ASYNC_BACKEND=http`**, the **ARQ worker** runs job **`score_document`**, which **`POST`s** one JSON request to **`SCORE_HTTP_URL`** and persists the result as a second row (`verifiedsignal_http`), unless idempotency says the work is already done.
- Your service is therefore an **optional second opinion**; it does **not** replace the heuristic unless the operator sets **`SCORE_API_PROMOTE_CANONICAL=true`**.

---

## 2. Transport and method

| Item | Requirement |
|------|-------------|
| **Method** | **`POST`** |
| **URL** | Configured by the operator as **`SCORE_HTTP_URL`** (full URL, e.g. `https://scorer.example.com/v1/score`) |
| **Request body** | **`application/json`** |
| **Response** | **`application/json`**; the worker sends **`Accept: application/json`** |
| **Auth** | Optional **`Authorization: Bearer <token>`** if **`SCORE_HTTP_BEARER_TOKEN`** is set on the worker |
| **Timeout** | Client-side timeout **`SCORE_HTTP_TIMEOUT_S`** (default **120s**); design for completion within that budget or tolerate retries |

---

## 3. Request contract (`schema_version` **1**)

```json
{
  "schema_version": 1,
  "document_id": "<uuid string>",
  "title": "<string|null>",
  "body_text": "<string, possibly truncated>",
  "body_text_truncated": <boolean>,
  "content_type": "<string|null>",
  "content_fingerprint": "<64-char hex string>"
}
```

**Semantics**

- **`body_text`** may be **truncated** to **`SCORE_HTTP_MAX_BODY_CHARS`** (default **12000**). When truncated, **`body_text_truncated`** is **`true`**.
- **`content_fingerprint`** is a **stable idempotency key**: same document and same body hash as used by the worker (prefer **`documents.content_sha256`** when present; otherwise **SHA-256 of UTF-8 `body_text`**). You may use it for caching or deduplication.

---

## 4. Success response (`schema_version` **1**)

- **HTTP status:** **`200`** only for a successful parseable score. Any other status is treated as failure (see §5).
- **Body:** JSON **object** (not an array).

**Required for the protocol**

| Field | Type | Rule |
|-------|------|------|
| **`schema_version`** | integer | Must be **`1`**. |

**Optional score fields** (each in **[0, 1]** if present; omitted or absent is allowed)

| Field | Meaning |
|-------|--------|
| **`factuality_score`** | Factuality / groundedness proxy |
| **`ai_generation_probability`** | Synthetic / LLM-like text proxy |
| **`fallacy_score`** | Logical / rhetorical risk proxy |
| **`confidence_score`** | Confidence in the above (or your chosen semantics) |

**Optional**

| Field | Type | Rule |
|-------|------|------|
| **`metadata`** | object | Arbitrary JSON; stored under **`score_payload.response.remote_metadata`**. |

**Extensions**

- Any **other top-level keys** are preserved in **`score_payload.response`** (for debugging or future UI).

---

## 5. HTTP behavior and worker semantics

| Outcome | Worker behavior |
|--------|------------------|
| **`200`** + JSON object + valid **`schema_version`** + scores in **[0, 1]** | Success → new **`document_scores`** row with **`job_status: completed`**. |
| **`408`, `429`, `5xx`**, network errors, timeouts | **Transient** → job **retries** (ARQ **`max_tries=5`**). |
| **`4xx`** (except **`408`** / **`429`** treated as retryable), invalid JSON, non-object JSON, wrong **`schema_version`**, scores outside **[0, 1]** | **Permanent** → **no retry**; terminal failure row with error message. |

**Idempotency:** If the worker already has a **`verifiedsignal_http`** row for this document with the same **`content_fingerprint`** and terminal status **`completed`** or **`failed_terminal`**, it **will not call** your service again.

---

## 6. Minimal functional behavior

1. **Accept** the request JSON above on the configured URL.
2. **Return** **`200`** with a JSON object including **`schema_version: 1`**.
3. Optionally return **one or more** of the four scalar scores in **[0, 1]** plus optional **`metadata`**.
4. **Stay within** the configured timeout; be **idempotent** for the same **`document_id`** + **`content_fingerprint`** (same result if called twice).
5. **Do not** rely on the worker following redirects for security-sensitive behavior; the worker calls **only** the URL the operator configured.

---

## 7. Non-goals (for this contract)

- **No** callback from VerifiedSignal to “register” your service beyond **`SCORE_HTTP_URL`**.
- **No** required streaming or batching protocol in this contract (batch is a separate pattern).
- **No** fixed path name (e.g. `/score`); the operator sets the **full URL**.

---

## 8. Reference implementation and tests

- **Reference scorer:** Minimal **FastAPI** app in **`scripts/reference_http_scorer/`** — run **`pdm run reference-http-scorer`**; see **[`scoring-http.md`](scoring-http.md)** (*Reference HTTP scorer*).
- **Tests:** `tests/unit/test_score_http_remote.py`, `tests/unit/test_reference_http_scorer_app.py`, `tests/integration/test_score_http_worker.py`.

---

## 9. Recommended integration patterns

1. **LLM APIs** — Chat Completions or Responses with a fixed JSON schema; map model output into the scalar columns + **`metadata.model`**.
2. **Provider REST** — Hive, GPTZero, Copyleaks, etc.; wrap each in a small adapter that normalizes to this response shape.
3. **On-prem / Hugging Face** — Sidecar HTTP service (transformers + GPU) exposing this contract; keeps the app worker thin and testable.
4. **Batch / queue** — For large corpora, use the same **`content_fingerprint`** and persistence model; batch systems can still normalize to this request/response for compatibility.

---

## 10. Planned: Bayesian fusion

The product may later **fuse** heuristic + HTTP scores (e.g. log-odds, priors). HTTP scorers should prefer **calibrated** or clearly documented probabilities if you want fusion to be meaningful. Design notes: **[`scoring-http.md`](scoring-http.md)** (*Planned: Bayesian fusion*).
