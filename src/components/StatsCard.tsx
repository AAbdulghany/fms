import { ReactNode } from "react";

interface StatsCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down";
  subtitle?: string;
  icon?: ReactNode;
  onClick?: () => void;
}

export function StatsCard({ 
  label, 
  value, 
  change, 
  trend, 
  subtitle,
  icon,
  onClick 
}: StatsCardProps) {
  const isClickable = onClick !== undefined;

  return (
    <div
      className={`rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm transition-colors ${
        isClickable ? "cursor-pointer hover:border-primary-300" : ""
      }`}
      onClick={onClick}
      role={isClickable ? "button" : undefined}
      tabIndex={isClickable ? 0 : undefined}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-neutral-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-primary-600">{value}</p>
          
          {change && (
            <p
              className={`mt-1 text-xs font-medium ${
                trend === "up" ? "text-success-main" : trend === "down" ? "text-error-main" : "text-neutral-600"
              }`}
            >
              {trend === "up" && "↑ "}
              {trend === "down" && "↓ "}
              {change}
            </p>
          )}
          
          {subtitle && (
            <p className="mt-1 text-xs text-neutral-600">{subtitle}</p>
          )}
        </div>
        
        {icon && (
          <div className="flex-shrink-0 text-neutral-400">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
