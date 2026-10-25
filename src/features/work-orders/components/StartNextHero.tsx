import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { WorkOrder } from "@/lib/types";
import { displayWorkOrderTitle } from "@/lib/workOrderDisplay";

interface StartNextHeroProps {
  workOrder: WorkOrder | null;
  onCreate?: () => void;
  canCreate?: boolean;
}

/**
 * D FINAL · F Queue — Start next soft card, then navy Start CTA, then ghost Create.
 * Phone only (`lg:hidden`).
 */
export function StartNextHero({ workOrder, onCreate, canCreate }: StartNextHeroProps) {
  const { t, i18n } = useTranslation();

  if (!workOrder) {
    return (
      <div className="space-y-2 lg:hidden">
        <div className="rounded-xl border border-primary-200 bg-primary-50 px-3 py-3">
          <p className="text-sm font-bold text-primary-800">{t("queue_empty_title")}</p>
          <p className="mt-0.5 text-xs text-primary-700/80">{t("queue_empty_body")}</p>
        </div>
        {canCreate && onCreate ? (
          <button
            type="button"
            onClick={onCreate}
            className="flex min-h-11 w-full items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 text-sm font-semibold text-neutral-900 hover:bg-neutral-50"
          >
            {t("create_work_order")}
          </button>
        ) : null}
      </div>
    );
  }

  const line = [
    displayWorkOrderTitle(workOrder, i18n.language),
    workOrder.site_name,
  ]
    .filter(Boolean)
    .join(" · ");

  const startLabel =
    workOrder.status === "assigned" || workOrder.status === "created"
      ? t("start_work_order")
      : t("open_work_order");

  return (
    <div className="space-y-2 lg:hidden">
      <div className="rounded-xl border border-primary-200 bg-primary-50 px-3 py-3">
        <p className="text-sm font-bold text-primary-800">{t("start_next")}</p>
        <p className="mt-0.5 truncate text-xs text-neutral-500">{line}</p>
      </div>

      <Link
        to={`/work-orders/${workOrder.id}`}
        className="flex min-h-11 w-full items-center justify-center rounded-xl bg-primary-700 text-sm font-bold text-white hover:bg-primary-800"
      >
        {startLabel}
      </Link>

      {canCreate && onCreate ? (
        <button
          type="button"
          onClick={onCreate}
          className="flex min-h-11 w-full items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 text-sm font-semibold text-neutral-900 hover:bg-neutral-50"
        >
          {t("create_work_order")}
        </button>
      ) : null}
    </div>
  );
}
