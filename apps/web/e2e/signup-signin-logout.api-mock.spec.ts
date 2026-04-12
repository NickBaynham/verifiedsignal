import { expect, test } from "@playwright/test";
import { installApiMockRoutes } from "./helpers/apiMockRoutes";

test.describe("API mode: sign up → sign out → sign in → sign out", () => {
  test.beforeEach(async ({ page }) => {
    await installApiMockRoutes(page);
  });

  test("sign up (auto sign-in), sign out, sign in again, sign out", async ({ page }) => {
    const email = `cycle-${Date.now()}@verifiedsignal.io`;
    const password = "e2e-password-9";

    await page.goto("/login");
    await page.getByRole("button", { name: "Sign up" }).click();
    await page.getByLabel("Email", { exact: false }).fill(email);
    await page.getByLabel("Password", { exact: false }).fill(password);
    await page.getByRole("button", { name: /Create account & sign in/i }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText(/API mode/i)).toBeVisible();

    await page.getByRole("button", { name: /Sign out/i }).click();
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();

    await page.getByLabel("Email", { exact: false }).fill(email);
    await page.getByLabel("Password", { exact: false }).fill(password);
    await page.getByRole("button", { name: /Continue to dashboard/i }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText(/API mode/i)).toBeVisible();

    await page.getByRole("button", { name: /Sign out/i }).click();
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });
});
