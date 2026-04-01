# Search and live updates

## Search (`GET /api/v1/search`)

### Query parameters

| Parameter | Description |
|-----------|-------------|
| **`q`** | Search text (optional; up to 2000 characters). Empty **`q`** runs a **match-all** query (still subject to filters and **`limit`**). |
| **`limit`** | Hits to return (1–100, default 10). |
| **`collection_id`** | Optional UUID. Must be a collection you can access (**403** if not). |
| **`content_type`** | Exact match on indexed MIME type (e.g. `text/plain`, `application/pdf`). |
| **`status`** | Exact match on document pipeline status (e.g. `completed`, `queued`). |
| **`ingest_source`** | `upload` or `url` — how the document entered the system (derived from **`document_sources`**). |
| **`tags`** | Repeat the parameter for **AND** semantics: `?tags=a&tags=b` requires both tags (from **`user_metadata.tags`** at intake). |
| **`include_facets`** | If `true`, the response includes **`facets`** — bucket counts for **`ingest_source`**, **`status`**, **`content_type`**, and **`tags`** over the current query + filters. |

### Auth and visibility

- **Default (`VERIFIEDSIGNAL_REQUIRE_AUTH_SEARCH=true`):** **`Authorization: Bearer <access_token>`** is **required**. Without it, the API returns **401**. Results are limited to documents in **collections your account can access**. Optional **`collection_id`** further narrows within that set.
- **Legacy / local demos:** operators may set **`VERIFIEDSIGNAL_REQUIRE_AUTH_SEARCH=false`**. Then calls **without** a Bearer token skip collection filtering (global index visibility). **Do not use in production** for confidential corpora.

Invalid or expired Bearer tokens receive **401**.

### How results are produced

1. On **upload** or **URL** intake, optional **`metadata`** JSON is stored in Postgres as **`documents.user_metadata`** (convention: **`tags`** string array, **`label`** string).
2. The worker **extract** stage fills **`documents.body_text`** (and binary extractors where configured).
3. The **index** stage writes an OpenSearch document with: **`title`**, **`body_text`**, **`metadata_text`** (flattened primitive values from **`user_metadata`** for full-text), **`collection_id`**, **`status`**, **`content_type`**, **`original_filename`**, **`ingest_source`** (`upload` \| `url`), **`tags`**, **`metadata_label`**.
4. **`GET /api/v1/search`** runs a **`bool`** query: **must** clause is **`multi_match`** on **`title`**, **`body_text`**, **`metadata_text`** (when **`q`** is non-empty), or **`match_all`**; **filter** clauses apply the metadata parameters above.

**Semantic / vector search** is not implemented yet; the index can be extended later (dense vector + kNN).

### Response shape

| Field | Meaning |
|-------|---------|
| **`query`**, **`limit`** | Echo. |
| **`hits`** | Each hit includes **`document_id`**, **`title`**, **`score`**, **`snippet`**, and when indexed **`collection_id`**, **`ingest_source`**, **`content_type`**, **`status`**, **`tags`**, **`metadata_label`**. |
| **`total`** | Total matching documents (track-total-hits style in OpenSearch). |
| **`index_status`** | `ok` \| `fake` \| `error` |
| **`message`** | Error detail when **`index_status`** is **`error`**. |
| **`facets`** | Present when **`include_facets=true`**: object with keys **`ingest_source`**, **`status`**, **`content_type`**, **`tags`**; each maps to a list of `{ "key", "count" }`. |

### Index status values

| `index_status` | Meaning |
|----------------|---------|
| **`ok`** | OpenSearch returned HTTP 200. |
| **`fake`** | **`USE_FAKE_OPENSEARCH=true`**: in-memory index (substring match on text fields). |
| **`error`** | OpenSearch error (see **`message`**). |

### Viewing extracted text and metadata

**`GET /api/v1/documents/{id}`** includes **`body_text`** and **`user_metadata`** when available.

### Operations requirements

- **Worker** must run (`pdm run worker`) with **`USE_FAKE_QUEUE=false`** so **`process_document`** runs after intake.
- **OpenSearch** at **`OPENSEARCH_URL`**, or **`USE_FAKE_OPENSEARCH=true`** for tests.
- After upgrading mappings, existing OpenSearch indices may need a **mapping merge** (the app attempts a merge on startup paths) or a **reindex** in production — see operator notes in **`db/README.md`** (migration **005** adds **`user_metadata`** in Postgres).

## Live updates (Server-Sent Events)

**`GET /api/v1/events/stream`**

Returns a **text/event-stream** (SSE) connection. Your client should use **`EventSource`** (browser) or an SSE-capable HTTP client.

### Authentication

- **Default (`VERIFIEDSIGNAL_REQUIRE_AUTH_SSE=true`):** you must prove identity with either:
  - **`Authorization: Bearer <access_token>`**, or
  - **`?access_token=<JWT>`** on the URL (required for browser **`EventSource`**, which cannot set custom headers).

Missing or invalid tokens → **401**.

- **Legacy:** **`VERIFIEDSIGNAL_REQUIRE_AUTH_SSE=false`** allows anonymous connections (all events on the shared channel; not suitable for multi-tenant production).

### Tenancy

When auth is enabled, the stream only delivers events whose **`payload.auth_sub`** matches the subscriber’s JWT **`sub`** (for example **`document_queued`** after your own upload). Other users’ events are not sent on your connection.

### What you will see

1. First, a **`connected`** event (JSON with `type` and empty `payload`).
2. Later, JSON lines with:
   - **`type`** — event name (for example **`document_queued`** after a successful file upload enqueue)
   - **`payload`** — structured details (e.g. `document_id`, `job_id`, `storage_key`, `auth_sub`)
   - **`ts`** — UTC timestamp
   - **`environment`** — server environment label

Events are published to **Redis pub/sub** (channel from **`EVENT_PUBSUB_CHANNEL`**, default **`verifiedsignal:sse`**) using **`REDIS_URL`**, the same broker as ARQ. Every API replica subscribes to that channel, so **`EventSource`** clients attached to any instance receive the same JSON lines (**`connected`**, then tenant-filtered events). For tests or single-process dev without Redis, set **`USE_FAKE_EVENT_HUB=true`** to use an in-process hub instead.

### Using SSE in the browser

```javascript
const token = "<access_token>";
const es = new EventSource(
  `${API_BASE}/api/v1/events/stream?access_token=${encodeURIComponent(token)}`,
  { withCredentials: true },
);
es.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  console.log(msg.type, msg.payload);
};
```

Handle **`onerror`** to reconnect with backoff if the network drops.

**Cross-origin SPAs:** the stream must be on the same **`VITE_API_URL`** origin you call for JSON APIs, or the browser will block **`EventSource`**. The React app under **`apps/web`** passes **`access_token`** as a query parameter when opening the stream.

**Security note:** query parameters can appear in logs and Referer headers. Use **short-lived access tokens**, **HTTPS only**, and avoid leaking URLs.

### Pipeline polling (worker progress)

The worker runs in a **separate process** from the API, so stage transitions are persisted in **`pipeline_runs`** / **`pipeline_events`** rather than only in the in-memory SSE hub.

- **`GET /api/v1/documents/{document_id}/pipeline`** — latest run plus ordered events for the document (requires Bearer JWT and document visibility). Use short-interval polling from the Upload/Dashboard UI until **`document_status`** is **`completed`** or **`failed`**.

## Collection analytics

**`GET /api/v1/collections/{collection_id}/analytics`** (Bearer required, collection must be accessible):

- **`facets`** — bucket counts from the search index (**`ingest_source`**, **`status`**, **`content_type`**, **`tags`**) for documents in that collection (same filter stack as search).
- **`postgres`** — rollups over **canonical** **`document_scores`**: averages, **`scored_documents`**, and a simple **suspicious** count (high AI proxy or low factuality heuristic).

## Next steps

- [Status and troubleshooting](status-and-troubleshooting.md)
- [Documents](documents.md)
