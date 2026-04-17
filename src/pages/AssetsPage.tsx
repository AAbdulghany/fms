import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import type { Asset, AssetLifecycleStatus } from "../lib/types";
import { EmptyState } from "../components/EmptyState";
import { AssetLifecycleBadge } from "../components/AssetLifecycleBadge";
import { FilterBar } from "../components/FilterBar";

export default function AssetsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [lifecycleFilter, setLifecycleFilter] = useState<AssetLifecycleStatus | "all">("all");

  useEffect(() => {
    void (async () => {
      try {
        const data = await apiFetch<Asset[]>("/assets");
        setAssets(data);
      } catch (error) {
        console.error("Failed to fetch assets", error);
        setAssets([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filteredAssets = assets.filter((asset) => {
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      asset.asset_id.toLowerCase().includes(query) ||
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold text-neutral-900">{t("assets")}</h1>
        <button
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          onClick={() => alert("Register asset - to be implemented")}
        >
          + {t("register_asset")}
        </button>
      </div>

      {/* Filters */}
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

          {/* Lifecycle Filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setLifecycleFilter("all")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                lifecycleFilter === "all"
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              {t("all")}
            </button>
            <button
              onClick={() => setLifecycleFilter("active")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                lifecycleFilter === "active"
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              {t("lifecycle_active")}
            </button>
            <button
              onClick={() => setLifecycleFilter("warning")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                lifecycleFilter === "warning"
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              {t("lifecycle_warning")}
            </button>
            <button
              onClick={() => setLifecycleFilter("end_of_life")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                lifecycleFilter === "end_of_life"
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              {t("lifecycle_end_of_life")}
            </button>
            <button
              onClick={() => setLifecycleFilter("replaced")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                lifecycleFilter === "replaced"
                  ? "bg-primary-600 text-white"
                  : "border border-neutral-300 bg-neutral-0 text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              {t("lifecycle_replaced")}
            </button>
          </div>
        </div>
      )}

      {/* Empty State */}
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
            onClick: () => alert("Register asset - to be implemented"),
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
        /* Assets Table */
        <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-neutral-200 bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("asset_id")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("asset_category")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("site_name")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("lifecycle_status")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("asset_age")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("repair_count")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {filteredAssets.map((asset) => (
                  <tr
                    key={asset.id}
                    onClick={() => navigate(`/assets/${asset.id}`)}
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                  >
                    <td className="px-6 py-4 font-mono text-sm font-medium text-primary-600">
                      {asset.asset_id}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-neutral-900">{asset.type}</div>
                      <div className="text-xs text-neutral-500">{asset.category}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">
                      {asset.site_name || "—"}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <AssetLifecycleBadge status={asset.lifecycle_status} />
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
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">
                      {asset.repair_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
