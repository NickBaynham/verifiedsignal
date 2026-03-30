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

## Opening one document

**`GET /api/v1/documents/{document_id}`**  
`document_id` is a UUID.

**Response (JSON):** same fields as list items, plus **`user_metadata`** (client JSON from intake), **`sources`** — provenance rows (e.g. **`upload`**, **`url`**) with locators, MIME types, and byte lengths when known, and **`body_text`** when extract has run.

**404** means the id does not exist **or** you do not have access.

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

## Getting the file back

Today’s public API focuses on **metadata and processing**. Downloading the original bytes through a dedicated “download” endpoint may or may not be exposed in your deployment—ask your administrator or check OpenAPI for newer routes.

## Next steps

- [Search and live updates](search-and-events.md) — notifications while documents process
- [Status and troubleshooting](status-and-troubleshooting.md)
