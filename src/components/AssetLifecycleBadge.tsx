interface AssetLifecycleBadgeProps {
  status: "active" | "warning" | "end_of_life" | "replaced";
}

const statusConfig = {
  active: {
    label: "Active",
    className: "bg-success-light text-success-dark",
  },
  warning: {
    label: "Warning",
    className: "bg-warning-light text-warning-dark",
  },
  end_of_life: {
    label: "End of Life",
    className: "bg-error-light text-error-dark",
  },
  replaced: {
    label: "Replaced",
    className: "bg-neutral-200 text-neutral-600",
  },
};

export function AssetLifecycleBadge({ status }: AssetLifecycleBadgeProps) {
  const config = statusConfig[status] || statusConfig.active;
  
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  );
}
