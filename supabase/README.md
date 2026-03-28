# Local Supabase (optional)

VerifiedSignal session auth (`/auth/*`) targets **Supabase GoTrue**. For local development:

1. Install the [Supabase CLI](https://supabase.com/docs/guides/cli).
2. From the repository root run:

   ```bash
   supabase init
   supabase start
   ```

3. Copy the printed **API URL**, **anon key**, **service role key**, and **JWT secret** into `.env` (see `.env.example`).

The FastAPI app validates access tokens with **JWKS** (hosted) or **HS256 + `SUPABASE_JWT_SECRET`** (CLI local); it does **not** call Supabase on every protected request.

For Docker-wide orchestration, prefer `supabase start` (official stack). The root `docker-compose.yml` remains focused on app Postgres/Redis/MinIO/OpenSearch.
