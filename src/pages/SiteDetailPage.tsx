import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate, Link } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { urgencyBadgeClass, workOrderStatusPillClass } from "../lib/workOrderDisplay";
import type { Site, Asset, AssetLifecycleStatus, WorkOrder, PaginatedWorkOrders } from "../lib/types";
import { EmptyState } from "../components/EmptyState";
import { AssetLifecycleBadge } from "../components/AssetLifecycleBadge";
import { AssetRegisterModal } from "../components/AssetRegisterModal";
import { SiteEditModal } from "../components/SiteEditModal";
import { SiteQRModal } from "../components/SiteQrModal";

type AssetOutApi = {
  id: string;
  site_id: string;
  name: string;
  category: string;
  lifecycle_status: AssetLifecycleStatus;
  current_repair_count: number;
  max_age_years?: number | null;
  installed_on?: string | null;
};

function mapToDisplayAsset(a: AssetOutApi): Asset {
  let ageYears = 0;
  if (a.installed_on) {
    const d = new Date(a.installed_on);
    ageYears = Math.max(0, (Date.now() - d.getTime()) / (365.25 * 24 * 3600 * 1000));
  }
  return {
    id: a.id,
    asset_id: a.name || `${a.id.slice(0, 8)}…`,
    site_id: a.site_id,
    company_id: "",
    type: a.name || a.category,
    category: a.category,
    lifecycle_status: a.lifecycle_status,
    age_years: ageYears,
    repair_count: a.current_repair_count,
    installation_date: a.installed_on ?? "",
    expected_lifespan_years: a.max_age_years ?? 5,
    lifespan_percentage: a.max_age_years && a.installed_on
      ? Math.min(100, Math.round((ageYears / a.max_age_years) * 100))
      : 50,
  };
}

export default function SiteDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [site, setSite] = useState<Site | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"assets" | "work-orders" | "locations" | "schedule">("assets");
  const [registerOpen, setRegisterOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [qrOpen, setQrOpen] = useState(false);

  const loadSite = useCallback(() => {
    if (!id) return;
    setLoading(true);
    void (async () => {
      try {
        type SiteApi = {
          id: string;
          client_id: string;
          name: string;
          timezone: string;
          status: "active" | "inactive";
          address?: string;
          city?: string;
          country?: string;
          company_name?: string;
        };
        const siteData = await apiFetch<SiteApi>(`/sites/${id}`);
        setSite({
          id: siteData.id,
          company_id: siteData.client_id,
          name: siteData.name,
          timezone: siteData.timezone,
          status: siteData.status,
          address: siteData.address ?? "",
          city: siteData.city ?? "",
          country: siteData.country ?? "",
          company_name: siteData.company_name,
        });

        const assetsData = await apiFetch<AssetOutApi[]>(`/sites/${id}/assets`);
        setAssets(assetsData.map(mapToDisplayAsset));

        const woData = await apiFetch<PaginatedWorkOrders>(`/work-orders?site_id=${id}&page_size=50`);
        setWorkOrders(woData.data);
      } catch (error) {
        console.error("Failed to fetch site data", error);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  useEffect(() => {
    loadSite();
  }, [loadSite]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!site) {
    return (
      <div className="text-center text-neutral-600">
        <p>{t("error")}</p>
      </div>
    );
  }

  const activeWorkOrders = workOrders.filter((wo) => !["closed", "cancelled"].includes(wo.status));

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-neutral-600">
        <Link to="/dashboard" className="hover:text-primary-600">
          {t("dashboard")}
        </Link>
        <span>›</span>
        {site.company_name && (
          <>
            <Link to={`/companies/${site.company_id}`} className="hover:text-primary-600">
              {site.company_name}
            </Link>
            <span>›</span>
          </>
        )}
        <span className="font-medium text-neutral-900">{site.name}</span>
      </nav>

      {/* Header */}
      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-semibold text-neutral-900">{site.name}</h1>
            {site.company_name && (
              <p className="mt-1 text-sm text-neutral-600">{site.company_name}</p>
            )}
            <p className="mt-1 flex items-center gap-1 text-sm text-neutral-600">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              {site.address}, {site.city}, {site.country}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              onClick={() => setEditOpen(true)}
            >
              {t("edit")}
            </button>
            <button
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              onClick={() => setQrOpen(true)}
            >
              {t("qr_code")}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex gap-6 border-t border-neutral-100 pt-4">
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                site.status === "active"
                  ? "bg-success-light text-success-dark"
                  : "bg-neutral-200 text-neutral-600"
              }`}
            >
              {site.status}
            </span>
          </div>
          <div className="text-sm text-neutral-600">
            <span className="font-medium text-neutral-900">{assets.length}</span> {t("assets")}
          </div>
          <div className="text-sm text-neutral-600">
            <span className="font-medium text-neutral-900">{activeWorkOrders.length}</span> {t("active_wos")}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-neutral-200">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab("assets")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "assets"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("assets")}
          </button>
          <button
            onClick={() => setActiveTab("work-orders")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "work-orders"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("work_orders")}
          </button>
          <button
            onClick={() => setActiveTab("locations")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "locations"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("locations")}
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "assets" && (
        <div className="space-y-4">
          {/* Toolbar */}
          <div className="flex items-center justify-end">
            <button
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              onClick={() => setRegisterOpen(true)}
            >
              + {t("register_asset")}
            </button>
          </div>

          {/* Assets List */}
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
              description="Register your first asset to start tracking maintenance."
              action={{
                label: `+ ${t("register_asset")}`,
                onClick: () => setRegisterOpen(true),
              }}
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
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
                  {assets.map((asset) => (
                    <tr
                      key={asset.id}
                      onClick={() => navigate(`/assets/${asset.id}`)}
                      className="cursor-pointer transition-colors hover:bg-neutral-50"
                    >
                      <td className="px-6 py-4 font-mono text-sm font-medium text-primary-600">
                        {asset.asset_id}
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-900">
                        {asset.type}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm">
                        <AssetLifecycleBadge status={asset.lifecycle_status} />
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">
                        {asset.age_years.toFixed(1)} {t("asset_age").toLowerCase()}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">
                        {asset.repair_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "work-orders" && (
        <div className="space-y-4">
          {/* Toolbar */}
          <div className="flex items-center justify-end">
            <button
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              onClick={() => navigate("/work-orders?open=create", { state: { prefillClientId: site.company_id, prefillSiteId: site.id } })}
            >
              + {t("create_work_order")}
            </button>
          </div>

          {workOrders.length === 0 ? (
            <EmptyState
              icon={
                <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              }
              title="No work orders yet"
              description="Work orders for this site will appear here."
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      ID
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("title")}
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
                  {workOrders.map((wo) => (
                    <tr
                      key={wo.id}
                      onClick={() => navigate(`/work-orders/${wo.id}`)}
                      className="cursor-pointer transition-colors hover:bg-neutral-50"
                    >
                      <td className="px-6 py-4 font-mono text-sm font-medium text-primary-600">
                        {wo.id.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-900">{wo.title}</td>
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
          )}
        </div>
      )}

      {activeTab === "locations" && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-8 text-center shadow-sm">
          <p className="text-neutral-600">Locations tab - to be implemented (hierarchical tree view)</p>
        </div>
      )}

      {site && (
        <>
          <AssetRegisterModal
            open={registerOpen}
            onClose={() => setRegisterOpen(false)}
            onCreated={loadSite}
            initialSiteId={site.id}
          />
          <SiteEditModal
            open={editOpen}
            site={site}
            onClose={() => setEditOpen(false)}
            onSaved={loadSite}
          />
          <SiteQRModal
            open={qrOpen}
            siteId={site.id}
            siteName={site.name}
            onClose={() => setQrOpen(false)}
          />
        </>
      )}
    </div>
  );
}
