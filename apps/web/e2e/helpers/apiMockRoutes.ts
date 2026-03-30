import type { Page } from "@playwright/test";
import { E2E_MOCK_API_ORIGIN } from "../../playwright.api-mock.config";

const DOC_ID = "11111111-1111-4111-8111-111111111111";
const COL_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

/** JSON detail for list + get document (matches FastAPI shapes). */
const listPayload = {
  items: [
    {
      id: DOC_ID,
      collection_id: COL_ID,
      title: "E2E Policy Brief",
      status: "indexed",
      original_filename: "brief.txt",
      content_type: "text/plain",
      created_at: "2026-01-02T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
    },
  ],
  total: 1,
  user_id: "e2e-sub",
};

const detailPayload = {
  ...listPayload.items[0],
  sources: [],
  body_text: "Hello from API mock document.",
  canonical_score: {
    factuality_score: 0.72,
    ai_generation_probability: 0.18,
    fallacy_score: null,
    confidence_score: 0.35,
    scorer_name: "verifiedsignal_heuristic",
    scorer_version: "1.0.0",
  },
};

/**
 * Intercept calls to {@link E2E_MOCK_API_ORIGIN} so the SPA can run in API mode without a real backend.
 */
export async function installApiMockRoutes(page: Page) {
  const origin = E2E_MOCK_API_ORIGIN;

  await page.route(`${origin}/api/v1/events/stream`, async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
      body: 'data: {"type":"connected","payload":{}}\n\n',
    });
  });

  await page.route(
    (url) => {
      const u = url.toString().split("?")[0];
      return u.startsWith(`${origin}/api/v1/collections/`) && u.endsWith("/analytics");
    },
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          collection_id: COL_ID,
          index_total: 1,
          index_status: "fake",
          index_message: null,
          facets: {
            status: [{ key: "indexed", count: 1 }],
            ingest_source: [{ key: "upload", count: 1 }],
          },
          postgres: {
            document_count: 2,
            scored_documents: 1,
            avg_factuality: 0.72,
            avg_ai_probability: 0.18,
            suspicious_count: 0,
          },
        }),
      });
    },
  );

  await page.route(
    (url) => {
      const u = url.toString();
      return u.includes(`${origin}/api/v1/documents/`) && u.includes("/pipeline");
    },
    async (route) => {
      const u = route.request().url();
      const docPart = u.split("/documents/")[1]?.split("/pipeline")[0] ?? DOC_ID;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          document_id: docPart,
          document_status: "completed",
          run: {
            id: "22222222-2222-4222-8222-222222222222",
            document_id: docPart,
            status: "succeeded",
            stage: "finalize",
            started_at: "2026-01-02T00:00:00Z",
            completed_at: "2026-01-02T00:01:00Z",
            error_detail: null,
            run_metadata: {},
          },
          events: [
            {
              id: "33333333-3333-4333-8333-333333333333",
              step_index: 0,
              event_type: "pipeline_started",
              stage: null,
              payload: {},
              created_at: "2026-01-02T00:00:00Z",
            },
            {
              id: "44444444-4444-4444-8444-444444444444",
              step_index: 1,
              event_type: "index_complete",
              stage: "index",
              payload: {},
              created_at: "2026-01-02T00:00:30Z",
            },
          ],
        }),
      });
    },
  );

  await page.route(`${origin}/auth/login`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "e2e-mock-access-token",
        expires_in: 3600,
        token_type: "bearer",
      }),
    });
  });

  await page.route(`${origin}/auth/refresh`, async (route) => {
    await route.fulfill({ status: 401, contentType: "application/json", body: "{}" });
  });

  await page.route(`${origin}/auth/logout`, async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });

  await page.route(`${origin}/api/v1/users/me`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user_id: "e2e-sub",
        database_user_id: "00000000-0000-4000-8000-000000000099",
        email: "e2e@verifiedsignal.io",
        display_name: "e2e",
      }),
    });
  });

  await page.route(`${origin}/api/v1/collections`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        collections: [
          {
            id: COL_ID,
            organization_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            name: "E2E Inbox",
            slug: "inbox",
            document_count: 2,
            created_at: "2026-01-01T00:00:00Z",
          },
        ],
      }),
    });
  });

  await page.route(
    (url) => {
      const u = url.toString();
      if (!u.startsWith(`${origin}/api/v1/documents/`)) return false;
      if (u.startsWith(`${origin}/api/v1/documents/from-url`)) return false;
      return true;
    },
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.fallback();
        return;
      }
      const u = route.request().url();
      const path = u.slice(`${origin}/api/v1/documents/`.length).split("?")[0];
      if (path.includes("/")) {
        await route.fallback();
        return;
      }
      if (path === DOC_ID) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(detailPayload),
        });
        return;
      }
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Document not found" }),
      });
    },
  );

  await page.route(
    (url) => {
      const base = url.toString().split("?")[0];
      return base === `${origin}/api/v1/documents`;
    },
    async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(listPayload),
        });
        return;
      }
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            document_id: "00000000-0000-4000-8000-0000000000e2",
            status: "queued",
            storage_key: "mock/key",
            job_id: "job-e2e",
          }),
        });
        return;
      }
      await route.fallback();
    },
  );

  await page.route(`${origin}/api/v1/documents/from-url`, async (route) => {
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({
        document_id: "00000000-0000-4000-8000-0000000000e3",
        status: "created",
        source_url: "https://example.com/x",
        job_id: "job-url",
      }),
    });
  });

  await page.route(
    (url) => url.toString().startsWith(`${origin}/api/v1/search`),
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          query: "",
          limit: 25,
          hits: [
            {
              document_id: DOC_ID,
              title: "E2E Policy Brief",
              score: 1,
              snippet: "Hello from API",
              status: "indexed",
            },
          ],
          total: 1,
          index_status: "fake",
          message: null,
        }),
      });
    },
  );
}

export { DOC_ID, COL_ID };
