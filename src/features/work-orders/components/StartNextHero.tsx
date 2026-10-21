import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { WorkOrder } from "@/lib/types";
import { urgencyBadgeClass, workOrderStatusPillClass } from "@/lib/workOrderDisplay";

interface StartNextHeroProps {
  workOrder: WorkOrder | null;
  onCreate?: () => void;
  canCreate?: boolean;
}

/** Concept D — Queue hero: next actionable WO + create CTA. */
export function StartNextHero({ workOrder, onCreate, canCreate }: StartNextHeroProps) {
  const { t } = useTranslation();

  if (!workOrder) {
    return (
      <div className="rounded-xl border border-primary-200 bg-primary-50 p-4 lg:hidden">
        <p className="text-sm font-semibold text-primary-800">{t("queue_empty_title")}</p>
        <p className="mt-1 text-xs text-primary-700/80">{t("queue_empty_body")}</p>
        {canCreate && onCreate && (
          <button
            type="button"
            onClick={onCreate}
            className="mt-3 w-full rounded-lg bg-primary-600 px-4 py-3 text-sm font-semibold text-white hover:bg-primary-700"
          >
            {t("create_work_order")}
          </button>
        )}
      </div>
    );
  }

  const subtitle = [workOrder.asset_name, workOrder.site_name].filter(Boolean).join(" · ");

  return (
    <div className="space-y-3 lg:hidden">
      <div className="rounded-xl border border-primary-300 bg-primary-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-primary-700">
          {t("start_next")}
        </p>
        <p className="mt-1 text-lg font-semibold text-neutral-900">
          {workOrder.title || workOrder.id.slice(0, 8)}
        </p>
        {subtitle ? <p className="mt-0.5 text-sm text-neutral-600">{subtitle}</p> : null}
        <div className="mt-2 flex flex-wrap gap-2">
          <span className={workOrderStatusPillClass(workOrder.status)}>{workOrder.status}</span>
          {workOrder.urgency ? (
            <span className={urgencyBadgeClass(workOrder.urgency)}>{workOrder.urgency}</span>
          ) : null}
        </div>
        <Link
          to={`/work-orders/${workOrder.id}`}
          className="mt-3 flex w-full items-center justify-center rounded-lg bg-primary-600 px-4 py-3 text-sm font-semibold text-white hover:bg-primary-700"
        >
          {workOrder.status === "assigned" || workOrder.status === "created"
            ? t("start_work_order")
            : t("open_work_order")}
        </Link>
      </div>
      {canCreate && onCreate && (
        <button
          type="button"
          onClick={onCreate}
          className="w-full rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-3 text-sm font-semibold text-neutral-900 hover:bg-neutral-100"
        >
          {t("create_work_order")}
        </button>
      )}
    </div>
  );
}
