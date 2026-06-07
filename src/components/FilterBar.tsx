import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

export interface FilterBarCompany {
  id: string;
  legal_name: string;
}

export interface FilterBarSite {
  id: string;
  name: string;
  client_id: string;
}

interface FilterBarProps {
  onFilterChange?: (filters: FilterValues) => void;
  showStatusFilter?: boolean;
  showUrgencyFilter?: boolean;
  showDateRange?: boolean;
  showSearch?: boolean;
  showCategoryFilter?: boolean;
  showCompanyFilter?: boolean;
  showSiteFilter?: boolean;
  companies?: FilterBarCompany[];
  sites?: FilterBarSite[];
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

function filtersToSearchParams(filters: FilterValues): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.search?.trim()) params.set("search", filters.search.trim());
  if (filters.status) params.set("status", filters.status);
  if (filters.urgency) params.set("urgency", filters.urgency);
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  if (filters.clientId) params.set("client_id", filters.clientId);
  if (filters.siteId) params.set("site_id", filters.siteId);
  if (filters.assigneeUserId) params.set("assignee_user_id", filters.assigneeUserId);
  if (filters.category) params.set("category", filters.category);
  return params;
}

export function FilterBar({
  onFilterChange,
  showStatusFilter = false,
  showUrgencyFilter = false,
  showDateRange = false,
  showSearch = true,
  showCategoryFilter = false,
  showCompanyFilter = false,
  showSiteFilter = false,
  companies = [],
  sites = [],
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
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        const managedKeys = [
          "search",
          "status",
          "urgency",
          "date_from",
          "date_to",
          "client_id",
          "site_id",
          "assignee_user_id",
          "category",
        ];
        for (const key of managedKeys) next.delete(key);
        filtersToSearchParams(filters).forEach((value, key) => {
          if (value) next.set(key, value);
        });
        return next;
      },
      { replace: true }
    );
    onFilterChange?.(filters);
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
    <div className="w-full min-w-0 rounded-lg border border-neutral-200 bg-neutral-0 p-4">
      <div className="flex w-full min-w-0 flex-nowrap items-end gap-x-3 overflow-x-auto pb-0.5">
        {showSearch && (
          <div className="w-full min-w-0 max-w-[220px] shrink-0 sm:w-[min(100%,220px)]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              Search
            </label>
            <input
              type="text"
              className="w-full min-w-0 rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Search..."
              value={filters.search || ""}
              onChange={(e) => updateFilter("search", e.target.value)}
            />
          </div>
        )}

        {showStatusFilter && (
          <div className="min-w-0 w-[min(100%,10rem)] shrink-0 sm:w-40">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              {t("status")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={filters.status || ""}
              onChange={(e) => updateFilter("status", e.target.value)}
            >
              <option value="">{t("filter_all")}</option>
              {availableStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>
        )}

        {showUrgencyFilter && (
          <div className="min-w-0 w-[min(100%,10rem)] shrink-0 sm:w-40">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              {t("urgency")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={filters.urgency || ""}
              onChange={(e) => updateFilter("urgency", e.target.value)}
            >
              <option value="">{t("filter_all")}</option>
              {availableUrgencies.map((urgency) => (
                <option key={urgency} value={urgency}>
                  {t(urgency)}
                </option>
              ))}
            </select>
          </div>
        )}

        {showCompanyFilter && companies.length > 0 && (
          <div className="min-w-0 w-[min(100%,12rem)] shrink-0 sm:min-w-[11rem] sm:max-w-[14rem]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              {t("company")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={filters.clientId || ""}
              onChange={(e) => {
                const v = e.target.value;
                setFilters((prev) => ({ ...prev, clientId: v, siteId: "" }));
              }}
            >
              <option value="">{t("filter_all")}</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.legal_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {showSiteFilter && sites.length > 0 && (
          <div className="min-w-0 w-[min(100%,12rem)] shrink-0 sm:min-w-[11rem] sm:max-w-[14rem]">
            <label className="mb-1 block text-xs font-medium text-neutral-700">
              {t("site")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              value={filters.siteId || ""}
              onChange={(e) => updateFilter("siteId", e.target.value)}
            >
              <option value="">{t("filter_all")}</option>
              {sites
                .filter((s) => !filters.clientId || s.client_id === filters.clientId)
                .map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
            </select>
          </div>
        )}

        {showCategoryFilter && (
          <div className="min-w-0 w-[min(100%,10rem)] shrink-0 sm:w-40">
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
          <div className="flex min-w-0 shrink-0 flex-nowrap items-end gap-x-3">
            <div className="w-[min(100%,10.5rem)] shrink-0">
              <label className="mb-1 block text-xs font-medium text-neutral-700">
                From
              </label>
              <input
                type="date"
                className="w-full min-w-0 rounded-md border border-neutral-300 px-2 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                value={filters.dateFrom || ""}
                onChange={(e) => updateFilter("dateFrom", e.target.value)}
              />
            </div>
            <div className="w-[min(100%,10.5rem)] shrink-0">
              <label className="mb-1 block text-xs font-medium text-neutral-700">
                To
              </label>
              <input
                type="date"
                className="w-full min-w-0 rounded-md border border-neutral-300 px-2 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                value={filters.dateTo || ""}
                onChange={(e) => updateFilter("dateTo", e.target.value)}
              />
            </div>
          </div>
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
