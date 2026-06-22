import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate, Link } from "react-router-dom";
import { apiFetch } from "@/lib/api";
import { urgencyBadgeClass, workOrderStatusPillClass } from "@/lib/workOrderDisplay";
import type { Asset, AssetLifecycleStatus, WorkOrder, PaginatedWorkOrders } from "@/lib/types";
import { AssetLifecycleBadge } from "@/components/AssetLifecycleBadge";
import { AssetLifecycleTimeline } from "@/components/AssetLifecycleTimeline";
import { AssetEditModal } from "@/components/AssetEditModal";

type AssetOutApi = {
  id: string;
  site_id: string;
  site_name?: string | null;
  company_name?: string | null;
  name: string;
  category: string;
  label_code?: string | null;
  model?: string | null;
  serial?: string | null;
  manufacturer?: string | null;
  floor?: string | null;
  room?: string | null;
  smart_labels?: string[] | null;
  criticality?: string | null;
  installed_on?: string | null;
  warranty_until?: string | null;
  last_maintenance_date?: string | null;
  max_repair_count?: number | null;
  max_age_years?: number | null;
  current_repair_count: number;
  lifecycle_status: AssetLifecycleStatus;
  location_id?: string | null;
  expected_eol_date?: string | null;
  is_spare?: boolean | null;
  metadata_json?: Record<string, unknown> | null;
};

function computeEolDate(installedOn: string | null | undefined, maxAgeYears: number | null | undefined): string | undefined {
  if (!installedOn || !maxAgeYears) return undefined;
  const d = new Date(installedOn);
  d.setFullYear(d.getFullYear() + maxAgeYears);
  return d.toISOString().slice(0, 10);
}

function mapToAsset(a: AssetOutApi): Asset {
  let ageYears = 0;
  if (a.installed_on) {
    const d = new Date(a.installed_on);
    ageYears = Math.max(0, (Date.now() - d.getTime()) / (365.25 * 24 * 3600 * 1000));
  }
  const maxAge = a.max_age_years ?? 5;
  const photoUrl =
    typeof a.metadata_json?.photo_url === "string"
      ? a.metadata_json.photo_url
      : typeof a.metadata_json?.image_url === "string"
        ? a.metadata_json.image_url
        : undefined;
  return {
    id: a.id,
    asset_id: a.label_code || a.name || `${a.id.slice(0, 8)}…`,
    name: a.name,
    site_id: a.site_id,
    site_name: a.site_name ?? undefined,
    company_id: "",
    company_name: a.company_name ?? undefined,
    type: a.category,
    category: a.category,
    manufacturer: a.manufacturer ?? undefined,
    model: a.model ?? undefined,
    serial_number: a.serial ?? undefined,
    floor: a.floor ?? undefined,
    room: a.room ?? undefined,
    smart_labels: a.smart_labels ?? undefined,
    criticality: (a.criticality ?? undefined) as Asset["criticality"],
    warranty_until: a.warranty_until ?? undefined,
    last_maintenance_date: a.last_maintenance_date ?? undefined,
    lifecycle_status: a.lifecycle_status,
    age_years: ageYears,
    repair_count: a.current_repair_count,
    installation_date: a.installed_on ?? "",
    expected_lifespan_years: maxAge,
    lifespan_percentage: a.installed_on
      ? Math.min(100, Math.round((ageYears / maxAge) * 100))
      : 0,
    expected_eol_date: a.expected_eol_date ?? computeEolDate(a.installed_on, a.max_age_years),
    is_spare: a.is_spare ?? false,
    photo_url: photoUrl,
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
  const [editOpen, setEditOpen] = useState(false);
  const [retireConfirm, setRetireConfirm] = useState(false);
  const [retiring, setRetiring] = useState(false);

  const loadAsset = () => {
    void (async () => {
      try {
        const assetData = await apiFetch<AssetOutApi>(`/assets/${id}`);
        setAsset(mapToAsset(assetData));
        const woData = await apiFetch<PaginatedWorkOrders>(`/work-orders?asset_id=${id}&page_size=50`);
        setWorkOrders(woData.data);
      } catch (error) {
        console.error("Failed to fetch asset data", error);
      } finally {
        setLoading(false);
      }
    })();
  };

  useEffect(() => {
    loadAsset();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleRetire() {
    if (!id) return;
    setRetiring(true);
    try {
      await apiFetch(`/assets/${id}/retire`, { method: "POST" });
      setRetireConfirm(false);
      loadAsset();
    } catch (err) {
      console.error("Retire failed", err);
    } finally {
      setRetiring(false);
    }
  }

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

  const COMPLETED_STATUSES = new Set(["completed", "verified", "closed"]);
  const maintenanceWOs = workOrders.filter((wo) => COMPLETED_STATUSES.has(wo.status));

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
        <span className="font-medium text-neutral-900">{asset.name || asset.asset_id}</span>
      </nav>

      {/* Header */}
      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-semibold text-neutral-900">
              {asset.name || asset.asset_id}
            </h1>
            <p className="mt-1 text-sm text-neutral-500">
              {[asset.company_name, asset.site_name, asset.category]
                .filter(Boolean)
                .join(" • ")}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              onClick={() => setEditOpen(true)}
            >
              {t("edit_asset")}
            </button>
            {asset.lifecycle_status !== "retired" && asset.lifecycle_status !== "replaced" && (
              <button
                className="rounded-lg border border-error-main bg-neutral-0 px-4 py-2 text-sm font-medium text-error-dark transition-colors hover:bg-error-light"
                onClick={() => setRetireConfirm(true)}
              >
                {t("retire_out_of_service") || "Mark out of service"}
              </button>
            )}
            {(asset.lifecycle_status === "retired" || asset.lifecycle_status === "replaced") && (
              <span className="inline-flex items-center rounded-lg border border-neutral-300 bg-neutral-100 px-3 py-2 text-sm font-medium text-neutral-500">
                {t("lifecycle_out_of_service") || "Out of service"}
              </span>
            )}
            <button
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              onClick={() => navigate(`/work-orders?open=create&asset_id=${id}`)}
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
                onClick={() => navigate(`/work-orders?open=create&asset_id=${id}`)}
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
                  onClick={() => navigate(`/work-orders?open=create&asset_id=${id}`)}
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
          {asset.photo_url && (
            <div className="mb-6">
              <img
                src={asset.photo_url}
                alt={asset.name || t("asset")}
                className="max-h-64 w-full rounded-lg object-contain border border-neutral-100 bg-neutral-50"
              />
            </div>
          )}
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
            {asset.floor && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("floor")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">{asset.floor}</dd>
              </div>
            )}
            {asset.room && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("room")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">{asset.room}</dd>
              </div>
            )}
            {asset.criticality && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("criticality")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">{t(`criticality_${asset.criticality}`) || asset.criticality}</dd>
              </div>
            )}
            {asset.warranty_until && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("warranty_until")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">
                  {new Date(asset.warranty_until).toLocaleDateString()}
                </dd>
              </div>
            )}
            {asset.last_maintenance_date && (
              <div>
                <dt className="text-sm font-medium text-neutral-500">{t("last_maintenance_date")}</dt>
                <dd className="mt-1 text-sm text-neutral-900">
                  {new Date(asset.last_maintenance_date).toLocaleDateString()}
                </dd>
              </div>
            )}
            {asset.smart_labels && asset.smart_labels.length > 0 && (
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-neutral-500">{t("smart_labels")}</dt>
                <dd className="mt-1 flex flex-wrap gap-1">
                  {asset.smart_labels.map((label) => (
                    <span
                      key={label}
                      className="rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-800"
                    >
                      {label}
                    </span>
                  ))}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-neutral-500">{t("installation_date")}</dt>
              <dd className="mt-1 text-sm text-neutral-900">
                {asset.installation_date ? new Date(asset.installation_date).toLocaleDateString() : "—"}
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
          {/* Shows completed/verified/closed WOs for this asset only — filtered client-side until NT-P5-A01 backend is live */}
          {maintenanceWOs.length === 0 ? (
            <div className="p-8 text-center text-neutral-600">
              <p>{t("no_maintenance_history")}</p>
              <p className="mt-2 text-sm">{t("no_maintenance_history_hint")}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("title")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("date")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("status")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("assigned_to")}
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
                      <td className="px-6 py-4 text-sm font-medium text-neutral-900">{wo.title}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-600">
                        {new Date(wo.opened_at).toLocaleDateString()}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm">
                        <span className={workOrderStatusPillClass(wo.status)}>
                          {t(wo.status) || wo.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-700">
                        {wo.assignee?.full_name || t("not_assigned")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Edit Modal */}
      {id && (
        <AssetEditModal
          open={editOpen}
          assetId={id}
          onClose={() => setEditOpen(false)}
          onSaved={() => { setEditOpen(false); loadAsset(); }}
        />
      )}

      {/* Retire Confirm Dialog */}
      {retireConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl bg-neutral-0 p-6 shadow-xl">
            <h3 className="mb-2 text-lg font-semibold text-neutral-900">
              {t("retire_out_of_service") || "Mark out of service"}
            </h3>
            <p className="mb-6 text-sm text-neutral-600">
              {t("retire_out_of_service_confirm") ||
                "This asset will be marked as retired / out of service. No further work orders can be assigned to it. This action cannot be undone."}
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="rounded-md px-4 py-2 text-sm hover:bg-neutral-100"
                onClick={() => setRetireConfirm(false)}
                disabled={retiring}
              >
                {t("cancel")}
              </button>
              <button
                className="rounded-md bg-error-dark px-4 py-2 text-sm font-medium text-white hover:bg-error-main disabled:opacity-50"
                onClick={() => void handleRetire()}
                disabled={retiring}
              >
                {retiring ? t("loading") : t("retire_out_of_service") || "Mark out of service"}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === "work-orders" && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
          <div className="flex items-center justify-between border-b border-neutral-100 px-6 py-3">
            <span className="text-sm font-medium text-neutral-700">{t("work_orders")}</span>
            <button
              type="button"
              className="rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              onClick={() => navigate(`/work-orders?open=create&asset_id=${id}`)}
            >
              + {t("create_work_order")}
            </button>
          </div>
          {workOrders.length === 0 ? (
            <div className="p-8 text-center text-neutral-600">
              <p>{t("no_work_orders")}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("title")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("status")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("urgency")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("assigned_to")}
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
                      <td className="px-6 py-4 text-sm font-medium text-neutral-900">{wo.title}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm">
                        <span className={workOrderStatusPillClass(wo.status)}>
                          {t(wo.status) || wo.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm">
                        <span className={urgencyBadgeClass(wo.urgency)}>{t(wo.urgency)}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-700">
                        {wo.assignee?.full_name || t("not_assigned")}
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
