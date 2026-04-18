-- Model write-back: canonical artifacts (findings, risks, tests, execution, evidence, contradictions).
-- Single table + audit events; OpenSearch/index layers remain derived.

CREATE TABLE model_writeback_artifacts (
  id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_model_id              UUID NOT NULL REFERENCES knowledge_models (id) ON DELETE CASCADE,
  knowledge_model_version_id      UUID REFERENCES knowledge_model_versions (id) ON DELETE SET NULL,
  artifact_kind                   VARCHAR(32) NOT NULL,
  title                           TEXT NOT NULL,
  summary                         TEXT,
  payload_json                    JSONB NOT NULL DEFAULT '{}'::jsonb,
  origin_type                     VARCHAR(32) NOT NULL,
  origin_id                       TEXT,
  verification_state              VARCHAR(32) NOT NULL DEFAULT 'proposed',
  confidence_score                NUMERIC(6, 5),
  reviewer_id                     UUID REFERENCES users (id) ON DELETE SET NULL,
  reviewed_at                     TIMESTAMPTZ,
  review_note                     TEXT,
  supersedes_id                   UUID REFERENCES model_writeback_artifacts (id) ON DELETE SET NULL,
  related_document_id             UUID REFERENCES documents (id) ON DELETE SET NULL,
  related_asset_id                UUID REFERENCES knowledge_model_assets (id) ON DELETE SET NULL,
  related_writeback_id            UUID REFERENCES model_writeback_artifacts (id) ON DELETE SET NULL,
  related_entity_id               UUID,
  related_claim_id                UUID,
  evidence_refs_json              JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT model_writeback_artifacts_kind_chk CHECK (artifact_kind IN (
    'finding', 'risk', 'test_artifact', 'execution_result', 'evidence_note', 'contradiction'
  )),
  CONSTRAINT model_writeback_artifacts_origin_chk CHECK (origin_type IN (
    'human', 'agent', 'imported_system', 'runtime_evidence', 'internal_service'
  )),
  CONSTRAINT model_writeback_artifacts_verification_chk CHECK (verification_state IN (
    'proposed', 'accepted', 'rejected', 'auto_ingested', 'superseded'
  )),
  CONSTRAINT model_writeback_artifacts_title_nonempty_chk CHECK (length(trim(title)) > 0)
);

CREATE INDEX ix_model_writeback_artifacts_model_created
  ON model_writeback_artifacts (knowledge_model_id, created_at DESC);
CREATE INDEX ix_model_writeback_artifacts_version_id
  ON model_writeback_artifacts (knowledge_model_version_id);
CREATE INDEX ix_model_writeback_artifacts_kind
  ON model_writeback_artifacts (artifact_kind);
CREATE INDEX ix_model_writeback_artifacts_verification
  ON model_writeback_artifacts (verification_state);

CREATE TRIGGER trg_model_writeback_artifacts_updated_at
  BEFORE UPDATE ON model_writeback_artifacts
  FOR EACH ROW EXECUTE PROCEDURE verifiedsignal_set_updated_at();

COMMENT ON TABLE model_writeback_artifacts IS
  'Canonical write-back artifacts attached to knowledge models (version-aware, provenance, governance).';


CREATE TABLE model_writeback_events (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artifact_id       UUID NOT NULL REFERENCES model_writeback_artifacts (id) ON DELETE CASCADE,
  event_type        VARCHAR(64) NOT NULL,
  actor_origin_type VARCHAR(32),
  actor_user_id     UUID REFERENCES users (id) ON DELETE SET NULL,
  payload_json      JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_model_writeback_events_artifact_created
  ON model_writeback_events (artifact_id, created_at DESC);

COMMENT ON TABLE model_writeback_events IS
  'Audit trail for write-back lifecycle (create, verification changes, etc.).';
