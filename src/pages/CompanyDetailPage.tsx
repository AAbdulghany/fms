import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate, Link } from "react-router-dom";
import { apiFetch } from "../lib/api";
import type { Company, Site } from "../lib/types";
import { EmptyState } from "../components/EmptyState";
import { CompanyEditModal } from "../components/CompanyEditModal";
import { SiteProvisionModal } from "../components/SiteProvisionModal";
import { ProvisionCredentialsModal } from "../components/ProvisionCredentialsModal";

type ClientApi = {
  id: string;
  legal_name: string;
  code: string;
  billing_email: string | null;
  status: string;
};

export default function CompanyDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [company, setCompany] = useState<Company | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"sites" | "work-orders" | "invoices" | "settings">("sites");
  const [searchQuery, setSearchQuery] = useState("");
  const [editOpen, setEditOpen] = useState(false);
  const [addSiteOpen, setAddSiteOpen] = useState(false);
  const [siteCreds, setSiteCreds] = useState<{ username: string; email: string; initialPassword: string } | null>(null);

  const load = useCallback(() => {
    if (!id) return;
    void (async () => {
      try {
        const c = await apiFetch<ClientApi>(`/clients/${id}`);
        const st = c.status === "archived" ? "archived" : "active";
        setCompany({
          id: c.id,
          name: c.legal_name,
          code: c.code,
          contact_email: c.billing_email ?? "",
          status: st as Company["status"],
          created_at: new Date().toISOString(),
        });

        type SiteApi = {
          id: string;
          client_id: string;
          name: string;
          timezone: string;
          status: string;
        };
        const sitesData = await apiFetch<SiteApi[]>(`/sites?client_id=${id}`);
        setSites(
          sitesData.map((s) => ({
            id: s.id,
            company_id: s.client_id,
            name: s.name,
            address: "",
            city: "",
            country: "",
            timezone: s.timezone,
            status: s.status === "active" ? "active" : "inactive",
          }))
        );
      } catch (error) {
        console.error("Failed to fetch company data", error);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  async function confirmArchive() {
    if (!id || !company) return;
    if (!window.confirm(t("archive_company_confirm"))) return;
    try {
      await apiFetch(`/clients/${id}/archive`, { method: "POST" });
      navigate("/companies");
    } catch (e) {
      console.error(e);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!company || !id) {
    return (
      <div className="text-center text-neutral-600">
        <p>{t("error")}</p>
      </div>
    );
  }

  const filteredSites = sites.filter((site) =>
    site.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <ProvisionCredentialsModal
        open={!!siteCreds}
        title={t("site_created_credentials")}
        username={siteCreds?.username ?? ""}
        email={siteCreds?.email ?? ""}
        initialPassword={siteCreds?.initialPassword ?? ""}
        onClose={() => setSiteCreds(null)}
      />

      <CompanyEditModal
        open={editOpen}
        companyId={id}
        initialLegalName={company.name}
        initialCode={company.code}
        onClose={() => setEditOpen(false)}
        onSaved={load}
      />

      <SiteProvisionModal
        open={addSiteOpen}
        clientId={id}
        onClose={() => setAddSiteOpen(false)}
        onProvisioned={(c) => {
          setSiteCreds(c);
          load();
        }}
      />

      <nav className="flex items-center gap-2 text-sm text-neutral-600">
        <Link to="/dashboard" className="hover:text-primary-600">
          {t("dashboard")}
        </Link>
        <span>›</span>
        <Link to="/companies" className="hover:text-primary-600">
          {t("companies")}
        </Link>
        <span>›</span>
        <span className="font-medium text-neutral-900">{company.name}</span>
      </nav>

      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-semibold text-neutral-900">{company.name}</h1>
            <p className="mt-1 font-mono text-xs text-neutral-500">
              {t("company_id_label")}: {company.id}
            </p>
            <p className="mt-1 font-mono text-sm text-neutral-600">
              {t("company_code")}: {company.code}
            </p>
            {company.contact_email ? (
              <p className="mt-1 text-sm text-neutral-600">{company.contact_email}</p>
            ) : null}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50"
              onClick={() => setEditOpen(true)}
            >
              {t("edit")}
            </button>
            <button
              type="button"
              className="rounded-lg border border-neutral-300 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50 disabled:opacity-50"
              disabled={company.status === "archived"}
              onClick={() => void confirmArchive()}
            >
              {t("archive")}
            </button>
          </div>
        </div>

        <div className="mt-4 flex gap-6 border-t border-neutral-100 pt-4">
          <div className="flex items-center gap-2">
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
          <div className="text-sm text-neutral-600">
            <span className="font-medium text-neutral-900">{company.sites_count ?? sites.length}</span> {t("sites_count")}
          </div>
          <div className="text-sm text-neutral-600">
            <span className="font-medium text-neutral-900">{company.active_wo_count ?? 0}</span> {t("active_wos")}
          </div>
        </div>
      </div>

      <div className="border-b border-neutral-200">
        <nav className="flex gap-6">
          <button
            type="button"
            onClick={() => setActiveTab("sites")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "sites"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("sites_count")}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("work-orders")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "work-orders"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("work_orders")}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("invoices")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "invoices"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("invoices")}
          </button>
        </nav>
      </div>

      {activeTab === "sites" && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder={`${t("search")} ${t("sites_count").toLowerCase()}...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-neutral-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
              />
            </div>
            <button
              type="button"
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
              disabled={company.status === "archived"}
              onClick={() => setAddSiteOpen(true)}
            >
              + {t("add_site")}
            </button>
          </div>

          {sites.length === 0 ? (
            <EmptyState
              icon={
                <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              }
              title={t("no_sites_for_company")}
              description={t("site_empty_hint")}
              action={{
                label: `+ ${t("add_site")}`,
                onClick: () => setAddSiteOpen(true),
              }}
            />
          ) : filteredSites.length === 0 ? (
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
            <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("site_name")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("site_timezone")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("assets")}
                    </th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("active_wos")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {filteredSites.map((site) => (
                    <tr
                      key={site.id}
                      onClick={() => navigate(`/sites/${site.id}`)}
                      className="cursor-pointer transition-colors hover:bg-neutral-50"
                    >
                      <td className="px-6 py-4 text-sm font-medium text-primary-600">{site.name}</td>
                      <td className="px-6 py-4 text-sm text-neutral-900">{site.timezone}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">{site.asset_count ?? 0}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-neutral-900">{site.active_wo_count ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "work-orders" && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-8 text-center shadow-sm">
          <p className="text-neutral-600">Work Orders tab - to be implemented</p>
        </div>
      )}

      {activeTab === "invoices" && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-8 text-center shadow-sm">
          <p className="text-neutral-600">Invoices tab - to be implemented</p>
        </div>
      )}
    </div>
  );
}
