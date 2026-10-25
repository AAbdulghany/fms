import { useTranslation } from "react-i18next";
import type { WorkOrderStatus } from "@/lib/types";
import { workOrderStatusPillClass } from "@/lib/workOrderDisplay";

/** Label for transitioning *to* `target` from `current`. */
function ctaLabelKey(current: WorkOrderStatus, target: WorkOrderStatus): string {
  if (target === "in_progress" && current === "on_hold") return "wo_cta_resume";
  if (target === "in_progress") return "wo_cta_start";
  if (target === "on_hold") return "wo_cta_hold";
  if (target === "completed") return "wo_cta_complete";
  if (target === "verified") return "wo_cta_verify";
  if (target === "closed") return "wo_cta_close";
  if (target === "cancelled") return "wo_cta_cancel";
  if (target === "assigned") return "wo_cta_assign";
  if (target === "created") return "wo_cta_review";
  if (target === "requested") return "wo_cta_review";
  return target;
}

function pickPrimary(allowed: WorkOrderStatus[]): WorkOrderStatus {
  const prefer: WorkOrderStatus[] = [
    "completed",
    "in_progress",
    "verified",
    "closed",
    "assigned",
    "created",
  ];
  for (const p of prefer) {
    if (allowed.includes(p)) return p;
  }
  return allowed[0];
}

interface Props {
  status: WorkOrderStatus;
  allowedNext: WorkOrderStatus[];
  canEdit: boolean;
  reportReadyForComplete: boolean;
  onTransition: (status: WorkOrderStatus) => void;
  /** Compact card mode (Job page status box) */
  embedded?: boolean;
}

/** Primary actions — only legal next statuses; labels match the target transition. */
export function WorkOrderJobRail({
  status,
  allowedNext,
  canEdit,
  reportReadyForComplete,
  onTransition,
  embedded = false,
}: Props) {
  const { t } = useTranslation();
  const shell = embedded
    ? "space-y-3"
    : "sticky top-0 z-20 -mx-1 space-y-2 border-b border-neutral-200 bg-neutral-0/95 px-1 py-3 backdrop-blur-sm";

  if (!canEdit || allowedNext.length === 0) {
    return (
      <div className={shell}>
        <span className={workOrderStatusPillClass(status)}>{t(status) || status}</span>
      </div>
    );
  }

  const primary = pickPrimary(allowedNext);
  const secondary = allowedNext.filter((s) => s !== primary);

  return (
    <div className={shell}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={workOrderStatusPillClass(status)}>{t(status) || status}</span>
        <span className="text-xs text-neutral-500">{t("wo_job_rail_hint") || "Next step"}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="min-h-11 flex-1 rounded-lg bg-secondary-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-secondary-600 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
          disabled={primary === "completed" && !reportReadyForComplete}
          title={
            primary === "completed" && !reportReadyForComplete
              ? t("error_report_required") || "Submit the report first"
              : undefined
          }
          onClick={() => onTransition(primary)}
        >
          {t(ctaLabelKey(status, primary)) || primary.replace(/_/g, " ")}
        </button>
        {secondary.map((s) => (
          <button
            key={s}
            type="button"
            className="min-h-11 rounded-lg border border-neutral-300 bg-neutral-0 px-3 py-2.5 text-sm font-medium text-neutral-800 hover:bg-neutral-50"
            onClick={() => onTransition(s)}
          >
            {t(ctaLabelKey(status, s)) || s.replace(/_/g, " ")}
          </button>
        ))}
      </div>
    </div>
  );
}
