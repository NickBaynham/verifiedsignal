# VerifiedSignal — guide for end users

This folder describes what you can do with the product **as it exists today**: HTTP API, optional web UI demo, and background processing. **Keyword search** is wired to **OpenSearch** (or a test-only in-memory stand-in); semantic / vector search and richer UI are still evolving.

## Who this is for

- People using a **client app** (custom SPA, mobile app, or script) that talks to the VerifiedSignal API.
- Anyone who wants a **plain-language** map of routes and behavior before reading OpenAPI (`/` on a running server) or operator docs.

## Chapters

| Guide | What it covers |
|--------|----------------|
| [Getting started](getting-started.md) | What the product does, base URLs, interactive API docs, limits |
| [Signing in and tokens](signing-in.md) | Email signup/login, refresh cookie, access token, logout |
| [Workspace and collections](workspace-and-collections.md) | Your org, Inbox, profile, choosing a collection |
| [Documents](documents.md) | Upload files, add by URL, **local folder tree + client-side sync** (web app), list, open details, delete, statuses |
| [Search and live updates](search-and-events.md) | Authenticated keyword search (filters + facets), authenticated SSE + tenant filtering, pipeline polling, collection analytics |
| [Status and troubleshooting](status-and-troubleshooting.md) | Service health, common errors, who to ask |

## Related documentation

- **Async HTTP scoring & `canonical_score` (operators):** [`../scoring-http.md`](../scoring-http.md)
- **Planned metadata & tags (technical design):** [`../document-metadata-design.md`](../document-metadata-design.md)
- **Operators / security / JWT details:** [`../auth-supabase.md`](../auth-supabase.md), [`../tenancy-postgres.md`](../tenancy-postgres.md)
- **URL intake (technical + SSRF):** [`../url-ingest.md`](../url-ingest.md)
- **Local Supabase:** [`../../supabase/README.md`](../../supabase/README.md)
- **Web demo (mock UI):** [`../../apps/web/README.md`](../../apps/web/README.md)

If you only need a short summary of accounts and collections, see the redirect at [`../accounts-and-collections.md`](../accounts-and-collections.md).
