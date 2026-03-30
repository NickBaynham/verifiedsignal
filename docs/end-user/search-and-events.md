# Search and live updates

## Search (`GET /api/v1/search`)

### Query parameters

| Parameter | Description |
|-----------|-------------|
| **`q`** | Search text (optional; up to 2000 characters). Empty **`q`** runs a **match-all** query (still subject to filters and **`limit`**). |
| **`limit`** | Hits to return (1–100, default 10). |
| **`collection_id`** | Optional UUID. **When you send a valid Bearer token**, narrows results to that collection; must be one you can access (**403** if not). Ignored when unauthenticated (callers without a token cannot scope by arbitrary collections). |
| **`content_type`** | Exact match on indexed MIME type (e.g. `text/plain`, `application/pdf`). |
| **`status`** | Exact match on document pipeline status (e.g. `completed`, `queued`). |
| **`ingest_source`** | `upload` or `url` — how the document entered the system (derived from **`document_sources`**). |
| **`tags`** | Repeat the parameter for **AND** semantics: `?tags=a&tags=b` requires both tags (from **`user_metadata.tags`** at intake). |
| **`include_facets`** | If `true`, the response includes **`facets`** — bucket counts for **`ingest_source`**, **`status`**, **`content_type`**, and **`tags`** over the current query + filters. |

### Auth and visibility

- **No `Authorization` header:** search behaves like early phases — **no collection ACL** is applied (same global index visibility as before). Do not expose unauthenticated search to confidential corpora.
- **Valid Bearer JWT:** results are limited to documents in **collections your account can access**. Optional **`collection_id`** further narrows within that set.

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

**Auth today:** like search, this route uses a **placeholder** optional principal—connections are not yet restricted per user in code you ship today. **Do not rely on this for confidential data** until your deployment adds real auth on the stream.

### What you will see

1. First, a **`connected`** event (JSON with `type` and empty `payload`).
2. Later, JSON lines with:
   - **`type`** — event name (for example **`document_queued`** after a successful file upload enqueue)
   - **`payload`** — structured details (e.g. `document_id`, `job_id`, `storage_key`)
   - **`ts`** — UTC timestamp
   - **`environment`** — server environment label

Events are broadcast **in memory** on a single API instance. Multi-server deployments will need a shared bus (for example Redis) for all users to see the same events—your operator’s roadmap.

### Using SSE in the browser

```javascript
const es = new EventSource(`${API_BASE}/api/v1/events/stream`);
es.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  console.log(msg.type, msg.payload);
};
```

Handle **`onerror`** to reconnect with backoff if the network drops.

## Next steps

- [Status and troubleshooting](status-and-troubleshooting.md)
- [Documents](documents.md)
