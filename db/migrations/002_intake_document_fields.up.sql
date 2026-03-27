-- =============================================================================
-- VerifiedSignal: Phase 1 intake — document file metadata, storage key, lifecycle
-- =============================================================================

-- Lifecycle: we skip a separate `created` *state* in the happy path and use
-- `queued` once the object exists in storage (see API comments). Column
-- `ingest_error` / `enqueue_error` capture failures without dropping the row.

ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS original_filename TEXT,
  ADD COLUMN IF NOT EXISTS content_type TEXT,
  ADD COLUMN IF NOT EXISTS file_size BIGINT,
  ADD COLUMN IF NOT EXISTS storage_key TEXT,
  ADD COLUMN IF NOT EXISTS ingest_error TEXT,
  ADD COLUMN IF NOT EXISTS enqueue_error TEXT;

ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_status_chk;
ALTER TABLE documents ADD CONSTRAINT documents_status_chk CHECK (
  status IN (
    'created',
    'queued',
    'processing',
    'completed',
    'failed',
    'draft',
    'active',
    'archived',
    'deleted'
  )
);

ALTER TABLE documents ADD CONSTRAINT documents_file_size_nonneg_chk CHECK (
  file_size IS NULL OR file_size >= 0
);

CREATE INDEX IF NOT EXISTS ix_documents_storage_key ON documents (storage_key)
  WHERE storage_key IS NOT NULL;

COMMENT ON COLUMN documents.storage_key IS
  'S3/MinIO object key for raw intake bytes (e.g. raw/{document_id}/{filename}).';
COMMENT ON COLUMN documents.ingest_error IS
  'Set when object upload or pre-storage validation fails; row kept for audit.';
COMMENT ON COLUMN documents.enqueue_error IS
  'Set when enqueue fails after successful storage; status remains queued.';

-- ---------------------------------------------------------------------------
-- Seed default org + collection for local dev (idempotent)
-- ---------------------------------------------------------------------------
INSERT INTO organizations (id, name, slug)
VALUES (
  '00000000-0000-4000-8000-000000000001'::uuid,
  'Local Dev',
  'local-dev'
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO collections (id, organization_id, name, slug)
VALUES (
  '00000000-0000-4000-8000-000000000002'::uuid,
  '00000000-0000-4000-8000-000000000001'::uuid,
  'Default Inbox',
  'default-inbox'
)
ON CONFLICT (organization_id, slug) DO NOTHING;
