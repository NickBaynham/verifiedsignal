-- =============================================================================
-- Veridoc: initial canonical schema (PostgreSQL)
-- =============================================================================
-- Postgres is the system-of-record. OpenSearch/Elasticsearch holds only derived
-- index state and can be dropped and rebuilt from this data plus pipeline logs.
--
-- Conventions:
--   - Primary keys: UUID (gen_random_uuid on PG 13+)
--   - Timestamps: created_at / updated_at (UTC), maintained by trigger
--   - Status/stage: TEXT + CHECK (avoid enum churn when workflows evolve)
--   - Scores: promoted NUMERIC columns for query/filter + JSONB for extensions
-- =============================================================================

-- gen_random_uuid() is built-in from PostgreSQL 13 onward (project targets 16 in Docker).
-- No extension required for UUID generation on supported versions.

-- -----------------------------------------------------------------------------
-- Updated-at trigger (reused by all mutable tables)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION veridoc_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

COMMENT ON FUNCTION veridoc_set_updated_at() IS
  'Sets updated_at to transaction time on UPDATE; keeps row metadata consistent for auditing.';

-- -----------------------------------------------------------------------------
-- users
-- -----------------------------------------------------------------------------
-- Identity for human actors. Link to organizations via organization_members (M2M).
-- -----------------------------------------------------------------------------
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT NOT NULL,
  display_name    TEXT,
  -- Optional: link to external IdP subject; nullable for local-only dev accounts.
  external_sub    TEXT,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT users_email_lower_chk CHECK (email = lower(email)),
  CONSTRAINT users_email_nonempty_chk CHECK (length(trim(email)) > 0)
);

CREATE UNIQUE INDEX uq_users_email ON users (email);
CREATE UNIQUE INDEX uq_users_external_sub ON users (external_sub) WHERE external_sub IS NOT NULL;

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE users IS
  'People who act in the system; organization affiliation is modeled via organization_members.';
COMMENT ON COLUMN users.external_sub IS
  'Stable identifier from an external auth provider (OIDC "sub", etc.), when applicable.';

-- -----------------------------------------------------------------------------
-- organizations
-- -----------------------------------------------------------------------------
CREATE TABLE organizations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  slug            TEXT NOT NULL,
  -- Bump when org-level integration contracts change (webhooks, export formats, etc.).
  settings_schema_version INT NOT NULL DEFAULT 1,
  metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT organizations_name_nonempty_chk CHECK (length(trim(name)) > 0),
  CONSTRAINT organizations_slug_nonempty_chk CHECK (length(trim(slug)) > 0),
  CONSTRAINT organizations_slug_lower_chk CHECK (slug = lower(slug)),
  CONSTRAINT organizations_settings_schema_version_chk CHECK (settings_schema_version >= 1)
);

CREATE UNIQUE INDEX uq_organizations_slug ON organizations (slug);

CREATE TRIGGER trg_organizations_updated_at
  BEFORE UPDATE ON organizations
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE organizations IS
  'Tenant boundary; owns collections and membership. Search indices are partitioned by org/collection in derived stores.';
COMMENT ON COLUMN organizations.settings_schema_version IS
  'Version of the interpretation of metadata / integration settings for this organization.';

-- -----------------------------------------------------------------------------
-- organization_members (users ↔ organizations, many-to-many)
-- -----------------------------------------------------------------------------
CREATE TABLE organization_members (
  organization_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  role            TEXT NOT NULL DEFAULT 'member',
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT organization_members_role_chk CHECK (
    role IN ('owner', 'admin', 'member', 'viewer')
  ),
  PRIMARY KEY (organization_id, user_id)
);

CREATE INDEX ix_organization_members_user_id ON organization_members (user_id);

CREATE TRIGGER trg_organization_members_updated_at
  BEFORE UPDATE ON organization_members
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE organization_members IS
  'Many-to-many membership; keeps users reusable across orgs and supports role-based access at the app layer.';

-- -----------------------------------------------------------------------------
-- collections
-- -----------------------------------------------------------------------------
CREATE TABLE collections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  slug            TEXT NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT collections_name_nonempty_chk CHECK (length(trim(name)) > 0),
  CONSTRAINT collections_slug_nonempty_chk CHECK (length(trim(slug)) > 0),
  CONSTRAINT collections_slug_lower_chk CHECK (slug = lower(slug)),
  CONSTRAINT uq_collections_org_slug UNIQUE (organization_id, slug)
);

CREATE INDEX ix_collections_organization_id ON collections (organization_id);

CREATE TRIGGER trg_collections_updated_at
  BEFORE UPDATE ON collections
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE collections IS
  'Groups documents under an organization; natural unit for ACLs and reindex fan-out.';

-- -----------------------------------------------------------------------------
-- documents
-- -----------------------------------------------------------------------------
CREATE TABLE documents (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id   UUID NOT NULL REFERENCES collections (id) ON DELETE CASCADE,
  title           TEXT,
  -- Stable external key from upstream systems (CMS id, upload batch key, etc.).
  external_key    TEXT,
  -- Optional content fingerprint for dedup and integrity (hash of canonical bytes).
  content_sha256  BYTEA CHECK (content_sha256 IS NULL OR octet_length(content_sha256) = 32),
  status          TEXT NOT NULL DEFAULT 'active',
  -- Version of the document row semantics for application migrations.
  row_schema_version INT NOT NULL DEFAULT 1,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT documents_status_chk CHECK (
    status IN ('draft', 'active', 'archived', 'deleted')
  ),
  CONSTRAINT documents_row_schema_version_chk CHECK (row_schema_version >= 1)
);

CREATE INDEX ix_documents_collection_id ON documents (collection_id);
CREATE INDEX ix_documents_collection_created_at ON documents (collection_id, created_at DESC);
CREATE UNIQUE INDEX uq_documents_collection_external_key
  ON documents (collection_id, external_key)
  WHERE external_key IS NOT NULL;

CREATE TRIGGER trg_documents_updated_at
  BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE documents IS
  'Logical document in a collection; OpenSearch documents should use id = documents.id for trivial full reindex.';
COMMENT ON COLUMN documents.content_sha256 IS
  'Optional SHA-256 of canonical document bytes; aids deduplication and audit trails.';

-- -----------------------------------------------------------------------------
-- document_sources
-- -----------------------------------------------------------------------------
-- One document may have many provenance records (URL, file upload, API pull).
-- -----------------------------------------------------------------------------
CREATE TABLE document_sources (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id     UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
  source_kind     TEXT NOT NULL,
  -- URI, object key, or opaque locator depending on source_kind.
  locator         TEXT NOT NULL,
  mime_type       TEXT,
  byte_length     BIGINT CHECK (byte_length IS NULL OR byte_length >= 0),
  fetched_at      timestamptz,
  raw_metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT document_sources_source_kind_chk CHECK (
    source_kind IN ('url', 'upload', 'api', 'email', 'manual', 'other')
  ),
  CONSTRAINT document_sources_locator_nonempty_chk CHECK (length(trim(locator)) > 0)
);

CREATE INDEX ix_document_sources_document_id ON document_sources (document_id);
CREATE INDEX ix_document_sources_document_created ON document_sources (document_id, created_at DESC);

CREATE TRIGGER trg_document_sources_updated_at
  BEFORE UPDATE ON document_sources
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE document_sources IS
  'Provenance and ingestion metadata; rebuilding search does not require this, but audits and re-ingestion do.';

-- -----------------------------------------------------------------------------
-- pipeline_runs
-- -----------------------------------------------------------------------------
-- Each run processes a document through a versioned pipeline definition.
-- -----------------------------------------------------------------------------
CREATE TABLE pipeline_runs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id         UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
  pipeline_name       TEXT NOT NULL,
  pipeline_version    TEXT NOT NULL,
  -- Monotonic definition version for migrations of pipeline semantics.
  definition_schema_version INT NOT NULL DEFAULT 1,
  status              TEXT NOT NULL DEFAULT 'pending',
  stage               TEXT NOT NULL DEFAULT 'queued',
  started_at          timestamptz,
  completed_at        timestamptz,
  error_code          TEXT,
  error_detail        jsonb,
  run_metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pipeline_runs_status_chk CHECK (
    status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')
  ),
  CONSTRAINT pipeline_runs_stage_chk CHECK (
    stage IN (
      'queued',
      'ingest',
      'extract',
      'enrich',
      'score',
      'index',
      'finalize'
    )
  ),
  CONSTRAINT pipeline_runs_definition_schema_version_chk CHECK (definition_schema_version >= 1),
  CONSTRAINT pipeline_runs_completed_after_started_chk CHECK (
    completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at
  )
);

CREATE INDEX ix_pipeline_runs_document_id ON pipeline_runs (document_id);
CREATE INDEX ix_pipeline_runs_document_created ON pipeline_runs (document_id, created_at DESC);
CREATE INDEX ix_pipeline_runs_status_stage ON pipeline_runs (status, stage);
CREATE INDEX ix_pipeline_runs_pipeline_name_version ON pipeline_runs (pipeline_name, pipeline_version);

CREATE TRIGGER trg_pipeline_runs_updated_at
  BEFORE UPDATE ON pipeline_runs
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE pipeline_runs IS
  'One execution of a pipeline for a document; drives reproducible reindex (replay) and operational dashboards.';
COMMENT ON COLUMN pipeline_runs.definition_schema_version IS
  'Version of the pipeline run row / stage model for forward-compatible application evolution.';

-- -----------------------------------------------------------------------------
-- pipeline_events
-- -----------------------------------------------------------------------------
-- Append-only style log per run (immutable facts for auditing).
-- -----------------------------------------------------------------------------
CREATE TABLE pipeline_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs (id) ON DELETE CASCADE,
  step_index      INT NOT NULL,
  event_type      TEXT NOT NULL,
  stage           TEXT,
  payload         jsonb NOT NULL DEFAULT '{}'::jsonb,
  event_schema_version INT NOT NULL DEFAULT 1,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pipeline_events_step_index_chk CHECK (step_index >= 0),
  CONSTRAINT pipeline_events_event_type_chk CHECK (length(trim(event_type)) > 0),
  CONSTRAINT pipeline_events_event_schema_version_chk CHECK (event_schema_version >= 1),
  CONSTRAINT uq_pipeline_events_run_step UNIQUE (pipeline_run_id, step_index)
);

CREATE INDEX ix_pipeline_events_pipeline_run_id ON pipeline_events (pipeline_run_id);
CREATE INDEX ix_pipeline_events_run_created ON pipeline_events (pipeline_run_id, created_at);

COMMENT ON TABLE pipeline_events IS
  'Ordered audit trail within a run; supports debugging and compliance without coupling to OpenSearch.';
COMMENT ON COLUMN pipeline_events.step_index IS
  'Per-run monotonic step order; stable ordering with created_at as tie-breaker if needed.';

-- -----------------------------------------------------------------------------
-- document_scores
-- -----------------------------------------------------------------------------
-- History of scores per document; exactly one row may be canonical per document.
-- Promoted columns speed filters/sorts; score_payload holds extensions.
-- All promoted scores are on [0, 1] where 1 means "strongest signal" for that metric.
-- -----------------------------------------------------------------------------
CREATE TABLE document_scores (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id     UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
  -- Nullable: score may come from a batch job not tied to a single pipeline run.
  pipeline_run_id UUID REFERENCES pipeline_runs (id) ON DELETE SET NULL,
  scorer_name     TEXT NOT NULL,
  scorer_version  TEXT NOT NULL,
  score_schema_version INT NOT NULL DEFAULT 1,
  scored_at       timestamptz NOT NULL DEFAULT now(),
  is_canonical    BOOLEAN NOT NULL DEFAULT false,
  factuality_score              NUMERIC(6, 5),
  ai_generation_probability     NUMERIC(6, 5),
  fallacy_score                 NUMERIC(6, 5),
  confidence_score              NUMERIC(6, 5),
  score_payload                 jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT document_scores_score_schema_version_chk CHECK (score_schema_version >= 1),
  CONSTRAINT document_scores_factuality_range_chk CHECK (
    factuality_score IS NULL OR (factuality_score >= 0 AND factuality_score <= 1)
  ),
  CONSTRAINT document_scores_ai_gen_range_chk CHECK (
    ai_generation_probability IS NULL
    OR (ai_generation_probability >= 0 AND ai_generation_probability <= 1)
  ),
  CONSTRAINT document_scores_fallacy_range_chk CHECK (
    fallacy_score IS NULL OR (fallacy_score >= 0 AND fallacy_score <= 1)
  ),
  CONSTRAINT document_scores_confidence_range_chk CHECK (
    confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)
  ),
  CONSTRAINT document_scores_scorer_nonempty_chk CHECK (
    length(trim(scorer_name)) > 0 AND length(trim(scorer_version)) > 0
  )
);

CREATE INDEX ix_document_scores_document_id ON document_scores (document_id);
CREATE INDEX ix_document_scores_document_scored_at ON document_scores (document_id, scored_at DESC);
CREATE INDEX ix_document_scores_pipeline_run_id ON document_scores (pipeline_run_id)
  WHERE pipeline_run_id IS NOT NULL;

-- At most one canonical score row per document (application must flip flags in one transaction).
CREATE UNIQUE INDEX uq_document_scores_one_canonical_per_document
  ON document_scores (document_id)
  WHERE is_canonical;

CREATE TRIGGER trg_document_scores_updated_at
  BEFORE UPDATE ON document_scores
  FOR EACH ROW EXECUTE PROCEDURE veridoc_set_updated_at();

COMMENT ON TABLE document_scores IS
  'Time-series scoring; canonical row is the application-defined "current truth" for downstream index denormalization.';
COMMENT ON COLUMN document_scores.is_canonical IS
  'When true, this row is the single canonical score for the document; unset others in the same transaction when promoting.';
COMMENT ON COLUMN document_scores.score_payload IS
  'Extensible metrics and model outputs not yet promoted to first-class columns.';
