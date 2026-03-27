-- Roll back intake columns (destructive). Reverts status constraint to v001 set.

DELETE FROM collections
WHERE id = '00000000-0000-4000-8000-000000000002'::uuid
  AND slug = 'default-inbox';

DELETE FROM organizations
WHERE id = '00000000-0000-4000-8000-000000000001'::uuid
  AND slug = 'local-dev';

DROP INDEX IF EXISTS ix_documents_storage_key;

ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_file_size_nonneg_chk;

ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_status_chk;
ALTER TABLE documents ADD CONSTRAINT documents_status_chk CHECK (
  status IN ('draft', 'active', 'archived', 'deleted')
);

ALTER TABLE documents
  DROP COLUMN IF EXISTS enqueue_error,
  DROP COLUMN IF EXISTS ingest_error,
  DROP COLUMN IF EXISTS storage_key,
  DROP COLUMN IF EXISTS file_size,
  DROP COLUMN IF EXISTS content_type,
  DROP COLUMN IF EXISTS original_filename;
