"""Facet aggregation wrapper (fake OpenSearch)."""

from app.core import config as config_mod
from app.services.opensearch_document_index import (
    facet_aggregation_sync,
    reset_fake_opensearch_index,
)
from app.services.search_filters import SearchFilters


def test_facet_aggregation_fake_empty(monkeypatch):
    monkeypatch.setenv("USE_FAKE_OPENSEARCH", "true")
    config_mod.get_settings.cache_clear()
    reset_fake_opensearch_index()
    out = facet_aggregation_sync(filters=SearchFilters(), settings=None)
    assert out["total"] == 0
    assert out["facets"] is not None
    config_mod.get_settings.cache_clear()
