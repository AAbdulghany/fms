import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import type { Company } from "../lib/types";
import { EmptyState } from "../components/EmptyState";
import { CompanyCreateModal } from "../components/CompanyCreateModal";

type ClientApi = {
  id: string;
  legal_name: string;
  code: string;
  billing_email: string | null;
  status?: string;
  sites_count?: number | null;
  active_wo_count?: number | null;
  primary_contact_email?: string | null;
  primary_contact_phone?: string | null;
};

function mapClientToCompany(c: ClientApi): Company {
  const st = c.status === "archived" ? "archived" : "active";
  return {
    id: c.id,
    name: c.legal_name,
    code: c.code,
    contact_email: c.primary_contact_email ?? c.billing_email ?? "",
    contact_phone: c.primary_contact_phone ?? undefined,
    status: st,
    sites_count: c.sites_count ?? undefined,
    active_wo_count: c.active_wo_count ?? undefined,
    created_at: new Date().toISOString(),
  };
}

export default function CompaniesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [includeArchived, setIncludeArchived] = useState(false);

  useEffect(() => {
    if (searchParams.get("create") === "1") {
      setCreateOpen(true);
      const next = new URLSearchParams(searchParams);
      next.delete("create");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const loadCompanies = (archived: boolean) => {
    setLoading(true);
    void (async () => {
      try {
        const url = archived ? "/clients?include_archived=true" : "/clients";
        const data = await apiFetch<ClientApi[]>(url);
        setCompanies(data.map(mapClientToCompany));
      } catch (error) {
        console.error("Failed to fetch companies", error);
        setCompanies([]);
      } finally {
        setLoading(false);
      }
    })();
  };

  useEffect(() => {
    loadCompanies(includeArchived);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeArchived]);

  const filteredCompanies = companies.filter((company) => {
    const query = searchQuery.toLowerCase();
    return (
      company.name.toLowerCase().includes(query) ||
      company.code.toLowerCase().includes(query) ||
      company.contact_email.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold text-neutral-900">{t("companies")}</h1>
        <button
          type="button"
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          onClick={() => setCreateOpen(true)}
        >
          + {t("add_company")}
        </button>
      </div>

      {/* Search + Include Archived */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder={`${t("search")} ${t("companies").toLowerCase()}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-neutral-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
          />
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-600 select-none">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-neutral-300 text-primary-600"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
          />
          {t("include_archived")}
        </label>
      </div>

      {/* Empty State */}
      {companies.length === 0 ? (
        <EmptyState
          icon={
            <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          }
          title={t("no_companies")}
          description="Add your first client company to start managing their sites and work orders."
          action={{
            label: `+ ${t("add_company")}`,
            onClick: () => setCreateOpen(true),
          }}
        />
      ) : filteredCompanies.length === 0 ? (
        <EmptyState
          icon={
            <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          }
          title={t("no_results")}
          description="Try adjusting your search criteria."
          action={{
            label: t("clear_filters"),
            onClick: () => setSearchQuery(""),
          }}
        />
      ) : (
        /* Table View (Desktop) / Card View (Mobile) */
        <>
          {/* Desktop Table */}
          <div className="hidden overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm md:block">
            <table className="w-full">
              <thead className="border-b border-neutral-200 bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("company_name")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("contact")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("sites_count")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("active_wos")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("status")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {filteredCompanies.map((company) => (
                  <tr
                    key={company.id}
                    onClick={() => navigate(`/companies/${company.id}`)}
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-primary-600">{company.name}</div>
                      <div className="text-xs text-neutral-500">{company.code}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-neutral-900">{company.contact_email}</div>
                      {company.contact_phone && (
                        <div className="text-xs text-neutral-500">{company.contact_phone}</div>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">
                      {company.sites_count ?? 0}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span
                        className={`font-medium ${
                          (company.active_wo_count ?? 0) > 10
                            ? "text-error-main"
                            : "text-neutral-900"
                        }`}
                      >
                        {company.active_wo_count ?? 0}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          company.status === "active"
                            ? "bg-success-light text-success-dark"
                            : company.status === "inactive"
                            ? "bg-neutral-200 text-neutral-600"
                            : "bg-warning-light text-warning-dark"
                        }`}
                      >
                        {company.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="grid gap-4 md:hidden">
            {filteredCompanies.map((company) => (
              <div
                key={company.id}
                onClick={() => navigate(`/companies/${company.id}`)}
                className="cursor-pointer rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm transition-colors hover:border-primary-300"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="text-base font-medium text-primary-600">{company.name}</div>
                    <div className="text-sm text-neutral-600">{company.contact_email}</div>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      company.status === "active"
                        ? "bg-success-light text-success-dark"
                        : "bg-neutral-200 text-neutral-600"
                    }`}
                  >
                    {company.status}
                  </span>
                </div>
                <div className="mt-3 flex gap-4 text-sm text-neutral-600">
                  <span>{company.sites_count ?? 0} {t("sites_count")}</span>
                  <span>•</span>
                  <span>{company.active_wo_count ?? 0} {t("active_wos")}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <CompanyCreateModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(companyId) => {
          loadCompanies(includeArchived);
          if (companyId) navigate(`/companies/${companyId}`);
        }}
      />
    </div>
  );
}
