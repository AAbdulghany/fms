import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface FilterBarProps {
  onFilterChange?: (filters: FilterValues) => void;
  showStatusFilter?: boolean;
  showUrgencyFilter?: boolean;
  showDateRange?: boolean;
  showSearch?: boolean;
  showCategoryFilter?: boolean;
  availableStatuses?: string[];
  availableUrgencies?: string[];
}

export interface FilterValues {
  status?: string;
  urgency?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
  clientId?: string;
  siteId?: string;
  assigneeUserId?: string;
  category?: string;
}

export function FilterBar({
  onFilterChange,
  showStatusFilter = false,
  showUrgencyFilter = false,
  showDateRange = false,
  showSearch = true,
  showCategoryFilter = false,
  availableStatuses = ["created", "assigned", "in_progress", "completed", "verified", "closed", "cancelled"],
  availableUrgencies = ["normal", "urgent", "emergency"],
}: FilterBarProps) {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [filters, setFilters] = useState<FilterValues>({
    status: searchParams.get("status") || "",
    urgency: searchParams.get("urgency") || "",
    dateFrom: searchParams.get("date_from") || "",
    dateTo: searchParams.get("date_to") || "",
    search: searchParams.get("search") || "",
    clientId: searchParams.get("client_id") || "",
    siteId: searchParams.get("site_id") || "",
    assigneeUserId: searchParams.get("assignee_user_id") || "",
    category: searchParams.get("category") || "",
  });

  useEffect(() => {
    // Update URL params whenever filters change
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });
    setSearchParams(params, { replace: true });
    
    if (onFilterChange) {
      onFilterChange(filters);
    }
  }, [filters, onFilterChange, setSearchParams]);

  const updateFilter = (key: keyof FilterValues, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      status: "",
      urgency: "",
      dateFrom: "",
      dateTo: "",
      search: "",
      clientId: "",
      siteId: "",
      assigneeUserId: "",
      category: "",
    });
  };

  const hasActiveFilters = Object.values(filters).some((val) => val !== "");

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4">
      <div className="flex flex-wrap items-end gap-3">
        {showSearch && (
          <div className="flex-1 min-w-[200px]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              Search
            </label>
            <input
              type="text"
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Search..."
              value={filters.search || ""}
              onChange={(e) => updateFilter("search", e.target.value)}
            />
          </div>
        )}

        {showStatusFilter && (
          <div className="min-w-[150px]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              {t("status")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={filters.status || ""}
              onChange={(e) => updateFilter("status", e.target.value)}
            >
              <option value="">All statuses</option>
              {availableStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>
        )}

        {showUrgencyFilter && (
          <div className="min-w-[150px]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              {t("urgency")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={filters.urgency || ""}
              onChange={(e) => updateFilter("urgency", e.target.value)}
            >
              <option value="">All urgencies</option>
              {availableUrgencies.map((urgency) => (
                <option key={urgency} value={urgency}>
                  {t(urgency)}
                </option>
              ))}
            </select>
          </div>
        )}

        {showCategoryFilter && (
          <div className="min-w-[150px]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              Category
            </label>
            <input
              type="text"
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Category..."
              value={filters.category || ""}
              onChange={(e) => updateFilter("category", e.target.value)}
            />
          </div>
        )}

        {showDateRange && (
          <>
            <div className="min-w-[150px]">
              <label className="mb-1 block text-xs font-medium text-neutral-700">
                From
              </label>
              <input
                type="date"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                value={filters.dateFrom || ""}
                onChange={(e) => updateFilter("dateFrom", e.target.value)}
              />
            </div>
            <div className="min-w-[150px]">
              <label className="mb-1 block text-xs font-medium text-neutral-700">
                To
              </label>
              <input
                type="date"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                value={filters.dateTo || ""}
                onChange={(e) => updateFilter("dateTo", e.target.value)}
              />
            </div>
          </>
        )}

        {hasActiveFilters && (
          <button
            type="button"
            className="rounded-md border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
            onClick={clearFilters}
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
