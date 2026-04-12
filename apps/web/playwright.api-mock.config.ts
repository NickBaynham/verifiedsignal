import { defineConfig, devices } from "@playwright/test";

/** Must match `installApiMockRoutes` (Playwright intercepts this origin). */
export const E2E_MOCK_API_ORIGIN = "http://127.0.0.1:17654";

/** Dedicated Vite port so `reuseExistingServer` does not pick up a normal `npm run dev` on 5173. */
const E2E_MOCK_WEB_PORT = 5183;

/**
 * E2E with `VITE_API_URL` pointed at a non-listening port; routes are mocked in-browser.
 * Run: `npm run test:e2e:api-mock`
 */
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.api-mock.spec.ts",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? "github" : "list",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: `http://127.0.0.1:${E2E_MOCK_WEB_PORT}`,
    headless: true,
    trace: "on-first-retry",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `VITE_API_URL=${E2E_MOCK_API_ORIGIN} npm run dev -- --port ${E2E_MOCK_WEB_PORT} --strictPort`,
    url: `http://127.0.0.1:${E2E_MOCK_WEB_PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
