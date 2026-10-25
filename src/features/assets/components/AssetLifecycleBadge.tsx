import { useTranslation } from "react-i18next";

interface AssetLifecycleBadgeProps {
  status: "active" | "warning" | "end_of_life" | "replaced" | "retired";
}

const statusConfig: Record<string, { labelKey: string; className: string }> = {
  active: {
    labelKey: "lifecycle_active",
    className: "bg-success-light text-success-dark",
  },
  warning: {
    labelKey: "lifecycle_warning",
    className: "bg-warning-light text-warning-dark",
  },
  end_of_life: {
    labelKey: "lifecycle_end_of_life",
    className: "bg-error-light text-error-dark",
  },
  replaced: {
    labelKey: "lifecycle_replaced",
    className: "bg-neutral-300 text-neutral-700",
  },
  retired: {
    labelKey: "lifecycle_replaced",
    className: "bg-neutral-300 text-neutral-700",
  },
};

export function AssetLifecycleBadge({ status }: AssetLifecycleBadgeProps) {
  const { t } = useTranslation();
  const config = statusConfig[status] || statusConfig.active;

  return (
    <span className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold ${config.className}`}>
      {t(config.labelKey)}
    </span>
  );
}
