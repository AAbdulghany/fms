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
import { getAccessToken } from "../lib/api";

export type NotificationItem = {
  id: string;
  type: string;
  title: string;
  work_order_id?: string;
  created_at: string;
  read: boolean;
};

type Ctx = {
  items: NotificationItem[];
  unreadCount: number;
  toast: string | null;
  markRead: (id: string) => void;
  clearToast: () => void;
};

const NotificationContext = createContext<Ctx | null>(null);

function pushToast(setter: (s: string | null) => void, msg: string) {
  setter(msg);
  window.setTimeout(() => setter(null), 4000);
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const markRead = useCallback((id: string) => {
    setItems((prev) => prev.map((x) => (x.id === id ? { ...x, read: true } : x)));
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    let cancelled = false;

    const connect = () => {
      const token = getAccessToken();
      wsRef.current?.close();
      wsRef.current = null;
      if (!token || cancelled) return;

      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      const url = `${proto}//${window.location.host}/api/v1/notifications/ws?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string) as {
            type?: string;
            title?: string;
            work_order_id?: string;
          };
          const title =
            data.title ||
            (data.type === "work_order.status_changed" ? "Work order status updated" : "Notification");
          const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
          const item: NotificationItem = {
            id,
            type: data.type ?? "event",
            title,
            work_order_id: data.work_order_id,
            created_at: new Date().toISOString(),
            read: false,
          };
          setItems((prev) => [item, ...prev].slice(0, 50));
          pushToast(setToast, title);
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
  }, []);

  const unreadCount = useMemo(() => items.filter((i) => !i.read).length, [items]);

  const value = useMemo(
    () => ({ items, unreadCount, toast, markRead, clearToast }),
    [items, unreadCount, toast, markRead, clearToast]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications requires NotificationProvider");
  return ctx;
}
