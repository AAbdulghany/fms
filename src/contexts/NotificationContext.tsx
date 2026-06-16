import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { apiFetch, getAccessToken } from "../lib/api";

export type NotificationItem = {
  id: string;
  type: string;
  title: string;
  work_order_id?: string;
  action?: string;
  created_at: string;
  read: boolean;
};

type Ctx = {
  items: NotificationItem[];
  unreadCount: number;
  toast: string | null;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clearToast: () => void;
  refresh: () => void;
};

const NotificationContext = createContext<Ctx | null>(null);

function pushToast(setter: (s: string | null) => void, msg: string) {
  setter(msg);
  window.setTimeout(() => setter(null), 4000);
}

type ApiNotification = {
  id: string;
  type: string;
  title: string;
  work_order_id?: string | null;
  action?: string | null;
  created_at: string;
  read: boolean;
};

function mapItem(n: ApiNotification): NotificationItem {
  return {
    id: n.id,
    type: n.type,
    title: n.title,
    work_order_id: n.work_order_id ?? undefined,
    action: n.action ?? undefined,
    created_at: n.created_at,
    read: n.read,
  };
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const seenIds = useRef<Set<string>>(new Set());

  const hydrate = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setItems([]);
      return;
    }
    try {
      const rows = await apiFetch<ApiNotification[]>("/notifications");
      const mapped = rows.map(mapItem);
      seenIds.current = new Set(mapped.map((x) => x.id));
      setItems(mapped);
    } catch {
      /* backend may be down */
    }
  }, []);

  const markRead = useCallback((id: string) => {
    setItems((prev) => prev.map((x) => (x.id === id ? { ...x, read: true } : x)));
    void apiFetch(`/notifications/${id}/read`, { method: "PATCH" }).catch(() => {});
  }, []);

  const markAllRead = useCallback(() => {
    setItems((prev) => prev.map((x) => ({ ...x, read: true })));
    void apiFetch("/notifications/read-all", { method: "POST" }).catch(() => {});
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    let cancelled = false;

    const connect = () => {
      const token = getAccessToken();
      wsRef.current?.close();
      wsRef.current = null;
      if (!token || cancelled) return;

      void hydrate();

      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      const url = `${proto}//${window.location.host}/api/v1/notifications/ws?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string) as ApiNotification & { title?: string };
          const id = data.id ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
          if (seenIds.current.has(id)) return;
          seenIds.current.add(id);
          const item = mapItem({
            id,
            type: data.type ?? "event",
            title: data.title ?? "Notification",
            work_order_id: data.work_order_id,
            action: data.action,
            created_at: data.created_at ?? new Date().toISOString(),
            read: false,
          });
          setItems((prev) => [item, ...prev].slice(0, 50));
          pushToast(setToast, item.title);
        } catch {
          /* ignore */
        }
      };

      ws.onerror = () => {
        /* connection may fail if backend down; silent */
      };
    };

    connect();

    const onAuthChange = () => {
      seenIds.current.clear();
      connect();
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
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [hydrate]);

  const unreadCount = useMemo(() => items.filter((i) => !i.read).length, [items]);

  const value = useMemo(
    () => ({ items, unreadCount, toast, markRead, markAllRead, clearToast, refresh: hydrate }),
    [items, unreadCount, toast, markRead, markAllRead, clearToast, hydrate]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications requires NotificationProvider");
  return ctx;
}
