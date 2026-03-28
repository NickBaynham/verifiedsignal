# Supabase auth integration

## Backend (implemented under `app/`)

- **Settings:** `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL`, `JWT_ALGORITHM`, `JWT_AUDIENCE`, `CORS_ORIGINS`, `AUTH_COOKIE_SECURE`.
- **JWT validation:** `app/auth/jwt_verify.py` — HS256 with shared secret when `SUPABASE_JWKS_URL` is empty; otherwise RS256 via JWKS. `app/auth/dependencies.py` exposes `get_current_user` (**401** if missing/invalid Bearer).
- **Session routes:** `app/api/routes/session_auth.py` mounted at `/auth` — signup, login (sets httpOnly refresh cookie on path `/auth`), refresh, logout, reset-password email.
- **Protected API examples:** `GET/POST /api/v1/documents`, `GET /api/v1/collections`, `GET /api/v1/users/me`.
- **CORS:** credentials enabled for `CORS_ORIGINS`.

Refresh cookie name: `vs_refresh_token` (path `/auth`).

## Frontend (`apps/web/`)

Scaffold with Vite + React + TypeScript; keep access tokens **in memory only**; call FastAPI for session operations. See `apps/web/README.md` and `supabase/README.md`.

## Tests

`tests/unit/test_session_auth.py` mocks the Supabase client; integration tests override `get_current_user` for database-heavy flows.
