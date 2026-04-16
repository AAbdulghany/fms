import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import type { PaginatedWorkOrders } from "../lib/types";

export function DashboardPage() {
  const { t } = useTranslation();
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const wo = await apiFetch<PaginatedWorkOrders>("/work-orders?page_size=100");
        const nonClosed = wo.data.filter(
          (w) => !["closed", "cancelled"].includes(w.status)
        ).length;
        setOpen(nonClosed);
      } catch {
        setOpen(0);
      }
    })();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold text-neutral-900">{t("welcome")}</h1>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/work-orders"
          className="rounded-xl border border-neutral-200 bg-neutral-0 p-6 shadow-sm transition hover:border-primary-300"
        >
          <p className="text-sm text-neutral-500">{t("open_work_orders")}</p>
          <p className="text-3xl font-bold text-primary-600">{open ?? "—"}</p>
        </Link>
        <Link
          to="/invoices"
          className="rounded-xl border border-neutral-200 bg-neutral-0 p-6 shadow-sm transition hover:border-primary-300"
        >
          <p className="text-sm text-neutral-500">{t("invoices")}</p>
          <p className="text-lg text-neutral-700">SAR</p>
        </Link>
      </div>
    </div>
  );
}
