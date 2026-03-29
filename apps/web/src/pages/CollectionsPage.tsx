import { Link } from "react-router-dom";
import { DEMO_COLLECTIONS } from "../demo";

export function CollectionsPage() {
  return (
    <>
      <h1 className="page-title">Collections</h1>
      <p className="page-sub">Open a collection to view analytics — <strong>Use Case 4</strong>.</p>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Documents</th>
              <th>Updated</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {DEMO_COLLECTIONS.map((c) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.name}</td>
                <td>{c.documentCount}</td>
                <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  {new Date(c.updatedAt).toLocaleDateString()}
                </td>
                <td>
                  <Link to={`/collections/${c.id}/analytics`}>Analytics →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
