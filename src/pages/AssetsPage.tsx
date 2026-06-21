import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import type { Asset, AssetLifecycleStatus, User } from "../lib/types";
import { hasAnyRole } from "../lib/roles";
import { EmptyState } from "../components/EmptyState";
import { AssetLifecycleBadge } from "../components/AssetLifecycleBadge";
import { AssetRegisterModal } from "../components/AssetRegisterModal";
import { AssetImportModal } from "../components/AssetImportModal";
import { MaintenanceCalendar } from "../components/MaintenanceCalendar";
import { AssetWorkOrderPanel } from "../components/AssetWorkOrderPanel";

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

function computeEolDate(installedOn: string | null | undefined, maxAgeYears: number | null | undefined): string | undefined {
  if (!installedOn || !maxAgeYears) return undefined;
  const d = new Date(installedOn);
  d.setFullYear(d.getFullYear() + maxAgeYears);
  return d.toISOString().slice(0, 10);
}

function mapToDisplayAsset(a: AssetOutApi): Asset {
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
  };
}

function warrantyBadge(warrantyUntil: string | undefined) {
  if (!warrantyUntil) return null;
  const isActive = new Date(warrantyUntil) >= new Date();
  return isActive
    ? { label: "Active", className: "bg-success-light text-success-dark" }
    : { label: "Expired", className: "bg-neutral-100 text-neutral-500 line-through" };
}

export default function AssetsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialSiteId = searchParams.get("site_id") || undefined;
  const openOnLoad = searchParams.get("register") === "1";

  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [lifecycleFilter, setLifecycleFilter] = useState<AssetLifecycleStatus | "all">("all");
  const [maintenanceFilter, setMaintenanceFilter] = useState<string>("");
  const [registerOpen, setRegisterOpen] = useState(openOnLoad);
  const [importOpen, setImportOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [clients, setClients] = useState<{ id: string; legal_name: string }[]>([]);
  const [clientFilter, setClientFilter] = useState("");
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const me = await apiFetch<User>("/users/me");
        setUser(me);
        if (hasAnyRole(me.role, ["super_admin", "company_admin"])) {
          const clientRows = await apiFetch<{ id: string; legal_name: string }[]>("/clients");
          setClients(clientRows);
        }
      } catch (err) {
        console.error("Failed to load user context", err);
      }
    })();
  }, []);

  const loadAssets = () => {
    void (async () => {
      try {
        const params = new URLSearchParams();
        if (initialSiteId) params.set("site_id", initialSiteId);
        if (maintenanceFilter) {
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

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  const showClientFilter = user && hasAnyRole(user.role, ["super_admin", "company_admin"]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold text-neutral-900">{t("assets")}</h1>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-50"
            onClick={() => setImportOpen(true)}
          >
            {t("import_csv") || "Import CSV"}
          </button>
          <button
            type="button"
            className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            onClick={() => setRegisterOpen(true)}
          >
            + {t("register_asset")}
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-3">
          {showClientFilter && clients.length > 0 && (
            <div className="flex items-center gap-2">
              <label htmlFor="client-filter" className="text-sm text-neutral-600">
                {t("select_client") || "Client"}
              </label>
              <select
                id="client-filter"
                data-testid="assets-client-filter"
                className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm"
                value={clientFilter}
                onChange={(e) => {
                  setClientFilter(e.target.value);
                  setSelectedAssetId(null);
                }}
              >
                <option value="">{t("all_clients") || "All clients"}</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.legal_name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <MaintenanceCalendar
            clientId={clientFilter || undefined}
            selectedAssetId={selectedAssetId}
            onSelectAsset={setSelectedAssetId}
          />
        </div>
        <AssetWorkOrderPanel assetId={selectedAssetId} />
      </div>

      {assets.length > 0 && (
        <div className="space-y-4">
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

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setMaintenanceFilter("")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                maintenanceFilter === "" ? "bg-primary-600 text-white" : "border border-neutral-300"
              }`}
            >
              {t("all_maintenance") || "All maintenance"}
            </button>
            <button
              type="button"
              onClick={() => setMaintenanceFilter("overdue")}
              className={`rounded-lg px-3 py-1.5 text-sm ${maintenanceFilter === "overdue" ? "bg-primary-600 text-white" : "border"}`}
            >
              {t("overdue") || "Overdue"}
            </button>
            <button
              type="button"
              onClick={() => setMaintenanceFilter("due_week")}
              className={`rounded-lg px-3 py-1.5 text-sm ${maintenanceFilter === "due_week" ? "bg-primary-600 text-white" : "border"}`}
            >
              {t("due_this_week") || "Due week"}
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
      )}

      {assets.length === 0 ? (
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
          description="Try adjusting your search or filter criteria."
          action={{
            label: t("clear_filters"),
            onClick: () => {
              setSearchQuery("");
              setLifecycleFilter("all");
            },
          }}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
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
                  return (
                  <tr
                    key={asset.id}
                    onClick={() => navigate(`/assets/${asset.id}`)}
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-semibold text-neutral-900">
                        {asset.name || "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-700">
                      {asset.category}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">
                      {asset.site_name || "—"}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <AssetLifecycleBadge status={asset.lifecycle_status} />
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
