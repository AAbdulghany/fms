import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate, Link } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { urgencyBadgeClass, workOrderStatusPillClass } from "../lib/workOrderDisplay";
import type { Asset, AssetLifecycleStatus, WorkOrder, PaginatedWorkOrders } from "../lib/types";
import { AssetLifecycleBadge } from "../components/AssetLifecycleBadge";
import { AssetLifecycleTimeline } from "../components/AssetLifecycleTimeline";

type AssetOutApi = {
  id: string;
  site_id: string;
  name: string;
  category: string;
  model?: string | null;
  serial?: string | null;
  installed_on?: string | null;
  warranty_until?: string | null;
  max_repair_count?: number | null;
  max_age_years?: number | null;
  current_repair_count: number;
  lifecycle_status: AssetLifecycleStatus;
  location_id?: string | null;
};

function mapToAsset(a: AssetOutApi): Asset {
  let ageYears = 0;
  if (a.installed_on) {
    const d = new Date(a.installed_on);
    ageYears = Math.max(0, (Date.now() - d.getTime()) / (365.25 * 24 * 3600 * 1000));
  }
  const maxAge = a.max_age_years ?? 5;
  return {
    id: a.id,
    asset_id: a.name || `${a.id.slice(0, 8)}…`,
    site_id: a.site_id,
    company_id: "",
    type: a.name || a.category,
    category: a.category,
    model: a.model ?? undefined,
    serial_number: a.serial ?? undefined,
    lifecycle_status: a.lifecycle_status,
    age_years: ageYears,
    repair_count: a.current_repair_count,
    installation_date: a.installed_on ?? "",
    expected_lifespan_years: maxAge,
    lifespan_percentage: a.installed_on
      ? Math.min(100, Math.round((ageYears / maxAge) * 100))
      : 0,
  };
}

export default function AssetDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"details" | "maintenance" | "work-orders">("details");

  useEffect(() => {
    void (async () => {
      try {
        const assetData = await apiFetch<AssetOutApi>(`/assets/${id}`);
        setAsset(mapToAsset(assetData));

        // Fetch work orders for this asset
        const woData = await apiFetch<PaginatedWorkOrders>(`/work-orders?asset_id=${id}&page_size=50`);
        setWorkOrders(woData.data);
      } catch (error) {
        console.error("Failed to fetch asset data", error);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="text-center text-neutral-600">
        <p>{t("error")}</p>
      </div>
    );
  }

  const maintenanceWOs = workOrders.filter((wo) => 
    wo.category === "preventive" || wo.category === "corrective"
  );

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-neutral-600">
        <Link to="/dashboard" className="hover:text-primary-600">
          {t("dashboard")}
        </Link>
        <span>›</span>
        <Link to="/assets" className="hover:text-primary-600">
          {t("assets")}
        </Link>
        <span>›</span>
        <span className="font-medium text-neutral-900">{asset.asset_id}</span>
      </nav>

      {/* Header */}
      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="font-mono text-3xl font-semibold text-neutral-900">
              {asset.type} — {asset.asset_id}
            </h1>
            <p className="mt-1 text-sm text-neutral-600">
              {asset.site_name && `${asset.site_name} • `}
              {asset.company_name}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              onClick={() => { /* edit asset – future implementation */ }}
            >
              {t("edit")}
            </button>
            <button
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              onClick={() => navigate("/work-orders")}
            >
              + {t("create_work_order")}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex flex-wrap gap-6 border-t border-neutral-100 pt-4">
          <div className="flex items-center gap-2">
            <AssetLifecycleBadge status={asset.lifecycle_status} />
          </div>
          <div className="text-sm text-neutral-600">
            <span className="font-medium text-neutral-900">{asset.age_years.toFixed(1)} years</span> age
          </div>
          <div className="text-sm text-neutral-600">
            <span className="font-medium text-neutral-900">{asset.lifespan_percentage}%</span> of lifespan used
          </div>
          {asset.last_maintenance_date && (
            <div className="text-sm text-neutral-600">
              Last maintenance:{" "}
              <span className="font-medium text-neutral-900">
                {new Date(asset.last_maintenance_date).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Lifecycle Timeline */}
      <AssetLifecycleTimeline asset={asset} />

      {/* Alert Banners */}
      {asset.lifecycle_status === "warning" && (
        <div className="rounded-lg border border-warning-main bg-warning-light p-4">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 flex-shrink-0 text-warning-dark"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-warning-dark">
                ⚠️ Warning: Asset is {asset.lifespan_percentage}% through expected lifespan.
              </p>
              <p className="mt-1 text-sm text-warning-dark">Replacement work order recommended.</p>
              <button
                className="mt-2 rounded-lg bg-warning-dark px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-warning-main"
                onClick={() => navigate("/work-orders")}
              >
                {t("create_work_order")}
              </button>
            </div>
          </div>
        </div>
      )}

      {asset.lifecycle_status === "end_of_life" && (
        <div className="rounded-lg border border-error-main bg-error-light p-4">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 flex-shrink-0 text-error-dark"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-error-dark">
                🔴 End of Life: Asset has exceeded expected lifespan.
              </p>
              {asset.replacement_wo_id ? (
                <p className="mt-1 text-sm text-error-dark">
                  Replacement work order:{" "}
                  <Link
                    to={`/work-orders/${asset.replacement_wo_id}`}
                    className="font-medium underline hover:no-underline"
                  >
                    View WO
                  </Link>
                </p>
              ) : (
                <button
                  className="mt-2 rounded-lg bg-error-dark px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-error-main"
                  onClick={() => navigate("/work-orders")}
                >
                  {t("create_work_order")}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-neutral-200">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab("details")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "details"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab("maintenance")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "maintenance"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            Maintenance History
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
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "details" && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-medium text-neutral-900">Asset Information</h2>
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-neutral-500">{t("asset_id")}</dt>
              <dd className="mt-1 font-mono text-sm text-neutral-900">{asset.asset_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-neutral-500">Type</dt>
              <dd className="mt-1 text-sm text-neutral-900">{asset.type}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-neutral-500">{t("asset_category")}</dt>
              <dd className="mt-1 text-sm text-neutral-900">{asset.category}</dd>
            </div>
            {asset.manufacturer && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("manufacturer")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">{asset.manufacturer}</dd>
              </div>
            )}
            {asset.model && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("model")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">{asset.model}</dd>
              </div>
            )}
            {asset.serial_number && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("serial_number")}</dt>
                <dd className="mt-1 font-mono text-sm text-neutral-900">{asset.serial_number}</dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-neutral-500">{t("installation_date")}</dt>
              <dd className="mt-1 text-sm text-neutral-900">
                {new Date(asset.installation_date).toLocaleDateString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-neutral-500">{t("expected_lifespan")}</dt>
              <dd className="mt-1 text-sm text-neutral-900">
                {asset.expected_lifespan_years} years
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-neutral-500">Current Age</dt>
              <dd className="mt-1 text-sm text-neutral-900">
                {asset.age_years.toFixed(1)} years
              </dd>
            </div>
            {asset.location_path && (
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-neutral-500">{t("location")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">{asset.location_path}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {activeTab === "maintenance" && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
          {maintenanceWOs.length === 0 ? (
            <div className="p-8 text-center text-neutral-600">
              <p>No maintenance history yet</p>
              <p className="mt-2 text-sm">Maintenance records will appear here as work orders are completed.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      Date
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      Type
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("description")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("status")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {maintenanceWOs.map((wo) => (
                    <tr
                      key={wo.id}
                      onClick={() => navigate(`/work-orders/${wo.id}`)}
                      className="cursor-pointer transition-colors hover:bg-neutral-50"
                    >
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">
                        {new Date(wo.opened_at).toLocaleDateString()}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">
                        {wo.category}
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-900">{wo.description}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm">
                        <span className={workOrderStatusPillClass(wo.status)}>{wo.status}</span>
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
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
          {workOrders.length === 0 ? (
            <div className="p-8 text-center text-neutral-600">
              <p>No work orders yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
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
    </div>
  );
}
