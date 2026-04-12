import type { Page } from "@playwright/test";

/**
 * Playwright rejects `/` in synthetic {@link FilePayload.name}. Real folder picks set
 * `webkitRelativePath` on each `File`. Dispatch a `change` event after assigning `files`
 * so React sees stable `File` objects (see UploadPage: copy `Array.from` before clearing).
 */
export async function dispatchSyntheticFolderPick(
  page: Page,
  entries: { relativePath: string; content: string }[],
): Promise<void> {
  await page.evaluate(
    ({ list }) => {
      const inp = document.querySelector(
        '[data-testid="local-folder-file-input"]',
      ) as HTMLInputElement | null;
      if (!inp) throw new Error('Missing input[data-testid="local-folder-file-input"]');
      const dt = new DataTransfer();
      for (const e of list) {
        const base = e.relativePath.includes("/")
          ? e.relativePath.slice(e.relativePath.lastIndexOf("/") + 1)
          : e.relativePath;
        const f = new File([e.content], base, { type: "text/plain" });
        Object.defineProperty(f, "webkitRelativePath", {
          value: e.relativePath,
          configurable: true,
          enumerable: true,
        });
        dt.items.add(f);
      }
      inp.files = dt.files;
      inp.dispatchEvent(new Event("input", { bubbles: true }));
      inp.dispatchEvent(new Event("change", { bubbles: true }));
    },
    { list: entries },
  );
}
