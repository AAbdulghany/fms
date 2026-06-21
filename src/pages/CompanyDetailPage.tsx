import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate, Link } from "react-router-dom";
import { apiFetch } from "../lib/api";
import type { Company, Site, WorkOrder, PaginatedWorkOrders, Invoice } from "../lib/types";
import { urgencyBadgeClass, workOrderStatusPillClass } from "../lib/workOrderDisplay";
import { formatMoneyAmount } from "../lib/formatCurrency";
import { EmptyState } from "../components/EmptyState";
import { CompanyEditModal } from "../components/CompanyEditModal";
import { SiteProvisionModal } from "../components/SiteProvisionModal";
import { SiteAssignManagerModal } from "../components/SiteAssignManagerModal";

type ClientApi = {
  id: string;
  legal_name: string;
  code: string;
  billing_email: string | null;
  status: string;
  primary_contact_email?: string | null;
  primary_contact_phone?: string | null;
  admin_user_id?: string | null;
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
  const [siteModal, setSiteModal] = useState<"add-only" | "provision" | null>(null);
  const [assignManagerSite, setAssignManagerSite] = useState<Site | null>(null);
  // Settings tab state
  const [settingsPhone, setSettingsPhone] = useState("");
  const [settingsEmail, setSettingsEmail] = useState("");
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [settingsSaved, setSettingsSaved] = useState(false);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [woTotal, setWoTotal] = useState(0);
  const [woPage, setWoPage] = useState(1);
  const [woLoading, setWoLoading] = useState(false);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [invLoading, setInvLoading] = useState(false);

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
          contact_email: c.primary_contact_email ?? c.billing_email ?? "",
          contact_phone: c.primary_contact_phone ?? undefined,
          status: st as Company["status"],
          created_at: new Date().toISOString(),
        });
        setSettingsEmail(c.primary_contact_email ?? c.billing_email ?? "");
        setSettingsPhone(c.primary_contact_phone ?? "");

        type SiteApi = {
          id: string;
          client_id: string;
          name: string;
          timezone: string;
          status: string;
          city?: string;
          country?: string;
          address?: string;
          asset_count?: number;
          active_wo_count?: number;
        };
        const sitesData = await apiFetch<SiteApi[]>(`/sites?client_id=${id}`);
        setSites(
          sitesData.map((s) => ({
            id: s.id,
            company_id: s.client_id,
            name: s.name,
            address: s.address ?? "",
            city: s.city ?? "",
            country: s.country ?? "",
            timezone: s.timezone,
            status: s.status === "active" ? "active" : "inactive",
            asset_count: s.asset_count,
            active_wo_count: s.active_wo_count,
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

  const loadWorkOrders = useCallback((page: number) => {
    if (!id) return;
    setWoLoading(true);
    void (async () => {
      try {
        const res = await apiFetch<PaginatedWorkOrders>(
          `/work-orders?client_id=${id}&page=${page}&page_size=20`
        );
        setWorkOrders(res.data);
        setWoTotal(res.meta.total);
        setWoPage(page);
      } catch (e) {
        console.error("Failed to fetch work orders", e);
      } finally {
        setWoLoading(false);
      }
    })();
  }, [id]);

  const loadInvoices = useCallback(() => {
    if (!id) return;
    setInvLoading(true);
    void (async () => {
      try {
        const res = await apiFetch<Invoice[]>(`/invoices?client_id=${id}`);
        setInvoices(res);
      } catch (e) {
        console.error("Failed to fetch invoices", e);
      } finally {
        setInvLoading(false);
      }
    })();
  }, [id]);

  useEffect(() => {
    if (activeTab === "work-orders" && workOrders.length === 0 && !woLoading) {
      loadWorkOrders(1);
    }
    if (activeTab === "invoices" && invoices.length === 0 && !invLoading) {
      loadInvoices();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

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

  const siteDefaults = sites.length > 0
    ? {
        city: sites[0].city ?? "",
        country: sites[0].country ?? "",
        timezone: sites[0].timezone ?? "",
      }
    : { city: "", country: "", timezone: "" };

  return (
    <div className="space-y-6">
      <CompanyEditModal
        open={editOpen}
        companyId={id}
        initialLegalName={company.name}
        initialCode={company.code}
        onClose={() => setEditOpen(false)}
        onSaved={load}
      />

      <SiteProvisionModal
        open={siteModal !== null}
        clientId={id}
        mode={siteModal === "provision" ? "provision" : "add-only"}
        defaultCity={siteDefaults.city}
        defaultCountry={siteDefaults.country}
        defaultTimezone={siteDefaults.timezone}
        onClose={() => setSiteModal(null)}
        onAdded={() => load()}
      />

      <SiteAssignManagerModal
        open={assignManagerSite !== null}
        siteId={assignManagerSite?.id ?? ""}
        siteName={assignManagerSite?.name ?? ""}
        onClose={() => setAssignManagerSite(null)}
        onAssigned={() => {
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
          <button
            type="button"
            onClick={() => setActiveTab("settings")}
            className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "settings"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-neutral-600 hover:text-neutral-900"
            }`}
          >
            {t("settings")}
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
              className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50 disabled:opacity-50"
              disabled={company.status === "archived"}
              onClick={() => setSiteModal("add-only")}
            >
              + {t("add_site")}
            </button>
            <button
              type="button"
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
              disabled={company.status === "archived"}
              onClick={() => setSiteModal("provision")}
            >
              + {t("add_site_manager_title")}
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
                onClick: () => setSiteModal("add-only"),
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
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                      {t("actions")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {filteredSites.map((site) => (
                    <tr
                      key={site.id}
                      className="transition-colors hover:bg-neutral-50"
                    >
                      <td
                        className="cursor-pointer px-6 py-4 text-sm font-medium text-primary-600"
                        onClick={() => navigate(`/sites/${site.id}`)}
                      >
                        {site.name}
                      </td>
                      <td
                        className="cursor-pointer px-6 py-4 text-sm text-neutral-900"
                        onClick={() => navigate(`/sites/${site.id}`)}
                      >
                        {site.timezone}
                      </td>
                      <td
                        className="cursor-pointer whitespace-nowrap px-6 py-4 text-sm text-neutral-900"
                        onClick={() => navigate(`/sites/${site.id}`)}
                      >
                        {site.asset_count ?? 0}
                      </td>
                      <td
                        className="cursor-pointer whitespace-nowrap px-6 py-4 text-sm text-neutral-900"
                        onClick={() => navigate(`/sites/${site.id}`)}
                      >
                        {site.active_wo_count ?? 0}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm">
                        <button
                          type="button"
                          className="rounded-md border border-neutral-300 px-3 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-50 disabled:opacity-40"
                          disabled={company.status === "archived"}
                          onClick={(e) => { e.stopPropagation(); setAssignManagerSite(site); }}
                        >
                          {t("assign_manager")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "work-orders" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-neutral-600">
              {woTotal} {t("work_orders")}
            </p>
            <button
              type="button"
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
              onClick={() => navigate("/work-orders?open=create", { state: { prefillClientId: id } })}
            >
              + {t("create_work_order")}
            </button>
          </div>
          {woLoading ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : workOrders.length === 0 ? (
            <EmptyState
              icon={
                <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              }
              title={t("no_results")}
              description="No work orders for this company yet."
            />
          ) : (
            <>
              <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
                <table className="w-full">
                  <thead className="border-b border-neutral-200 bg-neutral-50">
                    <tr>
                      <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">{t("title")}</th>
                      <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">{t("site")}</th>
                      <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">{t("status")}</th>
                      <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">{t("urgency")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-200">
                    {workOrders.map((wo) => (
                      <tr
                        key={wo.id}
                        onClick={() => navigate(`/work-orders/${wo.id}`)}
                        className="cursor-pointer transition-colors hover:bg-neutral-50"
                      >
                        <td className="px-6 py-4 text-sm font-medium text-primary-600">{wo.title || wo.id.slice(0, 8)}</td>
                        <td className="px-6 py-4 text-sm text-neutral-900">{wo.site_name || "—"}</td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <span className={workOrderStatusPillClass(wo.status)}>{wo.status}</span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <span className={urgencyBadgeClass(wo.urgency)}>{t(wo.urgency)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {woTotal > 20 && (
                <div className="flex justify-center gap-2">
                  <button
                    disabled={woPage <= 1}
                    onClick={() => loadWorkOrders(woPage - 1)}
                    className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-40"
                  >
                    ‹ Prev
                  </button>
                  <span className="px-3 py-1.5 text-sm text-neutral-600">
                    Page {woPage} / {Math.ceil(woTotal / 20)}
                  </span>
                  <button
                    disabled={woPage >= Math.ceil(woTotal / 20)}
                    onClick={() => loadWorkOrders(woPage + 1)}
                    className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-40"
                  >
                    Next ›
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === "invoices" && (
        <div className="space-y-4">
          {invLoading ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : invoices.length === 0 ? (
            <EmptyState
              icon={
                <svg className="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
              title={t("no_results")}
              description="No invoices for this company yet."
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">#</th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">{t("status")}</th>
                    <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="border-t border-neutral-200">
                      <td className="px-6 py-4 font-mono text-sm text-primary-600">{inv.number}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          inv.status === "paid" ? "bg-success-light text-success-dark"
                          : inv.status === "draft" ? "bg-neutral-200 text-neutral-600"
                          : "bg-warning-light text-warning-dark"
                        }`}>{inv.status}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-neutral-900">
                        {formatMoneyAmount(inv.total_sar, inv.currency || "SAR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      {activeTab === "settings" && (
        <div className="space-y-6">
          <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-neutral-900">{t("company_contact_settings")}</h2>
            <form
              className="space-y-4 max-w-md"
              onSubmit={async (e) => {
                e.preventDefault();
                setSettingsSaving(true);
                setSettingsError(null);
                setSettingsSaved(false);
                try {
                  // TODO: backend PATCH /clients/{id} or PATCH /users/{adminUserId}
                  await apiFetch(`/clients/${id}`, {
                    method: "PATCH",
                    json: {
                      billing_email: settingsEmail.trim() || undefined,
                      primary_contact_phone: settingsPhone.trim() || undefined,
                    },
                  });
                  setSettingsSaved(true);
                  load();
                } catch (err) {
                  setSettingsError(err instanceof Error ? err.message : t("error"));
                } finally {
                  setSettingsSaving(false);
                }
              }}
            >
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">{t("contact_email")}</label>
                <input
                  type="email"
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  value={settingsEmail}
                  onChange={(e) => setSettingsEmail(e.target.value)}
                  placeholder="billing@example.com"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">{t("contact_phone")}</label>
                <input
                  type="tel"
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  value={settingsPhone}
                  onChange={(e) => setSettingsPhone(e.target.value)}
                  placeholder="+966 5xx xxx xxx"
                />
              </div>
              {settingsError && <p className="text-sm text-error-main">{settingsError}</p>}
              {settingsSaved && <p className="text-sm text-success-dark">{t("settings_saved")}</p>}
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={settingsSaving}
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  {settingsSaving ? t("loading") : t("save")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
