DROP INDEX IF EXISTS ix_documents_user_metadata_gin;
ALTER TABLE documents DROP COLUMN IF EXISTS user_metadata;
