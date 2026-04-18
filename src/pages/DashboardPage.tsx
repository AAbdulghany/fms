import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import { urgencyBadgeClass, workOrderStatusPillClass } from "../lib/workOrderDisplay";
import type {
  PaginatedWorkOrders,
  User,
  DashboardStats,
  DashboardSummary,
  WorkOrder,
} from "../lib/types";
import { StatsCard } from "../components/StatsCard";

export function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentWOs, setRecentWOs] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const userData = await apiFetch<User>("/users/me");
        setUser(userData);

        const summary = await apiFetch<DashboardSummary>("/dashboard/summary");

        const wo = await apiFetch<PaginatedWorkOrders>("/work-orders?page_size=5");
        setRecentWOs(wo.data.slice(0, 5));

        const dashStats: DashboardStats = {
          active_wo_count: summary.open_work_orders,
          companies_count: summary.clients_count ?? undefined,
          sites_count: summary.sites_count ?? undefined,
          assets_count: summary.assets_count ?? undefined,
          technicians_count: summary.technicians_count ?? undefined,
          pending_invoices_draft: summary.pending_invoices_draft ?? undefined,
          my_tasks_count: summary.my_assigned_open ?? undefined,
          in_progress_count: summary.my_in_progress ?? undefined,
          completed_week_count: summary.completed_this_week,
          assets_at_eol_count: summary.assets_at_eol ?? undefined,
        };

        setStats(dashStats);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!user || !stats) {
    return (
      <div className="text-center text-neutral-600">
        <p>{t("error")}</p>
      </div>
    );
  }

  // Role-specific dashboard content
  const isSuperAdmin = user.role === "super_admin" || user.role === "company_admin";
  const isTechnician = user.role === "technician";
  const isClientAdmin = user.role === "client_admin";
  const isSiteManager = user.role === "site_manager";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-neutral-900">
          {t("welcome_back")}, {user.full_name}
        </h1>
        <p className="mt-1 text-sm text-neutral-600">{t(`role_${user.role}`)}</p>
      </div>

      {/* Stats Cards - Role-specific */}
      {isSuperAdmin && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            label={t("companies")}
            value={stats.companies_count ?? "—"}
            onClick={() => navigate("/companies")}
          />
          <StatsCard
            label={t("active_wos")}
            value={stats.active_wo_count}
            onClick={() => navigate("/work-orders")}
          />
          <StatsCard
            label={t("invoice_drafts")}
            value={stats.pending_invoices_draft ?? 0}
            onClick={() => navigate("/invoices")}
          />
          <StatsCard
            label={t("users")}
            value={stats.technicians_count ?? "—"}
            onClick={() => navigate("/users")}
          />
        </div>
      )}

      {isTechnician && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatsCard
            label={t("my_tasks")}
            value={stats.my_tasks_count ?? 0}
            subtitle={`${stats.my_tasks_count && stats.my_tasks_count > 0 ? "pending" : "all caught up"}`}
          />
          <StatsCard
            label={t("in_progress")}
            value={stats.in_progress_count ?? 0}
          />
          <StatsCard
            label={t("completed_this_week")}
            value={stats.completed_week_count ?? 0}
          />
        </div>
      )}

      {isClientAdmin && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatsCard
            label={t("sites_count")}
            value={stats.sites_count ?? "—"}
            onClick={() => navigate("/sites")}
          />
          <StatsCard
            label={t("active_wos")}
            value={stats.active_wo_count}
            onClick={() => navigate("/work-orders")}
          />
          <StatsCard
            label={t("invoice_drafts")}
            value={stats.pending_invoices_draft ?? 0}
            onClick={() => navigate("/invoices")}
          />
        </div>
      )}

      {isSiteManager && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatsCard
            label={t("assets")}
            value={stats.assets_count ?? "—"}
            subtitle={stats.assets_at_eol_count ? `${stats.assets_at_eol_count} at EOL` : undefined}
            onClick={() => navigate("/assets")}
          />
          <StatsCard
            label={t("active_wos")}
            value={stats.active_wo_count}
            onClick={() => navigate("/work-orders")}
          />
          <StatsCard
            label="Overdue Maintenance"
            value={stats.overdue_maintenance_count ?? 0}
          />
        </div>
      )}

      {/* Recent Work Orders */}
      {recentWOs.length > 0 && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
          <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4">
            <h2 className="text-lg font-medium text-neutral-900">
              {isTechnician ? t("my_work_orders") : t("recent_work_orders")}
            </h2>
            <Link
              to="/work-orders"
              className="text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              {t("view_all")} →
            </Link>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-neutral-200 bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("title")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("company")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("status")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("urgency")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {recentWOs.map((wo) => (
                  <tr
                    key={wo.id}
                    onClick={() => navigate(`/work-orders/${wo.id}`)}
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                  >
                    <td className="px-6 py-4 text-sm font-medium text-primary-600">
                      {wo.title || wo.id.slice(0, 8)}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">
                      {wo.company_name || "—"}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span className={workOrderStatusPillClass(wo.status)}>{wo.status}</span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span className={urgencyBadgeClass(wo.urgency)}>{t(wo.urgency)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-medium text-neutral-900">{t("quick_actions")}</h2>
        <div className="flex flex-wrap gap-3">
          {isSuperAdmin && (
            <>
              <button
                onClick={() => navigate("/work-orders")}
                className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              >
                + {t("create_work_order")}
              </button>
              <button
                onClick={() => navigate("/companies")}
                className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              >
                + {t("create_company")}
              </button>
              <button
                onClick={() => navigate("/assets")}
                className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              >
                + {t("register_asset")}
              </button>
            </>
          )}
          
          {isTechnician && (
            <>
              <button
                onClick={() => navigate("/work-orders")}
                className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              >
                {t("my_tasks")}
              </button>
            </>
          )}
          
          {isClientAdmin && (
            <>
              <button
                onClick={() => navigate("/work-orders")}
                className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              >
                + {t("create_work_order")}
              </button>
              <button
                onClick={() => navigate("/invoices")}
                className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              >
                {t("invoices")}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
