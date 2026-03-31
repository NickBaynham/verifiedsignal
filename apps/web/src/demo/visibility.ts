import { DEMO_DASHBOARD_METRICS, DEMO_DOCUMENTS } from "./mockData";
import type { DemoDocument } from "./types";

export function resolveDemoDocument(
  id: string,
  deleted: ReadonlySet<string>,
): DemoDocument | undefined {
  if (deleted.has(id)) return undefined;
  return DEMO_DOCUMENTS.find((d) => d.id === id);
}

export function visibleDashboardRecentIds(deleted: ReadonlySet<string>): string[] {
  return DEMO_DASHBOARD_METRICS.recentDocumentIds.filter((rid) => !deleted.has(rid));
}
