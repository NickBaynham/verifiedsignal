import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

const STORAGE_KEY = "verifiedsignal_demo_deleted_docs";

function loadDeletedIds(): Set<string> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw) as unknown;
    if (!Array.isArray(arr)) return new Set();
    return new Set(arr.filter((x): x is string => typeof x === "string"));
  } catch {
    return new Set();
  }
}

export type DemoDataContextValue = {
  deletedDocumentIds: ReadonlySet<string>;
  deleteDemoDocument: (documentId: string) => void;
  isDemoDocumentDeleted: (documentId: string) => boolean;
};

const DemoDataContext = createContext<DemoDataContextValue | null>(null);

export function DemoDataProvider({ children }: { children: ReactNode }) {
  const [deletedDocumentIds, setDeletedDocumentIds] = useState<Set<string>>(loadDeletedIds);

  const deleteDemoDocument = useCallback((documentId: string) => {
    setDeletedDocumentIds((prev) => {
      const next = new Set(prev);
      next.add(documentId);
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const value = useMemo<DemoDataContextValue>(
    () => ({
      deletedDocumentIds,
      deleteDemoDocument,
      isDemoDocumentDeleted: (id) => deletedDocumentIds.has(id),
    }),
    [deletedDocumentIds, deleteDemoDocument],
  );

  return <DemoDataContext.Provider value={value}>{children}</DemoDataContext.Provider>;
}

export function useDemoData(): DemoDataContextValue {
  const ctx = useContext(DemoDataContext);
  if (!ctx) {
    throw new Error("useDemoData must be used within DemoDataProvider");
  }
  return ctx;
}
