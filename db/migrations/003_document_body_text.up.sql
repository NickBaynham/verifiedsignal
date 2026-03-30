-- Extracted plain text for search indexing (derived from raw bytes in object storage).
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS body_text TEXT;

COMMENT ON COLUMN documents.body_text IS
  'Plain text extracted from stored raw bytes (e.g. text/*, JSON, UTF-8); used for OpenSearch keyword search.';
