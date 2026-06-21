import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import type { AssetLifecycleStatus, PaginatedWorkOrders, WorkOrder } from "../lib/types";
import { workOrderStatusPillClass } from "../lib/workOrderDisplay";

const OPEN_STATUSES = new Set([
  "requested",
  "created",
  "assigned",
  "in_progress",
  "on_hold",
]);

type AssetDetail = {
  id: string;
  name: string;
  next_due_at?: string | null;
  lifecycle_status: AssetLifecycleStatus;
};

type Props = {
  assetId: string | null;
};

function formatDate(dateStr: string, locale: string): string {
  try {
    return new Date(dateStr).toLocaleDateString(locale, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function AssetWorkOrderPanel({ assetId }: Props) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [assetDetail, setAssetDetail] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!assetId) {
      setWorkOrders([]);
      setAssetDetail(null);
      return;
    }
    void (async () => {
      setLoading(true);
      try {
        const [woData, assetData] = await Promise.all([
          apiFetch<PaginatedWorkOrders>(`/work-orders?asset_id=${assetId}&page_size=20`),
          apiFetch<AssetDetail>(`/assets/${assetId}`).catch(() => null),
        ]);
        setWorkOrders(woData.data.filter((wo) => OPEN_STATUSES.has(wo.status)));
        setAssetDetail(assetData);
      } catch (err) {
        console.error("Failed to load asset work orders", err);
        setWorkOrders([]);
        setAssetDetail(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [assetId]);

  if (!assetId) {
    return (
      <div
        className="rounded-lg border border-dashed border-neutral-200 bg-neutral-50 p-4 text-sm text-neutral-500"
        data-testid="asset-wo-panel-empty"
      >
        {t("select_asset_for_work_orders")}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm" data-testid="asset-wo-panel">
      <h2 className="mb-3 text-lg font-semibold text-neutral-900">
        {assetDetail?.name || t("linked_work_orders")}
      </h2>

      {loading ? (
        <div className="flex min-h-[80px] items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600" />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Scheduled Maintenance section */}
          {assetDetail?.next_due_at && (
            <div>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-neutral-700">
                <span className="inline-block h-2 w-2 rounded-full bg-primary-500" />
                {t("scheduled_maintenance")}
              </h3>
              <div className="rounded-lg border border-primary-100 bg-primary-50 px-3 py-2.5">
                <p className="text-sm font-medium text-primary-800">
                  {t("next_due")}: {formatDate(assetDetail.next_due_at, locale)}
                </p>
              </div>
            </div>
          )}

          {/* Open Work Orders section */}
          <div>
            <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-neutral-700">
              <span className="inline-block h-2 w-2 rounded-full bg-warning-main" />
              {t("open_work_orders")}
            </h3>
            {workOrders.length === 0 ? (
              <p className="text-sm text-neutral-500" data-testid="asset-wo-panel-no-results">
                {t("no_linked_work_orders")}
              </p>
            ) : (
              <ul className="space-y-2">
                {workOrders.map((wo) => (
                  <li key={wo.id}>
                    <Link
                      to={`/work-orders/${wo.id}`}
                      className="flex items-center justify-between rounded-lg border border-neutral-100 px-3 py-2 text-sm hover:bg-neutral-50"
                      data-testid={`asset-wo-link-${wo.id}`}
                    >
                      <span className="font-medium text-neutral-900">{wo.title}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${workOrderStatusPillClass(wo.status)}`}>
                        {wo.status.replace(/_/g, " ")}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
