# Documents

All routes below require **`Authorization: Bearer <access_token>`** unless noted.

## Listing documents

**`GET /api/v1/documents`**

**Query parameters (optional):**

- **`limit`** — default 50, maximum 200
- **`offset`** — for pagination (starts at 0)

**Response (JSON):**

- **`items`** — summaries (id, collection, title, status, filenames, sizes, errors if any, timestamps)
- **`total`** — number of documents you can access (subject to the same rules as the list)
- **`user_id`** — your JWT subject

You only see documents in **collections your account can access** (see [Workspace and collections](workspace-and-collections.md)).

## Uploading a file

**`POST /api/v1/documents`**  
**Content-Type:** `multipart/form-data`

**Form fields:**

| Field | Required | Description |
|--------|----------|-------------|
| **`file`** | yes | The file to store |
| **`collection_id`** | no* | UUID string of the target collection |
| **`title`** | no | Display title; defaults to the filename |
| **`metadata`** | no | JSON **object** as a string, e.g. `{"tags":["finance"],"label":"Q1"}`. Stored on **`user_metadata`** and used for search filters/facets after indexing. |

\*If your deployment disables the default-collection shortcut, **`collection_id` becomes required**—the API will say so in the error message.

**Success response (JSON):**

- **`document_id`**
- **`status`** — typically **`queued`** once the file is in object storage and processing is scheduled
- **`storage_key`** — internal object key
- **`job_id`** — background job id when enqueue succeeded
- **`enqueue_error`** — present if the row was stored but the job could not be enqueued (retry may be operator-dependent)

**Possible errors:**

- **400** — validation (empty file, missing filename, bad collection id, over size limit, etc.)
- **502** — object storage failure; response may include **`document_id`** for support

## Submitting a document by URL

**`POST /api/v1/documents/from-url`**  
**Content-Type:** `application/json`

**Body (JSON):**

| Field | Required | Description |
|--------|----------|-------------|
| **`url`** | yes | HTTPS URL to fetch (HTTP may be allowed only in some dev setups) |
| **`collection_id`** | no* | Same as file upload |
| **`title`** | no | Overrides title inferred from the URL path |
| **`metadata`** | no | Same convention as multipart **`metadata`** (JSON object); stored on **`user_metadata`**. |

\*Same **`collection_id`** rules as multipart upload.

**Response status:** **202 Accepted** (the server accepted the job; bytes are not necessarily downloaded yet).

**Response (JSON):**

- **`document_id`**
- **`status`** — **`created`** until the worker has fetched and stored the file
- **`source_url`** — normalized URL recorded for audit
- **`job_id`** — **`fetch_url_and_ingest`** job when enqueue succeeded
- **`enqueue_error`** — if enqueue failed

**What you should do:** poll **`GET /api/v1/documents/{document_id}`** until **`status`** becomes **`queued`**, **`failed`**, or progresses further. If **`failed`**, read **`ingest_error`**.

**Security:** the server blocks many unsafe URLs (private networks, embedded passwords in the URL, etc.). If you get **400**, the message explains the rule. Full technical notes: [`../url-ingest.md`](../url-ingest.md).

## Local folder ingestion (VerifiedSignal web app)

The HTTP API has **no** “watch this server directory” or “sync this UNC path” operation. The **React app** (`apps/web`, route **`/library/upload`** → **Local folder** tab) adds a **client-side** workflow on top of the same endpoints as normal uploads:

| Action | API used |
|--------|----------|
| Add or replace a file in the tree | **`POST /api/v1/documents`** (multipart), with **`title`** set to the file’s **relative path** inside the chosen folder so lists stay readable. |
| Remove a document when the file disappeared locally, or before replacing a changed file | **`DELETE /api/v1/documents/{document_id}`** |

**How sync works in the browser**

1. The user selects a folder (either **Choose folder…** via `webkitdirectory`, or **Grant folder access** via **`showDirectoryPicker`** where supported).
2. The app walks the tree and builds a list of **`{ relativePath, file }`** entries.
3. It keeps a small index in **`localStorage`** (key **`verifiedsignal:localDirSync:v1`**) keyed by **folder root name**, mapping each **`relativePath`** to **`document_id`**, **`lastModified`**, and **`size`**.
4. On **Sync now** (or **Auto-sync every 60s** when a directory handle is held in Chromium), the app: uploads paths not yet indexed; **deletes** then **re-uploads** when **`lastModified`** or **`size`** changed; **deletes** API documents for paths that no longer exist under the folder.

**Operator / user expectations**

- This is **not** multi-user server sync; clearing site data or another browser loses the index (documents in Postgres remain until deleted manually or by a new sync from a fresh index).
- **Chromium-class** browsers can **re-read** the same folder without re-picking and can run **periodic** sync. Other browsers can still **Choose folder…** each time; each run compares the new file list to the stored map (same **`rootName`** bucket) and applies adds/removes/updates.
- **`collection_id`** / **`metadata`** are not set by the folder UI today (same defaults as omitting them on a single-file form). If your deployment **requires** **`collection_id`**, use single-file upload or extend the client.

See also [Getting started](getting-started.md).

## Opening one document

**`GET /api/v1/documents/{document_id}`**  
`document_id` is a UUID.

**Response (JSON):** same fields as list items, plus **`user_metadata`** (client JSON from intake), **`sources`** — provenance rows (e.g. **`upload`**, **`url`**) with locators, MIME types, and byte lengths when known, **`body_text`** when extract has run, and optional **`canonical_score`** (the row with **`is_canonical=true`**: usually pipeline **`verifiedsignal_heuristic`**, or **`verifiedsignal_http`** if your deployment sets **`SCORE_API_PROMOTE_CANONICAL=true`** after a successful async score — see **[`../scoring-http.md`](../scoring-http.md)**).

**`GET /api/v1/documents/{document_id}/pipeline`** — latest **`pipeline_runs`** row and **`pipeline_events`** for polling worker progress (same auth rules as the document GET).

**404** means the id does not exist **or** you do not have access.

## Downloading the original file

**`GET /api/v1/documents/{document_id}/file`**

Returns the raw object stored at **`storage_key`** (same collection access rules as **`GET /documents/{id}`**).

**Query parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| **`redirect`** | **`true`** | When **`true`**, the API responds with **302 Found** and a **`Location`** header pointing at a **short-lived presigned URL** (S3/MinIO). The first request still requires **`Authorization: Bearer`**. Follow the redirect to download bytes from object storage (e.g. `curl -L` with Bearer on the first hop only). When **`false`**, the API streams the file in the response body (still authenticated). Use **`redirect=false`** when clients cannot reach the object-storage host directly (e.g. some browser or same-origin SPA flows). |

**Success:**

- **302** — presigned URL in **`Location`** (TTL configured server-side, env **`DOWNLOAD_PRESIGNED_TTL_SECONDS`**, default 3600). Not used when storage is the in-memory test double or presigning fails; the API falls back to streaming.
- **200** — raw bytes; **`Content-Type`** from the document row when known; **`Content-Disposition: attachment`** with the original filename when available.

**Errors:**

- **404** — document missing, no access, no **`storage_key`**, or object absent from storage
- **502** — storage read error when streaming (**`redirect=false`** or no presigned URL)

## Deleting a document

**`DELETE /api/v1/documents/{document_id}`**

**Success:** **204 No Content**  
**404** if missing or not accessible.

The API removes the canonical database row (and related metadata) and **attempts** to delete the raw file from object storage.

## Understanding document status

The API may show several **status** values over time, including:

| Status | Plain meaning |
|--------|----------------|
| **`created`** | Row exists; for URL ingest, the worker has not finished fetching yet |
| **`queued`** | Raw bytes are stored; a processing job is expected to run |
| **`processing`** | Worker pipeline is running |
| **`completed`** | Pipeline finished successfully (exact meaning may evolve with product) |
| **`failed`** | Something went wrong; check **`ingest_error`** or operator logs |

Older schema values such as **`draft`**, **`active`**, **`archived`**, or **`deleted`** may still appear on some rows during migrations—treat ambiguous cases with your administrator.

**Fields that help debugging:**

- **`ingest_error`** — upload/fetch problems
- **`enqueue_error`** — could not queue background work

## Next steps

- [Search and live updates](search-and-events.md) — notifications while documents process
- [Status and troubleshooting](status-and-troubleshooting.md)
