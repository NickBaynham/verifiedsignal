import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchCurrentUser } from "../api/users";
import * as sessionAuth from "../api/sessionAuth";
import { isApiBackend } from "../config";

const DEMO_USER_KEY = "verifiedsignal_demo_user";
/** Survives full page loads (unlike httpOnly cookies in some dev setups). Cleared on logout. */
const API_ACCESS_TOKEN_KEY = "verifiedsignal_api_access_token";

export interface AuthUser {
  email: string;
  name: string;
}

interface AuthState {
  user: AuthUser | null;
  /** Present only when `VITE_API_URL` is set and the user has a session. */
  accessToken: string | null;
  /** True while attempting cookie refresh on load (API mode only). */
  authLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

function readDemoUser(): AuthUser | null {
  try {
    const raw = sessionStorage.getItem(DEMO_USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return null;
    const email = (parsed as { email?: string }).email;
    const name = (parsed as { name?: string }).name;
    if (typeof email !== "string" || typeof name !== "string") return null;
    return { email, name };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const apiMode = isApiBackend();
  const [user, setUser] = useState<AuthUser | null>(() => {
    if (apiMode) return null;
    return typeof sessionStorage !== "undefined" ? readDemoUser() : null;
  });
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(() => apiMode);

  useEffect(() => {
    if (apiMode) return;
    if (user) sessionStorage.setItem(DEMO_USER_KEY, JSON.stringify(user));
    else sessionStorage.removeItem(DEMO_USER_KEY);
  }, [apiMode, user]);

  useEffect(() => {
    if (!apiMode) {
      setAuthLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const stored =
          typeof sessionStorage !== "undefined" ? sessionStorage.getItem(API_ACCESS_TOKEN_KEY) : null;
        let token = stored;
        if (!token) {
          const tok = await sessionAuth.refreshAccessToken();
          if (cancelled) return;
          token = tok?.access_token ?? null;
        }
        if (!token) {
          if (!cancelled) {
            setAccessToken(null);
            setUser(null);
            sessionStorage.removeItem(API_ACCESS_TOKEN_KEY);
          }
          return;
        }
        setAccessToken(token);
        const me = await fetchCurrentUser(token);
        if (cancelled) return;
        sessionStorage.setItem(API_ACCESS_TOKEN_KEY, token);
        setUser({
          email: me.email ?? me.user_id,
          name: displayNameFromMe(me),
        });
      } catch {
        if (!cancelled) {
          setAccessToken(null);
          setUser(null);
          sessionStorage.removeItem(API_ACCESS_TOKEN_KEY);
        }
      } finally {
        if (!cancelled) setAuthLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiMode]);

  const login = useCallback(
    async (email: string, password: string) => {
      if (!apiMode) {
        const safe = email.trim() || "demo@verifiedsignal.io";
        setUser({
          email: safe,
          name: safe.split("@")[0].replace(/\./g, " "),
        });
        return;
      }
      const tok = await sessionAuth.loginWithPassword(email.trim(), password);
      sessionStorage.setItem(API_ACCESS_TOKEN_KEY, tok.access_token);
      setAccessToken(tok.access_token);
      const me = await fetchCurrentUser(tok.access_token);
      setUser({
        email: me.email ?? me.user_id,
        name: displayNameFromMe(me),
      });
    },
    [apiMode],
  );

  const logout = useCallback(async () => {
    if (apiMode) {
      try {
        await sessionAuth.logoutSession();
      } catch {
        /* clear local session regardless */
      }
      setAccessToken(null);
      sessionStorage.removeItem(API_ACCESS_TOKEN_KEY);
    }
    setUser(null);
  }, [apiMode]);

  const value = useMemo(
    () => ({
      user,
      accessToken,
      authLoading,
      login,
      logout,
    }),
    [user, accessToken, authLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function displayNameFromMe(me: { display_name: string | null; email: string | null; user_id: string }): string {
  if (me.display_name?.trim()) return me.display_name.trim();
  const em = me.email;
  if (em) return em.split("@")[0]!.replace(/\./g, " ");
  return me.user_id.slice(0, 8);
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
