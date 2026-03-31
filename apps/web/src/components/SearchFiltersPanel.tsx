import type { FacetBucket } from "../api/types";

type CollectionOption = { id: string; name: string };

type Props = {
  collections: CollectionOption[];
  collectionId: string;
  onCollectionId: (v: string) => void;
  contentType: string;
  onContentType: (v: string) => void;
  status: string;
  onStatus: (v: string) => void;
  ingestSource: "" | "upload" | "url";
  onIngestSource: (v: "" | "upload" | "url") => void;
  tagsInput: string;
  onTagsInput: (v: string) => void;
  includeFacets: boolean;
  onIncludeFacets: (v: boolean) => void;
};

export function SearchFiltersPanel({
  collections,
  collectionId,
  onCollectionId,
  contentType,
  onContentType,
  status,
  onStatus,
  ingestSource,
  onIngestSource,
  tagsInput,
  onTagsInput,
  includeFacets,
  onIncludeFacets,
}: Props) {
  return (
    <fieldset
      className="card"
      style={{ marginTop: "0.75rem", padding: "0.75rem 1rem", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}
    >
      <legend id="search-filters-legend" style={{ fontSize: "0.95rem", fontWeight: 600, padding: "0 0.25rem" }}>
        Search filters
      </legend>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: "0.75rem",
          alignItems: "end",
        }}
      >
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="search-collection">Collection</label>
          <select
            id="search-collection"
            value={collectionId}
            onChange={(e) => onCollectionId(e.target.value)}
            style={{ width: "100%" }}
          >
            <option value="">All collections</option>
            {collections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="search-content-type">Content type (contains)</label>
          <input
            id="search-content-type"
            value={contentType}
            onChange={(e) => onContentType(e.target.value)}
            placeholder="e.g. pdf"
            style={{ width: "100%" }}
          />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="search-status">Status</label>
          <input
            id="search-status"
            value={status}
            onChange={(e) => onStatus(e.target.value)}
            placeholder="e.g. indexed"
            style={{ width: "100%" }}
          />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor="search-ingest">Ingest source</label>
          <select
            id="search-ingest"
            value={ingestSource}
            onChange={(e) => onIngestSource(e.target.value as "" | "upload" | "url")}
            style={{ width: "100%" }}
          >
            <option value="">Any</option>
            <option value="upload">upload</option>
            <option value="url">url</option>
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0, gridColumn: "1 / -1" }}>
          <label htmlFor="search-tags">Tags (comma-separated, AND)</label>
          <input
            id="search-tags"
            value={tagsInput}
            onChange={(e) => onTagsInput(e.target.value)}
            placeholder="policy, vendor"
            style={{ width: "100%", maxWidth: "480px" }}
          />
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9rem", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={includeFacets}
            onChange={(e) => onIncludeFacets(e.target.checked)}
          />
          Include facet counts
        </label>
      </div>
    </fieldset>
  );
}

export function SearchFacetsTable({ facets }: { facets: Record<string, FacetBucket[]> | null | undefined }) {
  if (!facets || Object.keys(facets).length === 0) return null;
  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <h3 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Facets</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {Object.entries(facets).map(([name, buckets]) => (
          <div key={name}>
            <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: 6 }}>{name}</div>
            <table className="table" style={{ fontSize: "0.85rem" }}>
              <thead>
                <tr>
                  <th>Value</th>
                  <th>Count</th>
                </tr>
              </thead>
              <tbody>
                {buckets.map((b, i) => (
                  <tr key={`${name}-${i}`}>
                    <td>{b.key ?? "—"}</td>
                    <td>{b.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
