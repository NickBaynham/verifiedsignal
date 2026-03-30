/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** When unset or empty, the UI uses local demo data and demo login. */
  readonly VITE_API_URL?: string;
  readonly VITE_SUPABASE_URL?: string;
  readonly VITE_SUPABASE_ANON_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
