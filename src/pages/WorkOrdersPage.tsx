import { useEffect, useMemo, useState } from "react";

import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { useTranslation } from "react-i18next";



import { apiFetch } from "../lib/api";

import type { PaginatedWorkOrders, ReportTemplate, WorkOrder } from "../lib/types";

import { urgencyBadgeClass, workOrderStatusPillClass } from "../lib/workOrderDisplay";

import { FilterBar } from "../components/FilterBar";

import { WorkOrderRequestReviewModal } from "../components/WorkOrderRequestReviewModal";



interface UserMe {

  id: string;

  role: string;

  client_id?: string | null;

}



interface Company {

  id: string;

  legal_name: string;

}



interface Site {

  id: string;

  name: string;

  client_id: string;

  company_name?: string | null;

}



type WoView = "all" | "requests" | "my_requests";



const ADMIN_ROLES = new Set(["super_admin", "company_admin"]);

const REQUESTER_ROLES = new Set(["client_admin", "site_manager"]);



function statusLabel(status: string, t: (key: string) => string): string {

  const known = [

    "requested",

    "declined",

    "created",

    "assigned",

    "in_progress",

    "on_hold",

    "completed",

    "verified",

    "cancelled",

    "closed",

  ];

  return known.includes(status) ? t(status) : status;

}



export function WorkOrdersPage() {

  const { t } = useTranslation();

  const [searchParams, setSearchParams] = useSearchParams();

  const location = useLocation();

  const navigate = useNavigate();

  const [rows, setRows] = useState<WorkOrder[]>([]);

  const [err, setErr] = useState<string | null>(null);

  const [me, setMe] = useState<UserMe | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);

  const [modalMode, setModalMode] = useState<"create" | "request">("create");

  const [companies, setCompanies] = useState<Company[]>([]);

  const [sites, setSites] = useState<Site[]>([]);

  const [requestSites, setRequestSites] = useState<Site[]>([]);

  const [templates, setTemplates] = useState<ReportTemplate[]>([]);

  const [reviewTarget, setReviewTarget] = useState<WorkOrder | null>(null);

  const [form, setForm] = useState({

    title: "",

    description: "",

    urgency: "normal",

    client_id: "",

    site_id: "",

    asset_id: "",

    source: "request",

    category: "general",

    template_id: "",

  });



  const woView = (searchParams.get("view") as WoView) || "all";

  const canDirectCreate = me ? ADMIN_ROLES.has(me.role) : false;

  const canRequest = me ? REQUESTER_ROLES.has(me.role) : false;

  const canApproveRequests = canDirectCreate;

  const showFilters = me && ["client_admin", "company_admin", "super_admin", "site_manager"].includes(me.role);



  const fetchOrders = async () => {

    try {

      const params = new URLSearchParams();

      searchParams.forEach((value, key) => {

        if (value && key !== "view") params.append(key, value);

      });

      if (woView === "requests") {

        params.set("status", "requested");

      }



      const url = `/work-orders${params.toString() ? `?${params.toString()}` : ""}`;

      const res = await apiFetch<PaginatedWorkOrders>(url);

      let data = res.data;

      if (woView === "my_requests" && me) {

        data = data.filter(

          (w) =>

            (w.status === "requested" || w.status === "declined") &&

            w.creator?.id === me.id

        );

      }

      setRows(data);

    } catch (e) {

      setErr(e instanceof Error ? e.message : "Error");

    }

  };



  const fetchMe = async () => {

    try {

      const user = await apiFetch<UserMe>("/users/me");

      setMe(user);

    } catch (e) {

      console.error("Failed to fetch user", e);

    }

  };



  const fetchCompanies = async () => {

    try {

      const res = await apiFetch<Company[]>("/clients");

      setCompanies(res);

    } catch (e) {

      console.error("Failed to fetch companies", e);

    }

  };



  const fetchSites = async (clientId?: string) => {

    try {

      const url = clientId ? `/sites?client_id=${clientId}` : "/sites";

      const res = await apiFetch<Site[]>(url);

      setSites(res);

    } catch (e) {

      console.error("Failed to fetch sites", e);

    }

  };



  const fetchRequestSites = async () => {

    try {

      const res = await apiFetch<Site[]>("/sites");

      setRequestSites(res);

      if (me?.role === "client_admin" && me.client_id) {

        setForm((f) => ({ ...f, client_id: me.client_id ?? "" }));

        void fetchSites(me.client_id ?? undefined);

      } else if (me?.role === "site_manager" && res.length === 1) {

        setForm((f) => ({

          ...f,

          client_id: res[0].client_id,

          site_id: res[0].id,

        }));

      }

    } catch (e) {

      console.error("Failed to fetch request sites", e);

    }

  };



  const fetchTemplates = async () => {

    try {

      const res = await apiFetch<ReportTemplate[]>("/report-templates");

      setTemplates(res);

    } catch (e) {

      console.error("Failed to fetch templates", e);

    }

  };



  useEffect(() => {

    void fetchMe();

    void fetchCompanies();

    void fetchTemplates();

  }, []);



  const clientIdInUrl = searchParams.get("client_id");

  useEffect(() => {

    void fetchSites(clientIdInUrl || undefined);

  }, [clientIdInUrl]);



  useEffect(() => {

    if (me) void fetchOrders();

  }, [searchParams, woView, me?.id]);



  useEffect(() => {

    const state = location.state as { prefillClientId?: string; prefillSiteId?: string } | null;

    const prefillClientId = state?.prefillClientId;

    const prefillSiteId = state?.prefillSiteId;

    if (prefillClientId && prefillSiteId) {

      setForm((f) => ({

        ...f,

        client_id: prefillClientId,

        site_id: prefillSiteId,

      }));

      void fetchSites(prefillClientId);

      setModalMode(canRequest && !canDirectCreate ? "request" : "create");

      setIsModalOpen(true);

      navigate(location.pathname, { replace: true, state: null });

    }

  }, [location.state, location.pathname, navigate, canDirectCreate, canRequest]);



  const setView = (view: WoView) => {

    const next = new URLSearchParams(searchParams);

    if (view === "all") next.delete("view");

    else next.set("view", view);

    if (view === "requests") next.delete("status");

    setSearchParams(next, { replace: true });

  };



  const openCreateModal = () => {

    setModalMode("create");

    setIsModalOpen(true);

  };



  const openRequestModal = () => {

    setModalMode("request");

    setForm((f) => ({

      ...f,

      source: "request",

      client_id: me?.role === "client_admin" && me.client_id ? me.client_id : "",

      site_id: "",

    }));

    void fetchRequestSites();

    if (me?.role === "client_admin" && me.client_id) {

      void fetchSites(me.client_id);

    }

    setIsModalOpen(true);

  };



  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    const endpoint = modalMode === "request" ? "/work-orders/request" : "/work-orders";

    let clientId = form.client_id;
    let siteId = form.site_id;
    if (modalMode === "request") {
      if (!clientId && me?.client_id) clientId = me.client_id;
      if (!clientId && lockedRequestCompany) clientId = lockedRequestCompany.id;
      if (!siteId && lockedRequestSite) {
        siteId = lockedRequestSite.id;
        clientId = clientId || lockedRequestSite.client_id;
      }
      if (!clientId && requestCompanies.length === 1) clientId = requestCompanies[0].id;
      if (!siteId && requestSiteOptions.length === 1) siteId = requestSiteOptions[0].id;
    }

    try {
      await apiFetch(endpoint, {
        method: "POST",
        json: {
          title: form.title,
          description: form.description,
          urgency: form.urgency,
          client_id: clientId,
          site_id: siteId,
          asset_id: form.asset_id || undefined,
          source: modalMode === "request" ? "request" : form.source,
          category: form.category,
          template_id: form.template_id || undefined,
        },
      });

      setIsModalOpen(false);

      setForm({

        title: "",

        description: "",

        urgency: "normal",

        client_id: "",

        site_id: "",

        asset_id: "",

        source: "request",

        category: "general",

        template_id: "",

      });

      if (canRequest && !canDirectCreate) {

        setView("my_requests");

      }

      void fetchOrders();

    } catch (e: unknown) {

      console.error("Work Order submit error:", e);

      setErr(e instanceof Error ? e.message : "Error");

    }

  };



  const handleClientChange = (clientId: string) => {

    setForm({ ...form, client_id: clientId, site_id: "" });

    void fetchSites(clientId);

  };



  const handleRequestSiteChange = (siteId: string) => {

    const site = requestSites.find((s) => s.id === siteId);

    setForm({

      ...form,

      site_id: siteId,

      client_id: site?.client_id ?? form.client_id,

    });

  };



  const statusOptions = useMemo(

    () => [

      "requested",

      "declined",

      "created",

      "assigned",

      "in_progress",

      "completed",

      "verified",

      "closed",

      "cancelled",

    ],

    []

  );



  const requestCompanies = useMemo(() => {

    if (me?.role === "client_admin") return companies;

    if (me?.role === "site_manager") {

      const map = new Map<string, Company>();

      for (const s of requestSites) {

        if (!map.has(s.client_id)) {

          map.set(s.client_id, {

            id: s.client_id,

            legal_name: s.company_name || s.client_id.slice(0, 8),

          });

        }

      }

      return [...map.values()];

    }

    return companies;

  }, [companies, me?.role, requestSites]);



  const requestSiteOptions = useMemo(() => {

    if (me?.role === "site_manager") return requestSites;

    return sites.filter((s) => s.client_id === form.client_id);

  }, [form.client_id, me?.role, requestSites, sites]);



  const showRequestCompanyField = modalMode === "request" && me?.role !== "site_manager" && requestCompanies.length > 1;

  const showRequestSiteField = modalMode === "request" && requestSiteOptions.length !== 1;

  const lockedRequestCompany =

    modalMode === "request" && (me?.role === "client_admin" || requestCompanies.length === 1)

      ? requestCompanies[0]

      : null;

  const lockedRequestSite =

    modalMode === "request" && requestSiteOptions.length === 1 ? requestSiteOptions[0] : null;



  useEffect(() => {
    if (!isModalOpen || modalMode !== "request") return;
    if (lockedRequestCompany && form.client_id !== lockedRequestCompany.id) {
      setForm((f) => ({ ...f, client_id: lockedRequestCompany.id }));
    }
    if (lockedRequestSite) {
      setForm((f) => ({
        ...f,
        client_id: lockedRequestSite.client_id,
        site_id: lockedRequestSite.id,
      }));
    }
  }, [isModalOpen, modalMode, lockedRequestCompany, lockedRequestSite, form.client_id, form.site_id]);

  const viewTabs: { id: WoView; label: string; show: boolean }[] = [

    { id: "all", label: t("wo_tab_all"), show: true },

    { id: "requests", label: t("wo_tab_requests"), show: canApproveRequests },

    { id: "my_requests", label: t("wo_tab_my_requests"), show: canRequest },

  ];



  return (

    <div className="space-y-4">

      <div className="flex flex-wrap items-center justify-between gap-3">

        <h1 className="text-2xl font-semibold text-neutral-900">{t("work_orders")}</h1>

        <div className="flex flex-wrap gap-2">

          {canDirectCreate && (

            <button

              onClick={openCreateModal}

              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"

            >

              + {t("create_work_order")}

            </button>

          )}

          {canRequest && (

            <button

              onClick={openRequestModal}

              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"

            >

              + {t("request_work_order")}

            </button>

          )}

        </div>

      </div>



      <div className="flex flex-wrap gap-2 border-b border-neutral-200 pb-1">

        {viewTabs

          .filter((tab) => tab.show)

          .map((tab) => (

            <button

              key={tab.id}

              type="button"

              onClick={() => setView(tab.id)}

              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${

                woView === tab.id

                  ? "border-b-2 border-primary-600 text-primary-700"

                  : "text-neutral-600 hover:text-neutral-900"

              }`}

            >

              {tab.label}

            </button>

          ))}

      </div>



      {err && <p className="text-error-main">{err}</p>}



      {showFilters && (

        <FilterBar

          showStatusFilter={woView === "all"}

          showUrgencyFilter

          showDateRange

          showSearch

          showCompanyFilter={canDirectCreate || me?.role === "company_admin" || me?.role === "super_admin"}

          showSiteFilter

          companies={companies}

          sites={sites}

          availableStatuses={statusOptions}

        />

      )}



      {isModalOpen && (

        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">

          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">

            <h2 className="mb-4 text-xl font-bold text-neutral-900">

              {modalMode === "request" ? t("request_work_order") : t("create_work_order")}

            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">

              <div>

                <label className="block text-sm font-medium text-neutral-700">{t("title")}</label>

                <input

                  className="w-full rounded-md border border-neutral-300 p-2"

                  value={form.title}

                  onChange={(e) => setForm({ ...form, title: e.target.value })}

                  required

                />

              </div>

              <div>

                <label className="block text-sm font-medium text-neutral-700">{t("description")}</label>

                <textarea

                  className="w-full rounded-md border border-neutral-300 p-2"

                  value={form.description}

                  onChange={(e) => setForm({ ...form, description: e.target.value })}

                />

              </div>

              <div className={`grid gap-4 ${modalMode === "create" ? "grid-cols-2" : "grid-cols-1"}`}>

                <div>

                  <label className="block text-sm font-medium text-neutral-700">{t("urgency")}</label>

                  <select

                    className="w-full rounded-md border border-neutral-300 p-2"

                    value={form.urgency}

                    onChange={(e) => setForm({ ...form, urgency: e.target.value })}

                  >

                    <option value="normal">{t("normal")}</option>

                    <option value="urgent">{t("urgent")}</option>

                    <option value="emergency">{t("emergency")}</option>

                  </select>

                </div>

                {modalMode === "create" && (

                  <div>

                    <label className="block text-sm font-medium text-neutral-700">{t("source")}</label>

                    <select

                      className="w-full rounded-md border border-neutral-300 p-2"

                      value={form.source}

                      onChange={(e) => setForm({ ...form, source: e.target.value })}

                    >

                      <option value="corrective">{t("corrective")}</option>

                      <option value="preventive">{t("preventive")}</option>

                      <option value="request">{t("request")}</option>

                    </select>

                  </div>

                )}

              </div>



              {modalMode === "request" ? (

                <>

                  {lockedRequestCompany && (

                    <div>

                      <label className="block text-sm font-medium text-neutral-700">{t("company")}</label>

                      <input

                        readOnly

                        className="w-full rounded-md border border-neutral-200 bg-neutral-50 p-2 text-sm"

                        value={lockedRequestCompany.legal_name}

                      />

                      <input type="hidden" value={lockedRequestCompany.id} />

                    </div>

                  )}

                  {showRequestCompanyField && (

                    <div>

                      <label className="block text-sm font-medium text-neutral-700">{t("company")}</label>

                      <select

                        className="w-full rounded-md border border-neutral-300 p-2"

                        value={form.client_id}

                        onChange={(e) => handleClientChange(e.target.value)}

                        required

                      >

                        <option value="">{t("select_company")}</option>

                        {requestCompanies.map((c) => (

                          <option key={c.id} value={c.id}>

                            {c.legal_name}

                          </option>

                        ))}

                      </select>

                    </div>

                  )}

                  {lockedRequestSite && (

                    <div>

                      <label className="block text-sm font-medium text-neutral-700">{t("site")}</label>

                      <input

                        readOnly

                        className="w-full rounded-md border border-neutral-200 bg-neutral-50 p-2 text-sm"

                        value={lockedRequestSite.name}

                      />

                    </div>

                  )}

                  {showRequestSiteField && (

                    <div>

                      <label className="block text-sm font-medium text-neutral-700">{t("site")}</label>

                      <select

                        className="w-full rounded-md border border-neutral-300 p-2"

                        value={form.site_id}

                        onChange={(e) =>

                          me?.role === "site_manager"

                            ? handleRequestSiteChange(e.target.value)

                            : setForm({ ...form, site_id: e.target.value })

                        }

                        required

                        disabled={me?.role !== "site_manager" && !form.client_id}

                      >

                        <option value="">{t("select_site")}</option>

                        {requestSiteOptions.map((s) => (

                          <option key={s.id} value={s.id}>

                            {s.name}

                          </option>

                        ))}

                      </select>

                    </div>

                  )}

                </>

              ) : (

                <div className="grid grid-cols-2 gap-4">

                  <div>

                    <label className="block text-sm font-medium text-neutral-700">{t("company")}</label>

                    <select

                      className="w-full rounded-md border border-neutral-300 p-2"

                      value={form.client_id}

                      onChange={(e) => handleClientChange(e.target.value)}

                      required

                    >

                      <option value="">{t("select_company")}</option>

                      {companies.map((c) => (

                        <option key={c.id} value={c.id}>

                          {c.legal_name}

                        </option>

                      ))}

                    </select>

                  </div>

                  <div>

                    <label className="block text-sm font-medium text-neutral-700">{t("site")}</label>

                    <select

                      className="w-full rounded-md border border-neutral-300 p-2"

                      value={form.site_id}

                      onChange={(e) => setForm({ ...form, site_id: e.target.value })}

                      required

                      disabled={!form.client_id}

                    >

                      <option value="">{t("select_site")}</option>

                      {sites

                        .filter((s) => s.client_id === form.client_id)

                        .map((s) => (

                          <option key={s.id} value={s.id}>

                            {s.name}

                          </option>

                        ))}

                    </select>

                  </div>

                </div>

              )}



              {modalMode === "create" && (

                <div>

                  <label className="block text-sm font-medium text-neutral-700">

                    {t("report_template") || "Report Template"}{" "}

                    <span className="text-xs text-neutral-500">(Optional)</span>

                  </label>

                  <select

                    className="w-full rounded-md border border-neutral-300 p-2"

                    value={form.template_id}

                    onChange={(e) => setForm({ ...form, template_id: e.target.value })}

                  >

                    <option value="">{t("no_template") || "No template"}</option>

                    {templates.map((tmpl) => (

                      <option key={tmpl.id} value={tmpl.id}>

                        {tmpl.name}

                      </option>

                    ))}

                  </select>

                </div>

              )}

              <div className="flex justify-end space-x-3 pt-4">

                <button

                  type="button"

                  onClick={() => setIsModalOpen(false)}

                  className="rounded-md px-4 py-2 text-sm font-medium text-neutral-600 hover:bg-neutral-100"

                >

                  {t("cancel")}

                </button>

                <button

                  type="submit"

                  className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"

                >

                  {modalMode === "request" ? t("submit_request") : t("create")}

                </button>

              </div>

            </form>

          </div>

        </div>

      )}



      {reviewTarget && (

        <WorkOrderRequestReviewModal

          workOrder={reviewTarget}

          open

          onClose={() => setReviewTarget(null)}

          onResolved={() => void fetchOrders()}

        />

      )}



      <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">

        <table className="min-w-full text-start text-sm">

          <thead className="bg-neutral-100 text-neutral-700">

            <tr>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("title")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("status")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("company")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("site")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("created_by")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("assigned_to")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("urgency")}</th>

              <th className="px-3 py-3 font-medium whitespace-nowrap">{t("date_created")}</th>

              {canApproveRequests && woView === "requests" && (

                <th className="px-3 py-3 font-medium whitespace-nowrap">{t("actions")}</th>

              )}

            </tr>

          </thead>

          <tbody>

            {rows.length === 0 && (

              <tr>

                <td colSpan={canApproveRequests && woView === "requests" ? 9 : 8} className="px-3 py-8 text-center text-neutral-500">

                  {t("no_results")}

                </td>

              </tr>

            )}

            {rows.map((w) => (

              <tr key={w.id} className="border-t border-neutral-200 hover:bg-neutral-50">

                <td className="px-3 py-3 whitespace-nowrap">

                  <Link className="text-primary-600 hover:underline" to={`/work-orders/${w.id}`}>

                    {w.title || w.id.slice(0, 8)}

                  </Link>

                </td>

                <td className="px-3 py-3 whitespace-nowrap">

                  <span className={workOrderStatusPillClass(w.status)}>{statusLabel(w.status, t)}</span>

                </td>

                <td

                  className="max-w-[10rem] truncate px-3 py-3 text-sm text-neutral-700"

                  title={w.company_name || undefined}

                >

                  {w.company_name || "—"}

                </td>

                <td

                  className="max-w-[10rem] truncate px-3 py-3 text-sm text-neutral-700"

                  title={w.site_name || undefined}

                >

                  {w.site_name || "—"}

                </td>

                <td

                  className="max-w-[9rem] truncate px-3 py-3 text-sm text-neutral-700"

                  title={w.creator?.full_name || w.creator?.email || undefined}

                >

                  {w.creator?.full_name || w.creator?.email || "—"}

                </td>

                <td

                  className="max-w-[9rem] truncate px-3 py-3 text-sm text-neutral-700"

                  title={w.assignee?.full_name || w.assignee?.email || undefined}

                >

                  {w.assignee?.full_name || w.assignee?.email || "—"}

                </td>

                <td className="px-3 py-3 text-sm whitespace-nowrap">

                  <span className={urgencyBadgeClass(w.urgency)}>

                    {["normal", "urgent", "emergency"].includes(w.urgency) ? t(w.urgency) : w.urgency}

                  </span>

                </td>

                <td className="px-3 py-3 text-sm text-neutral-600 whitespace-nowrap">

                  {new Date(w.opened_at).toLocaleString()}

                </td>

                {canApproveRequests && woView === "requests" && (

                  <td className="px-3 py-3 whitespace-nowrap">

                    {w.status === "requested" ? (

                      <button

                        type="button"

                        className="rounded-md bg-primary-600 px-3 py-1 text-xs font-medium text-white hover:bg-primary-700"

                        onClick={() => setReviewTarget(w)}

                      >

                        {t("review_request")}

                      </button>

                    ) : (

                      "—"

                    )}

                  </td>

                )}

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>

  );

}


