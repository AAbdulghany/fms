import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, getAccessToken } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [tokenPresent, setTokenPresent] = useState(() => Boolean(getAccessToken()));

  useEffect(() => {
    const syncToken = () => {
      const next = Boolean(getAccessToken());
      setTokenPresent(next);
      if (!next) {
        // Drop cached tenant data on logout / token clear.
        queryClient.clear();
      }
    };
    window.addEventListener("fms-auth-token-changed", syncToken);
    const onStorage = (e: StorageEvent) => {
      if (e.key === "access_token") syncToken();
    };
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("fms-auth-token-changed", syncToken);
      window.removeEventListener("storage", onStorage);
    };
  }, [queryClient]);

  const meQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: () => apiFetch<User>("/users/me"),
    enabled: tokenPresent,
    staleTime: 5 * 60_000,
    gcTime: 30 * 60_000,
    retry: false,
    refetchOnWindowFocus: true,
  });

  // Recover if cache was seeded from login UserPublic (no features) before this fix.
  useEffect(() => {
    if (!tokenPresent || !meQuery.data || Array.isArray(meQuery.data.features)) return;
    void queryClient.invalidateQueries({ queryKey: queryKeys.me });
  }, [tokenPresent, meQuery.data, queryClient]);

  const setUser = useCallback(
    (next: User | null) => {
      if (next) {
        queryClient.setQueryData(queryKeys.me, next);
        // Login/refresh return UserPublic without subscription `features`.
        // Invalidate so GET /users/me fills the full profile (nav feature gates).
        if (!Array.isArray(next.features)) {
          void queryClient.invalidateQueries({ queryKey: queryKeys.me });
        }
      } else {
        queryClient.setQueryData(queryKeys.me, null);
        queryClient.removeQueries({ queryKey: queryKeys.me });
      }
    },
    [queryClient]
  );

  const refresh = useCallback(async (): Promise<User | null> => {
    if (!getAccessToken()) {
      setUser(null);
      return null;
    }
    try {
      const result = await queryClient.fetchQuery({
        queryKey: queryKeys.me,
        queryFn: () => apiFetch<User>("/users/me"),
        staleTime: 0,
      });
      return result;
    } catch {
      setUser(null);
      return null;
    }
  }, [queryClient, setUser]);

  const user = tokenPresent ? (meQuery.data ?? null) : null;

  let status: AuthStatus;
  if (!tokenPresent) {
    status = "anonymous";
  } else if (meQuery.isPending || (meQuery.isFetching && !meQuery.data && !meQuery.isError)) {
    status = "loading";
  } else if (user) {
    status = "authenticated";
  } else {
    status = "anonymous";
  }

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
