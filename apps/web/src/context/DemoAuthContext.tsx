import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface DemoUser {
  email: string;
  name: string;
}

interface DemoAuthState {
  user: DemoUser | null;
  login: (email: string, _password: string) => void;
  logout: () => void;
}

const DemoAuthContext = createContext<DemoAuthState | null>(null);

export function DemoAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DemoUser | null>(null);

  const login = useCallback((email: string, _password: string) => {
    const safe = email.trim() || "demo@verifiedsignal.io";
    setUser({
      email: safe,
      name: safe.split("@")[0].replace(/\./g, " "),
    });
  }, []);

  const logout = useCallback(() => setUser(null), []);

  const value = useMemo(
    () => ({
      user,
      login,
      logout,
    }),
    [user, login, logout],
  );

  return <DemoAuthContext.Provider value={value}>{children}</DemoAuthContext.Provider>;
}

export function useDemoAuth(): DemoAuthState {
  const ctx = useContext(DemoAuthContext);
  if (!ctx) {
    throw new Error("useDemoAuth must be used within DemoAuthProvider");
  }
  return ctx;
}
