"""Shared pipeline stage ordering (API intake → worker scaffold)."""

# Must stay aligned with `pipeline_runs.stage` CHECK constraint in db/migrations.
DOCUMENT_SCAFFOLD_STAGES: tuple[str, ...] = (
    "ingest",
    "extract",
    "enrich",
    "score",
    "index",
    "finalize",
)

PIPELINE_NAME = "document_scaffold"
PIPELINE_VERSION = "0.1.0"
