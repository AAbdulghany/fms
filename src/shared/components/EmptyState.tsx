import { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex min-h-[400px] items-center justify-center rounded-lg border-2 border-dashed border-neutral-300 bg-neutral-50 p-12">
      <div className="text-center">
        {icon && (
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center text-neutral-400">
            {icon}
          </div>
        )}
        
        <h3 className="text-lg font-medium text-neutral-900">{title}</h3>
        
        {description && (
          <p className="mt-2 max-w-md text-sm text-neutral-600">{description}</p>
        )}
        
        {action && (
          <button
            type="button"
            onClick={action.onClick}
            className="mt-6 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          >
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
}
