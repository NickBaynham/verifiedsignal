import { expect, test, type Page } from "@playwright/test";
import { dispatchSyntheticFolderPick } from "./helpers/folderUpload";
import { installApiMockRoutes } from "./helpers/apiMockRoutes";

async function mockPasswordLogin(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Password", { exact: false }).fill("pw");
  await page.getByRole("button", { name: /Continue to dashboard/i }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

test.describe("Upload folder (API mock)", () => {
  test.beforeEach(async ({ page }) => {
    await installApiMockRoutes(page);
  });

  test("Local folder sync uploads each file and logs results", async ({ page }) => {
    await mockPasswordLogin(page);
    await page.goto("/library/upload");
    await expect(page.getByRole("heading", { name: "Upload" })).toBeVisible();
    await page.getByRole("button", { name: /^Local folder$/i }).click();
    await dispatchSyntheticFolderPick(page, [
      { relativePath: "e2e-upload-folder/root.txt", content: "root fixture\n" },
      { relativePath: "e2e-upload-folder/sub/inner.txt", content: "nested fixture\n" },
    ]);
    // localDirectorySync logs these prefixes (see apps/web/src/lib/localDirectorySync.ts)
    await expect(page.getByText(/Uploaded:|Unchanged:/)).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/root\.txt/)).toBeVisible();
    await expect(page.getByText(/inner\.txt/)).toBeVisible();
  });
});
