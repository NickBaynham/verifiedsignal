# VerifiedSignal Web (React + Vite)

The SPA should use **Supabase JS** only where the auth spec requires it (e.g. password reset from emailed link); **login, signup, logout, and refresh** should call the FastAPI API (`VITE_API_URL`) so the refresh token stays **httpOnly** on the API origin.

## Setup

```bash
npm create vite@latest . -- --template react-ts
# If the directory is non-empty, create in a temp folder and merge, or use `npm init vite@latest`.
npm install @supabase/supabase-js @supabase/auth-ui-react @supabase/auth-ui-shared react-router-dom
```

Copy `.env.example` to `.env.local` (gitignored) and set:

- `VITE_SUPABASE_URL` — same as `SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY` — anon key (reset-password / URL hash flows)
- `VITE_API_URL` — FastAPI base, e.g. `http://127.0.0.1:8000`

Implement the routes and `AuthContext` described in the product spec (`docs/auth-supabase.md` at repo root).
