import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useNotifications } from "../contexts/NotificationContext";

export default function NotificationBell() {
  const { t } = useTranslation();
  const { items, unreadCount, markRead, toast, clearToast } = useNotifications();
  const [open, setOpen] = useState(false);

  return (
    <>
      {toast && (
        <div className="fixed bottom-4 end-4 z-50 max-w-sm rounded-lg bg-primary-800 px-4 py-3 text-sm text-white shadow-lg">
          <div className="flex items-start justify-between gap-2">
            <span>{toast}</span>
            <button type="button" className="text-white/80 hover:text-white" onClick={clearToast}>
              ×
            </button>
          </div>
        </div>
      )}

      <div className="relative">
        <button
          type="button"
          className="relative rounded-md p-2 text-neutral-600 hover:bg-neutral-100"
          aria-label={t("notifications")}
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          {unreadCount > 0 && (
            <span className="absolute end-0 top-0 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-error-main px-1 text-[10px] font-bold text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>

        {open && (
          <div className="absolute end-0 z-50 mt-2 w-80 max-h-96 overflow-y-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-lg">
            <div className="border-b border-neutral-200 px-4 py-2 font-semibold text-neutral-900">
              {t("notifications")}
            </div>
            {items.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-neutral-500">{t("no_notifications")}</div>
            ) : (
              <ul className="divide-y divide-neutral-100">
                {items.map((n) => (
                  <li key={n.id}>
                    {n.work_order_id ? (
                      <Link
                        to={`/work-orders/${n.work_order_id}`}
                        className={`block px-4 py-3 text-sm hover:bg-neutral-50 ${!n.read ? "bg-primary-50/50" : ""}`}
                        onClick={() => {
                          markRead(n.id);
                          setOpen(false);
                        }}
                      >
                        {n.title}
                        <div className="mt-1 text-xs text-neutral-500">{(n.created_at || "").slice(0, 16)}</div>
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className={`w-full px-4 py-3 text-start text-sm hover:bg-neutral-50 ${!n.read ? "bg-primary-50/50" : ""}`}
                        onClick={() => markRead(n.id)}
                      >
                        {n.title}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </>
  );
}
