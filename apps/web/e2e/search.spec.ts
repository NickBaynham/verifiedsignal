import { expect, test } from "@playwright/test";
import { loginAsDemoUser } from "./helpers/auth";

test.describe("Search (mock)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemoUser(page);
    await page.getByRole("navigation").getByRole("link", { name: "Search" }).click();
  });

  test("filters mock results by query", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Search" })).toBeVisible();
    const q = page.getByLabel("Query");
    await q.fill("__no_hits_playwright__");
    await expect(page.getByText(/No mock results/i)).toBeVisible();
    await q.fill("Vendor security");
    await expect(page.getByRole("link", { name: /Vendor security questionnaire/i })).toBeVisible();
  });

  test("switches keyword / semantic / hybrid modes", async ({ page }) => {
    await page.getByRole("button", { name: "Semantic" }).click();
    await expect(page.getByText(/Mode: semantic/i).first()).toBeVisible();
    await page.getByRole("button", { name: "Hybrid" }).click();
    await expect(page.getByText(/Mode: hybrid/i).first()).toBeVisible();
  });

  test("typo hint offers correction", async ({ page }) => {
    await page.getByLabel("Query").fill("goverment policy");
    await expect(page.getByRole("button", { name: "government policy" })).toBeVisible();
  });

  test("search filters by collection (demo metadata)", async ({ page }) => {
    await page.getByLabel("Collection").selectOption({ label: "Legal & vendor" });
    await page.getByLabel("Query").fill("questionnaire");
    await expect(page.getByRole("link", { name: /Vendor security questionnaire/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Policy brief/i })).not.toBeVisible();
  });

  test("include facet counts shows facet table", async ({ page }) => {
    await page.getByRole("checkbox", { name: /Include facet counts/i }).check();
    await expect(page.getByRole("heading", { name: "Facets" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "complete", exact: true })).toBeVisible();
  });
});
