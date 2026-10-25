import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiFetch, getAccessToken } from "@/lib/api";
import type { User } from "@/lib/types";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  user: User | null;
  status: AuthStatus;
  /** True until the first auth resolution finishes. */
  loading: boolean;
  setUser: (user: User | null) => void;
  refresh: () => Promise<User | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/** Dedupes concurrent /users/me calls across StrictMode double-mount and consumers. */
let inflight: Promise<User> | null = null;

function fetchMeOnce(): Promise<User> {
  if (!inflight) {
    inflight = apiFetch<User>("/users/me").finally(() => {
      inflight = null;
    });
  }
  return inflight;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>(() =>
    getAccessToken() ? "loading" : "anonymous"
  );

  const setUser = useCallback((next: User | null) => {
    setUserState(next);
    setStatus(next ? "authenticated" : "anonymous");
  }, []);

  const refresh = useCallback(async (): Promise<User | null> => {
    if (!getAccessToken()) {
      setUser(null);
      return null;
    }
    try {
      const next = await fetchMeOnce();
      setUserState(next);
      setStatus("authenticated");
      return next;
    } catch {
      setUserState(null);
      setStatus("anonymous");
      return null;
    }
  }, [setUser]);

  useEffect(() => {
    let cancelled = false;

    const sync = async () => {
      if (!getAccessToken()) {
        if (!cancelled) {
          setUserState(null);
          setStatus("anonymous");
        }
        return;
      }
      if (!cancelled) setStatus((s) => (s === "authenticated" ? s : "loading"));
      try {
        const next = await fetchMeOnce();
        if (!cancelled) {
          setUserState(next);
          setStatus("authenticated");
        }
      } catch {
        if (!cancelled) {
          setUserState(null);
          setStatus("anonymous");
        }
      }
    };

    void sync();

    const onAuthChange = () => {
      void sync();
    };
    window.addEventListener("fms-auth-token-changed", onAuthChange);
    const onStorage = (e: StorageEvent) => {
      if (e.key === "access_token") onAuthChange();
    };
    window.addEventListener("storage", onStorage);

    return () => {
      cancelled = true;
      window.removeEventListener("fms-auth-token-changed", onAuthChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      loading: status === "loading",
      setUser,
      refresh,
    }),
    [user, status, setUser, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth requires AuthProvider");
  return ctx;
}
