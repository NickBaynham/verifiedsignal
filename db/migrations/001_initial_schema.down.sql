-- =============================================================================
-- Veridoc: rollback initial canonical schema
-- =============================================================================
-- Drops objects created in 001_initial_schema.up.sql in dependency-safe order.
-- WARNING: This destroys all data in these tables. Use only in dev or controlled
-- rollback scenarios—not as a substitute for backups in production.
-- =============================================================================

DROP TABLE IF EXISTS pipeline_events CASCADE;
DROP TABLE IF EXISTS document_scores CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS document_sources CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS collections CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP FUNCTION IF EXISTS veridoc_set_updated_at() CASCADE;
