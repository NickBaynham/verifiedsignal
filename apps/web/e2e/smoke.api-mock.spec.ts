import { expect, test } from "@playwright/test";
import { COL_ID, DOC_ID, installApiMockRoutes } from "./helpers/apiMockRoutes";

test.describe("API mode (mocked HTTP)", () => {
  test.beforeEach(async ({ page }) => {
    await installApiMockRoutes(page);
  });

  test("signs in against mocked /auth/login and shows API banner", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email", { exact: false }).fill("e2e@verifiedsignal.io");
    await page.getByLabel("Password", { exact: false }).fill("any-password");
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText(/API mode/i)).toBeVisible();
    await expect(page.getByRole("link", { name: "E2E Policy Brief" })).toBeVisible();
  });

  test("opens document from dashboard", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Password", { exact: false }).fill("pw");
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await page.getByRole("link", { name: "E2E Policy Brief" }).click();
    await expect(page.getByRole("heading", { name: "E2E Policy Brief" })).toBeVisible();
    await expect(page.getByText(/Hello from API mock document/i)).toBeVisible();
  });

  test("search lists mocked hits", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Password", { exact: false }).fill("pw");
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await page.getByRole("navigation").getByRole("link", { name: "Search" }).click();
    await expect(page.getByRole("link", { name: "E2E Policy Brief" })).toBeVisible({ timeout: 20_000 });
  });

  test("collections and analytics use API metadata", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Password", { exact: false }).fill("pw");
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await page.getByRole("navigation").getByRole("link", { name: "Collections" }).click();
    await expect(page.getByRole("cell", { name: "E2E Inbox", exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Analytics →" }).click();
    await expect(page.getByRole("heading", { name: "E2E Inbox" })).toBeVisible();
    await expect(page.getByText(/OpenSearch facet buckets/i)).toBeVisible();
  });

  test("unknown document id shows not found", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Password", { exact: false }).fill("pw");
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await page.goto(`/documents/${COL_ID}`);
    await expect(page.getByRole("heading", { name: "Document not found" })).toBeVisible();
  });

  test("known document id loads", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Password", { exact: false }).fill("pw");
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await page.goto(`/documents/${DOC_ID}`);
    await expect(page.getByRole("heading", { name: "E2E Policy Brief" })).toBeVisible();
  });
});
