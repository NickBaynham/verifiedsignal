-- Client-supplied JSON (tags, labels, integration keys) for filtering and optional metadata search.
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS user_metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN documents.user_metadata IS
  'Convention-based JSON at intake (e.g. tags[], label); denormalized into OpenSearch at index time.';

CREATE INDEX IF NOT EXISTS ix_documents_user_metadata_gin ON documents USING gin (user_metadata jsonb_path_ops);
