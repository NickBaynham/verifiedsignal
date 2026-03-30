# Search and live updates

## Search (`GET /api/v1/search`)

**Query parameters:**

- **`q`** — search text (can be empty; up to 2000 characters). Empty **`q`** returns a limited **match-all** slice of the index (useful for sanity checks, not a full catalog API).
- **`limit`** — number of hits (1–100, default 10).

**Auth:** the route accepts calls **with or without** a Bearer token today; results are **not** filtered per user in this phase—treat deployments accordingly until ACL-aware search is added.

### How results are produced

1. When a document is **uploaded** or ingested by URL, raw bytes live in **object storage**.
2. The **worker** runs the **`extract`** pipeline stage: it reads those bytes and, for common **text-like** types (`text/plain`, `text/markdown`, `application/json`, `text/html`, other `text/*`, and a small UTF-8 heuristic), stores **plain text** in Postgres as **`documents.body_text`**.
3. The **`index`** stage sends **title**, **`body_text`**, **collection id**, and **status** to **OpenSearch** under the index name from **`OPENSEARCH_INDEX_NAME`** (default **`verifiedsignal_documents`**).
4. **`GET /api/v1/search`** runs a **keyword** query (`multi_match` on **title** and **body_text**).

**Vectors / semantic search** are not implemented yet; the same pipeline can be extended later (separate dense-vector field + kNN query).

### Index status in the JSON response

| `index_status` | Meaning |
|----------------|---------|
| **`ok`** | OpenSearch returned HTTP 200 for the search request. |
| **`fake`** | **`USE_FAKE_OPENSEARCH=true`** (typical in automated tests): in-memory index, substring match. |
| **`error`** | OpenSearch error (see **`message`**). |

Each hit includes **`document_id`**, **`title`**, **`score`**, and a short **`snippet`** from the body.

### Viewing extracted text

**`GET /api/v1/documents/{id}`** includes **`body_text`** when the worker has finished **extract** (may be **`null`** for unsupported binaries or before the pipeline runs).

### Operations requirements

- **Worker** must run (`pdm run worker`) with **`USE_FAKE_QUEUE=false`** so **`process_document`** jobs execute after intake.
- **OpenSearch** must be reachable at **`OPENSEARCH_URL`** (for example Compose service on port **9200**), unless you use **`USE_FAKE_OPENSEARCH=true`** (dev/tests only).

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
