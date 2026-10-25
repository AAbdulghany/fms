import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { Asset, AssetLifecycleStatus } from "@/lib/types";
import { EmptyState } from "@/shared/components/EmptyState";
import { AssetLifecycleBadge } from "@/features/assets/components/AssetLifecycleBadge";
import { AssetRegisterModal } from "@/features/assets/components/AssetRegisterModal";
import { AssetImportModal } from "@/features/assets/components/AssetImportModal";

type AssetOutApi = {
  id: string;
  site_id: string;
  site_name?: string | null;
  name: string;
  category: string;
  label_code?: string | null;
  next_due_at?: string | null;
  lifecycle_status: AssetLifecycleStatus;
  current_repair_count: number;
  max_age_years?: number | null;
  installed_on?: string | null;
  warranty_until?: string | null;
  expected_eol_date?: string | null;
};

type DisplayAsset = Asset & { next_due_at?: string | null };

function computeEolDate(installedOn: string | null | undefined, maxAgeYears: number | null | undefined): string | undefined {
  if (!installedOn || !maxAgeYears) return undefined;
  const d = new Date(installedOn);
  d.setFullYear(d.getFullYear() + maxAgeYears);
  return d.toISOString().slice(0, 10);
}

function mapToDisplayAsset(a: AssetOutApi): DisplayAsset {
  let ageYears = 0;
  if (a.installed_on) {
    const d = new Date(a.installed_on);
    ageYears = Math.max(0, (Date.now() - d.getTime()) / (365.25 * 24 * 3600 * 1000));
  }
  const eolDate = a.expected_eol_date ?? computeEolDate(a.installed_on, a.max_age_years);
  return {
    id: a.id,
    asset_id: a.label_code || `${a.id.slice(0, 8)}…`,
    name: a.name,
    site_id: a.site_id,
    site_name: a.site_name ?? undefined,
    company_id: "",
    type: a.category,
    category: a.category,
    lifecycle_status: a.lifecycle_status,
    age_years: ageYears,
    repair_count: a.current_repair_count,
    installation_date: a.installed_on ?? "",
    expected_lifespan_years: a.max_age_years ?? 5,
    lifespan_percentage: 50,
    warranty_until: a.warranty_until ?? undefined,
    expected_eol_date: eolDate,
    next_due_at: a.next_due_at ?? null,
  };
}

function warrantyBadge(warrantyUntil: string | undefined) {
  if (!warrantyUntil) return null;
  const isActive = new Date(warrantyUntil) >= new Date();
  return isActive
    ? { label: "Active", className: "bg-success-light text-success-dark" }
    : { label: "Expired", className: "bg-neutral-100 text-neutral-500 line-through" };
}

function daysUntil(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const due = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  due.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / (24 * 3600 * 1000));
}

export default function AssetsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialSiteId = searchParams.get("site_id") || undefined;
  const openOnLoad = searchParams.get("register") === "1";

  const [assets, setAssets] = useState<DisplayAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [lifecycleFilter, setLifecycleFilter] = useState<AssetLifecycleStatus | "all">("all");
  /** "" = all assets; "all" = maintenance view (has schedule); overdue | due_week */
  const [maintenanceFilter, setMaintenanceFilter] = useState<string>("");
  const [phoneChip, setPhoneChip] = useState<"all" | "active" | "due">("all");
  const [registerOpen, setRegisterOpen] = useState(openOnLoad);
  const [importOpen, setImportOpen] = useState(false);

  const loadAssets = () => {
    void (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (initialSiteId) params.set("site_id", initialSiteId);
        if (maintenanceFilter === "all") {
          params.set("view", "maintenance");
          params.set("sort", "next_due");
        } else if (maintenanceFilter) {
          params.set("view", "maintenance");
          params.set("sort", "next_due");
          params.set("filter", maintenanceFilter);
        }
        const q = params.toString() ? `?${params.toString()}` : "";
        const data = await apiFetch<AssetOutApi[]>(`/assets${q}`);
        setAssets(data.map(mapToDisplayAsset));
      } catch (error) {
        console.error("Failed to fetch assets", error);
        setAssets([]);
      } finally {
        setLoading(false);
      }
    })();
  };

  useEffect(() => {
    loadAssets();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload on site / maintenance filter
  }, [initialSiteId, maintenanceFilter]);

  const filteredAssets = assets.filter((asset) => {
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      asset.asset_id.toLowerCase().includes(query) ||
      (asset.name && asset.name.toLowerCase().includes(query)) ||
      asset.type.toLowerCase().includes(query) ||
      asset.category.toLowerCase().includes(query) ||
      (asset.site_name && asset.site_name.toLowerCase().includes(query));

    const matchesLifecycle =
      lifecycleFilter === "all" || asset.lifecycle_status === lifecycleFilter;

    return matchesSearch && matchesLifecycle;
  });

  const phoneAssets = filteredAssets.filter((asset) => {
    if (phoneChip === "active") return asset.lifecycle_status === "active";
    if (phoneChip === "due") {
      const remaining = daysUntil(asset.next_due_at);
      return remaining != null && remaining <= 7;
    }
    return true;
  });

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  const clearAllFilters = () => {
    setSearchQuery("");
    setLifecycleFilter("all");
    setMaintenanceFilter("");
  };

  return (
    <div className="space-y-6">
      <div className="space-y-3 lg:hidden">
        <h1 className="text-lg font-semibold text-neutral-900">{t("assets")}</h1>
        <input
          type="text"
          placeholder={`${t("search")} ${t("assets")}`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-neutral-300 bg-neutral-0 px-3 py-2 text-sm"
        />
        <button
          type="button"
          data-testid="register-asset-button-mobile"
          className="min-h-11 w-full rounded-xl bg-primary-600 text-sm font-semibold text-white"
          onClick={() => setRegisterOpen(true)}
        >
          + {t("register_asset")}
        </button>
        <div className="flex gap-2">
          {(
            [
              ["all", t("all")],
              ["active", t("lifecycle_active")],
              ["due", t("due")],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setPhoneChip(id)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                phoneChip === id
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="hidden flex-wrap items-center justify-between gap-3 lg:flex">
        <h1 className="text-3xl font-semibold text-neutral-900">{t("assets")}</h1>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/assets/maintenance-calendar"
            data-testid="open-maintenance-calendar"
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-50"
          >
            {t("maintenance_calendar") || "Maintenance calendar"}
          </Link>
          <button
            type="button"
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-50"
            onClick={() => setImportOpen(true)}
          >
            {t("import_csv") || "Import CSV"}
          </button>
          <button
            type="button"
            data-testid="register-asset-button"
            className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            onClick={() => setRegisterOpen(true)}
          >
            + {t("register_asset")}
          </button>
        </div>
      </div>

      <div className="hidden space-y-4 lg:block">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder={`${t("search")} ${t("assets").toLowerCase()}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2" data-testid="maintenance-filter-bar">
          <button
            type="button"
            onClick={() => setMaintenanceFilter("")}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              maintenanceFilter === "" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
          >
            {t("all") || "All"}
          </button>
          <button
            type="button"
            onClick={() => setMaintenanceFilter("all")}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              maintenanceFilter === "all" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
          >
            {t("all_maintenance") || "All maintenance"}
          </button>
          <button
            type="button"
            onClick={() => setMaintenanceFilter("overdue")}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              maintenanceFilter === "overdue" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
          >
            {t("overdue") || "Overdue"}
          </button>
          <button
            type="button"
            onClick={() => setMaintenanceFilter("due_week")}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              maintenanceFilter === "due_week" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
          >
            {t("due_this_week") || "Due this week"}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(["all", "active", "warning", "end_of_life", "replaced"] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setLifecycleFilter(status === "all" ? "all" : status)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                lifecycleFilter === status
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              {status === "all" ? t("all") : t(`lifecycle_${status}`)}
            </button>
          ))}
        </div>
      </div>

      {assets.length === 0 && !maintenanceFilter ? (
        <EmptyState
          icon={
            <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
          }
          title={t("no_assets")}
          description="Register your first asset to start tracking lifecycle and maintenance history."
          action={{
            label: `+ ${t("register_asset")}`,
            onClick: () => setRegisterOpen(true),
          }}
        />
      ) : filteredAssets.length === 0 ? (
        <EmptyState
          icon={
            <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          }
          title={t("no_results")}
          description={
            maintenanceFilter === "overdue"
              ? t("no_overdue_assets") || "No assets with overdue preventive maintenance."
              : maintenanceFilter === "due_week"
                ? t("no_due_this_week") || "No assets due for maintenance in the next 7 days."
                : "Try adjusting your search or filter criteria."
          }
          action={{
            label: t("clear_filters"),
            onClick: clearAllFilters,
          }}
        />
      ) : (
        <>
          <ul className="space-y-2 lg:hidden">
            {phoneAssets.length === 0 ? (
              <li className="rounded-xl border border-neutral-200 bg-neutral-0 px-3 py-6 text-center text-sm text-neutral-500">
                {t("no_results")}
              </li>
            ) : (
              phoneAssets.map((asset) => {
                const remaining = daysUntil(asset.next_due_at);
                const due = remaining != null && remaining <= 7;
                return (
                  <li key={asset.id}>
                    <button
                      type="button"
                      onClick={() => navigate(`/assets/${asset.id}`)}
                      className="flex w-full items-center gap-3 rounded-xl border border-neutral-200 bg-neutral-0 px-3 py-3 text-start"
                    >
                      <svg
                        className="h-5 w-5 shrink-0 text-primary-700"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={1.8}
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                        />
                      </svg>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-semibold text-neutral-900">
                          {asset.name || "—"}
                        </span>
                        <span className="block truncate text-xs text-neutral-500">
                          {asset.site_name || asset.category}
                        </span>
                      </span>
                      {due ? (
                        <span className="shrink-0 rounded-md bg-amber-100 px-1.5 py-0.5 text-[11px] font-semibold text-amber-900">
                          {t("due")}
                        </span>
                      ) : (
                        <AssetLifecycleBadge status={asset.lifecycle_status} />
                      )}
                    </button>
                  </li>
                );
              })
            )}
          </ul>

          <div className="hidden overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm lg:block">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("asset_name")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("asset_type")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("site_name")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("lifecycle_status")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("next_due") || "Next due"}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("warranty")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("asset_age")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("eol_date")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {filteredAssets.map((asset) => {
                    const wb = warrantyBadge(asset.warranty_until);
                    const remaining = daysUntil(asset.next_due_at);
                    return (
                      <tr
                        key={asset.id}
                        onClick={() => navigate(`/assets/${asset.id}`)}
                        className="cursor-pointer transition-colors hover:bg-neutral-50"
                      >
                        <td className="px-6 py-4">
                          <div className="text-sm font-semibold text-neutral-900">{asset.name || "—"}</div>
                        </td>
                        <td className="px-6 py-4 text-sm text-neutral-700">{asset.category}</td>
                        <td className="px-6 py-4 text-sm text-neutral-900">{asset.site_name || "—"}</td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <AssetLifecycleBadge status={asset.lifecycle_status} />
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          {asset.next_due_at ? (
                            <span
                              className={
                                remaining != null && remaining < 0
                                  ? "font-medium text-error-main"
                                  : remaining != null && remaining <= 7
                                    ? "font-medium text-warning-main"
                                    : "text-neutral-700"
                              }
                            >
                              {new Date(asset.next_due_at).toLocaleDateString()}
                              {remaining != null && (
                                <span className="ms-1 text-xs text-neutral-500">
                                  ({remaining < 0
                                    ? t("days_overdue", { count: Math.abs(remaining) }) ||
                                      `${Math.abs(remaining)}d overdue`
                                    : t("days_remaining", { count: remaining }) || `${remaining}d`})
                                </span>
                              )}
                            </span>
                          ) : (
                            <span className="text-neutral-400">—</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          {wb ? (
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${wb.className}`}>
                              {t(wb.label === "Active" ? "warranty_active" : "warranty_expired") || wb.label}
                            </span>
                          ) : (
                            <span className="text-neutral-400">—</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <span
                            className={`font-medium ${
                              asset.age_years >= 10
                                ? "text-error-main"
                                : asset.age_years >= 5
                                  ? "text-warning-main"
                                  : "text-neutral-900"
                            }`}
                          >
                            {asset.age_years.toFixed(1)} yrs
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-700">
                          {asset.expected_eol_date
                            ? new Date(asset.expected_eol_date).toLocaleDateString()
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <AssetRegisterModal
        open={registerOpen}
        onClose={() => setRegisterOpen(false)}
        onCreated={() => loadAssets()}
        initialSiteId={initialSiteId}
      />
      <AssetImportModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onDone={() => loadAssets()}
      />
    </div>
  );
}
