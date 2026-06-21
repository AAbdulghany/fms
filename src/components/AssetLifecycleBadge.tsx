interface AssetLifecycleBadgeProps {
  status: "active" | "warning" | "end_of_life" | "replaced" | "retired";
}

const statusConfig: Record<string, { label: string; className: string }> = {
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
    label: "Retired",
    className: "bg-neutral-300 text-neutral-700",
  },
  retired: {
    label: "Retired",
    className: "bg-neutral-300 text-neutral-700",
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
