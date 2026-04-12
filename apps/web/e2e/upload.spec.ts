import { expect, test } from "@playwright/test";
import { dispatchSyntheticFolderPick } from "./helpers/folderUpload";
import { loginAsDemoUser } from "./helpers/auth";

test.describe("Upload (mock pipeline)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemoUser(page);
    await page.getByRole("navigation").getByRole("link", { name: "Upload" }).click();
    await expect(page.getByRole("heading", { name: "Upload" })).toBeVisible();
  });

  test("selects file and completes mock ingestion stages", async ({ page }) => {
    await page.getByRole("button", { name: /^File upload$/i }).click();
    await page.locator('input[type="file"]').setInputFiles({
      name: "e2e-notes.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("playwright e2e upload body"),
    });
    await expect(page.getByText("e2e-notes.txt")).toBeVisible();
    await page.getByRole("button", { name: /Start ingestion \(mock\)/i }).click();
    await expect(page.getByRole("button", { name: /Processing/i })).toBeVisible();
    await expect(page.getByText("Complete").first()).toBeVisible({ timeout: 20_000 });
  });

  test("URL tab shows placeholder controls", async ({ page }) => {
    await page.getByRole("button", { name: /^URL submission$/i }).click();
    await expect(page.getByLabel(/Document URL/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Queue URL \(mock\)/i })).toBeVisible();
  });

  test("Local folder tab ingests directory tree (mock pipeline)", async ({ page }) => {
    await page.getByRole("button", { name: /^Local folder$/i }).click();
    await dispatchSyntheticFolderPick(page, [
      { relativePath: "e2e-upload-folder/root.txt", content: "root\n" },
      { relativePath: "e2e-upload-folder/sub/inner.txt", content: "inner\n" },
    ]);
    await expect(page.getByText("e2e-upload-folder/root.txt")).toBeVisible();
    await expect(page.getByText("e2e-upload-folder/sub/inner.txt")).toBeVisible();
    await page.getByRole("button", { name: /Start ingestion \(mock\)/i }).click();
    await expect(page.getByRole("button", { name: /Processing/i })).toBeVisible();
    await expect(page.getByText("Complete").first()).toBeVisible({ timeout: 20_000 });
  });
});
