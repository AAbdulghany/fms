import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { useTranslation } from "react-i18next";



import { apiFetch } from "@/lib/api";

import { useAuth } from "@/contexts/AuthContext";

import type { PaginatedWorkOrders, WorkOrder } from "@/lib/types";

import { displayWorkOrderTitle, urgencyBadgeClass, workOrderStatusPillClass } from "@/lib/workOrderDisplay";

import { FilterBar } from "@/shared/components/FilterBar";

import { WorkOrderRequestReviewModal } from "@/features/work-orders/components/WorkOrderRequestReviewModal";
import { StartNextHero } from "@/features/work-orders/components/StartNextHero";




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



interface AssetOption {

  id: string;

  name: string;

  category: string;

  site_id?: string;

  site_name?: string | null;

  company_name?: string | null;

}



type WoView = "all" | "requests" | "my_requests";



const ADMIN_ROLES = new Set(["super_admin", "company_admin"]);

const CREATE_ROLES = new Set(["super_admin", "company_admin", "company_engineer"]);

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

  const { t, i18n } = useTranslation();

  const [searchParams, setSearchParams] = useSearchParams();

  const location = useLocation();

  const navigate = useNavigate();

  const { user: me } = useAuth();

  const [rows, setRows] = useState<WorkOrder[]>([]);

  const [err, setErr] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);

  const [modalMode, setModalMode] = useState<"create" | "request">("create");

  const [companies, setCompanies] = useState<Company[]>([]);

  const [sites, setSites] = useState<Site[]>([]);

  const [assets, setAssets] = useState<AssetOption[]>([]);

  const [assetQuery, setAssetQuery] = useState("");

  const [assetHits, setAssetHits] = useState<AssetOption[]>([]);

  const [pickedAssetLabel, setPickedAssetLabel] = useState("");

  const [pickedAssetMeta, setPickedAssetMeta] = useState("");

  const [autoTitle, setAutoTitle] = useState("");

  const [requestSites, setRequestSites] = useState<Site[]>([]);

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

  });



  const woView = (searchParams.get("view") as WoView) || "all";

  const canDirectCreate = me ? CREATE_ROLES.has(me.role) : false;

  const canRequest = me ? REQUESTER_ROLES.has(me.role) : false;

  const canApproveRequests = me ? ADMIN_ROLES.has(me.role) : false;

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



  const fetchAssets = async (siteId: string) => {

    if (!siteId) {

      setAssets([]);

      return;

    }

    try {

      const res = await apiFetch<AssetOption[]>(`/assets?site_id=${siteId}`);

      setAssets(res);

    } catch (e) {

      console.error("Failed to fetch assets", e);

      setAssets([]);

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



  useEffect(() => {

    void fetchCompanies();

  }, []);



  const clientIdInUrl = searchParams.get("client_id");

  useEffect(() => {

    void fetchSites(clientIdInUrl || undefined);

  }, [clientIdInUrl]);



  useEffect(() => {

    if (me) void fetchOrders();

  }, [searchParams, woView, me?.id]);



  useEffect(() => {

    const reviewId = searchParams.get("review");

    if (!reviewId || !canApproveRequests) return;

    const found = rows.find((r) => r.id === reviewId);

    if (found?.status === "requested") {

      setReviewTarget(found);

      return;

    }

    void apiFetch<WorkOrder>(`/work-orders/${reviewId}`)

      .then((wo) => {

        if (wo.status === "requested") setReviewTarget(wo);

      })

      .catch(() => {});

  }, [searchParams, rows, canApproveRequests]);



  useEffect(() => {
    if (searchParams.get("open") !== "request" || !me || !canRequest) return;

    setModalMode("request");
    setForm((f) => ({
      ...f,
      source: "request",
      client_id: me.role === "client_admin" && me.client_id ? me.client_id : "",
      site_id: "",
    }));
    void fetchRequestSites();
    if (me.role === "client_admin" && me.client_id) {
      void fetchSites(me.client_id);
    }
    setIsModalOpen(true);

    const next = new URLSearchParams(searchParams);
    next.delete("open");
    setSearchParams(next, { replace: true });
  }, [me, canRequest, searchParams]);

  useEffect(() => {
    if (searchParams.get("open") !== "create") return;
    if (me && !canDirectCreate) return;

    setModalMode("create");
    setIsModalOpen(true);
    if (!me) return;
    const assetIdParam = searchParams.get("asset_id");

    if (assetIdParam) {
      void (async () => {
        try {
          const asset = await apiFetch<{ id: string; name?: string; site_id: string }>(`/assets/${assetIdParam}`);
          const siteList = await apiFetch<Site[]>("/sites");
          const site = siteList.find((s) => s.id === asset.site_id);
          if (asset.name) {
            setAssetQuery(asset.name);
            setPickedAssetLabel(asset.name);
            setPickedAssetMeta(site?.name || "");
          }
          if (site) {
            setForm((f) => ({
              ...f,
              client_id: site.client_id,
              site_id: site.id,
              asset_id: assetIdParam,
            }));
            void fetchSites(site.client_id);
            void fetchAssets(site.id);
          } else {
            setForm((f) => ({ ...f, asset_id: assetIdParam }));
          }
        } catch (e) {
          console.error("Failed to prefill asset for work order", e);
        }
      })();
    }

  }, [me, canDirectCreate, searchParams]);



  useEffect(() => {

    const state = location.state as { prefillClientId?: string; prefillSiteId?: string } | null;

    const prefillClientId = state?.prefillClientId;

    const prefillSiteId = state?.prefillSiteId;

    if (!prefillClientId) return;

    setForm((f) => ({

      ...f,

      client_id: prefillClientId,

      site_id: prefillSiteId ?? "",

    }));

    void fetchSites(prefillClientId);

    setModalMode(canRequest && !canDirectCreate ? "request" : "create");

    setIsModalOpen(true);

    navigate(location.pathname + location.search, { replace: true, state: null });

  }, [location.state, location.pathname, location.search, navigate, canDirectCreate, canRequest]);



  const closeReviewModal = () => {

    setReviewTarget(null);

    const next = new URLSearchParams(searchParams);

    next.delete("review");

    setSearchParams(next, { replace: true });

  };



  const setView = (view: WoView) => {

    const next = new URLSearchParams(searchParams);

    if (view === "all") next.delete("view");

    else next.set("view", view);

    if (view === "requests") next.delete("status");

    setSearchParams(next, { replace: true });

  };



  const clearCreateQuery = () => {
    if (searchParams.get("open") === "create" || searchParams.get("asset_id")) {
      const next = new URLSearchParams(searchParams);
      next.delete("open");
      next.delete("asset_id");
      setSearchParams(next, { replace: true });
    }
  };

  const closeWorkOrderModal = () => {
    setIsModalOpen(false);
    clearCreateQuery();
  };

  const dismissCreate = () => {
    setIsModalOpen(false);
    if (searchParams.get("open") === "create" && window.history.length > 1) {
      navigate(-1);
      return;
    }
    clearCreateQuery();
  };

  const openCreateModal = () => {

    setModalMode("create");

    setForm((f) => ({ ...f, source: f.source === "request" ? "corrective" : f.source }));

    void fetchSites();

    setIsModalOpen(true);

  };

  useEffect(() => {
    if (!isModalOpen) return;
    const q = assetQuery.trim();
    if (q.length < 2 || q === pickedAssetLabel) {
      setAssetHits([]);
      return;
    }
    const handle = window.setTimeout(() => {
      void (async () => {
        try {
          const res = await apiFetch<AssetOption[]>(`/assets?search=${encodeURIComponent(q)}`);
          setAssetHits(res.slice(0, 6));
        } catch {
          setAssetHits([]);
        }
      })();
    }, 250);
    return () => window.clearTimeout(handle);
  }, [assetQuery, isModalOpen, pickedAssetLabel]);

  useEffect(() => {
    const assetName = pickedAssetLabel.trim();
    if (!isModalOpen || !assetName) {
      setAutoTitle("");
      return;
    }
    const source = modalMode === "request" ? "request" : form.source || "corrective";
    const ar = i18n.language?.startsWith("ar");
    const phrase = ar
      ? source === "preventive"
        ? "صيانة وقائية"
        : source === "corrective"
          ? "صيانة تصحيحية"
          : "صيانة"
      : source === "preventive"
        ? "Preventive maintenance"
        : source === "corrective"
          ? "Corrective maintenance"
          : t(source);
    setAutoTitle(`${phrase} — ${assetName}`);
  }, [isModalOpen, pickedAssetLabel, form.source, modalMode, i18n.language, t]);

  async function pickAsset(hit: AssetOption) {
    let clientId = sites.find((s) => s.id === hit.site_id)?.client_id || "";
    if (!clientId && hit.site_id) {
      try {
        const siteList = await apiFetch<Site[]>("/sites");
        setSites(siteList);
        clientId = siteList.find((s) => s.id === hit.site_id)?.client_id || "";
      } catch {
        clientId = "";
      }
    }
    setPickedAssetLabel(hit.name);
    setPickedAssetMeta([hit.company_name, hit.site_name].filter(Boolean).join(" · "));
    setAssetQuery(hit.name);
    setAssetHits([]);
    setForm((f) => ({
      ...f,
      asset_id: hit.id,
      site_id: hit.site_id || f.site_id,
      client_id: clientId || f.client_id,
      title: f.title || hit.name,
    }));
  }



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

    if (!form.asset_id) {
      setErr(t("asset_required"));
      return;
    }

    try {
      const lang = i18n.language?.startsWith("ar") ? "ar" : "en";
      await apiFetch(`${endpoint}?lang=${lang}`, {
        method: "POST",
        json: {
          title: autoTitle,
          description: form.description,
          urgency: form.urgency,
          client_id: clientId,
          site_id: siteId,
          asset_id: form.asset_id,
          source: modalMode === "request" ? "request" : form.source,
          category: form.category,
        },
      });

      closeWorkOrderModal();

      setForm({

        title: "",

        description: "",

        urgency: "normal",

        client_id: "",

        site_id: "",

        asset_id: "",

        source: "request",

        category: "general",

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

    setForm({ ...form, client_id: clientId, site_id: "", asset_id: "" });

    setAssets([]);

    void fetchSites(clientId);

  };



  const handleSiteChange = (siteId: string) => {

    setForm({ ...form, site_id: siteId, asset_id: "" });

    void fetchAssets(siteId);

  };



  const handleRequestSiteChange = (siteId: string) => {

    const site = requestSites.find((s) => s.id === siteId);

    setForm({

      ...form,

      site_id: siteId,

      client_id: site?.client_id ?? form.client_id,

      asset_id: "",

    });

    void fetchAssets(siteId);

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

  useEffect(() => {
    if (!isModalOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [isModalOpen]);

  const viewTabs: { id: WoView; label: string; show: boolean }[] = [

    { id: "all", label: t("wo_tab_all"), show: true },

    { id: "requests", label: t("wo_tab_requests"), show: canApproveRequests },

    { id: "my_requests", label: t("wo_tab_my_requests"), show: canRequest },

  ];

  const nextWo =
    rows.find((w) =>
      ["assigned", "in_progress", "created", "on_hold"].includes(w.status)
    ) ?? rows[0] ?? null;
  const upNextRows = nextWo ? rows.filter((w) => w.id !== nextWo.id) : rows;

  return (

    <div className="space-y-3 lg:space-y-4">

      <div className="flex flex-wrap items-center justify-between gap-2 lg:gap-3">

        <h1 className="text-xl font-semibold text-neutral-900 lg:text-2xl">{t("my_work")}</h1>

        <div className="hidden flex-wrap gap-2 lg:flex">

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

      <StartNextHero
        workOrder={nextWo}
        canCreate={Boolean(canDirectCreate || canRequest)}
        onCreate={canDirectCreate ? openCreateModal : canRequest ? openRequestModal : undefined}
      />



      <div className="hidden flex-wrap gap-2 border-b border-neutral-200 pb-1 lg:flex">

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

        <div className="hidden lg:block">

          <FilterBar

            showStatusFilter={woView === "all"}

            showUrgencyFilter

            showDateRange

            showSearch

            showCompanyFilter={Boolean(me && ADMIN_ROLES.has(me.role))}

            showSiteFilter

            companies={companies}

            sites={sites}

            availableStatuses={statusOptions}

          />

        </div>

      )}



      {isModalOpen && createPortal(

        <div className="fixed inset-0 z-[80] flex h-dvh w-full overflow-hidden overscroll-none bg-[#F7F9FC] lg:items-center lg:justify-center lg:bg-black/50 lg:backdrop-blur-sm">

          <div className="flex h-dvh w-full flex-col overflow-hidden bg-[#F7F9FC] lg:h-auto lg:max-h-[90vh] lg:max-w-md lg:overflow-y-auto lg:rounded-xl lg:bg-white lg:p-6 lg:shadow-xl">

            <header className="flex items-center gap-2 border-b border-neutral-200 bg-white px-3 py-3 lg:hidden">
              <button
                type="button"
                className="min-h-11 min-w-11 text-lg text-neutral-900"
                onClick={dismissCreate}
                aria-label={t("back") || "Back"}
              >
                ‹
              </button>
              <h2 className="min-w-0 flex-1 truncate text-base font-bold text-neutral-900">
                {modalMode === "request" ? t("request_work_order") : t("new_work_order")}
              </h2>
            </header>

            <h2 className="mb-4 hidden text-xl font-bold text-neutral-900 lg:block">

              {modalMode === "request" ? t("request_work_order") : t("create_work_order")}

            </h2>

            <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col lg:block lg:space-y-4">

              <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:hidden">
                <div className="rounded-xl border border-neutral-200 bg-white px-3 py-2.5">
                  <label className="block text-sm font-bold text-neutral-900" htmlFor="phone-asset-search">
                    {t("asset")}
                  </label>
                  <input
                    id="phone-asset-search"
                    type="search"
                    className="mt-1 w-full bg-transparent text-base text-neutral-900 outline-none placeholder:text-neutral-500"
                    placeholder={t("scan_or_search")}
                    value={assetQuery}
                    onChange={(e) => {
                      const next = e.target.value;
                      setAssetQuery(next);
                      if (next !== pickedAssetLabel) {
                        setForm((f) => ({ ...f, asset_id: "" }));
                      }
                    }}
                    autoComplete="off"
                  />
                  {form.asset_id && pickedAssetLabel === assetQuery && pickedAssetMeta && (
                    <p className="mt-1 text-xs text-neutral-500">{pickedAssetMeta}</p>
                  )}
                  {assetHits.length > 0 && (
                    <ul className="mt-2 max-h-40 overflow-auto rounded-lg border border-neutral-200">
                      {assetHits.map((hit) => (
                        <li key={hit.id}>
                          <button
                            type="button"
                            className="w-full px-3 py-2 text-start text-sm hover:bg-neutral-50"
                            onClick={() => void pickAsset(hit)}
                          >
                            <span className="font-medium text-neutral-900">{hit.name}</span>
                            {(hit.site_name || hit.company_name) && (
                              <span className="mt-0.5 block text-xs text-neutral-500">
                                {[hit.company_name, hit.site_name].filter(Boolean).join(" · ")}
                              </span>
                            )}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="rounded-xl border border-neutral-200 bg-white px-3 py-2.5">
                  <p className="text-sm font-bold text-neutral-900">{t("priority")}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(["normal", "urgent", "emergency"] as const).map((level) => {
                      const on = form.urgency === level;
                      return (
                        <button
                          key={level}
                          type="button"
                          className={
                            on
                              ? "rounded-lg bg-primary-700 px-3 py-1.5 text-sm font-semibold text-white"
                              : "rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-800"
                          }
                          onClick={() => setForm((f) => ({ ...f, urgency: level }))}
                        >
                          {t(level)}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {modalMode === "create" && (
                  <div className="rounded-xl border border-neutral-200 bg-white px-3 py-2.5">
                    <p className="text-sm font-bold text-neutral-900">{t("source")}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(["corrective", "preventive"] as const).map((src) => {
                        const on = form.source === src;
                        return (
                          <button
                            key={src}
                            type="button"
                            className={
                              on
                                ? "rounded-lg bg-primary-700 px-3 py-1.5 text-sm font-semibold text-white"
                                : "rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-800"
                            }
                            onClick={() => setForm((f) => ({ ...f, source: src }))}
                          >
                            {t(src)}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <label className="rounded-xl border border-neutral-200 bg-white px-3 py-2.5">
                  <span className="block text-sm font-bold text-neutral-900">{t("description")}</span>
                  <textarea
                    className="mt-1 w-full resize-none bg-transparent text-base text-neutral-900 outline-none placeholder:text-neutral-500"
                    rows={3}
                    placeholder={t("description")}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </label>

                <div className="rounded-xl border border-dashed border-neutral-300 bg-white px-3 py-2.5">
                  <p className="text-xs font-semibold text-neutral-500">{t("title")}</p>
                  <p className="mt-1 text-sm font-semibold text-neutral-900">
                    {autoTitle || t("wo_title_needs_asset")}
                  </p>
                </div>

                <button
                  type="submit"
                  className="mt-auto min-h-11 w-full shrink-0 rounded-xl bg-primary-700 text-sm font-bold text-white"
                >
                  {modalMode === "request" ? t("submit_request") : t("create_work_order")}
                </button>
              </div>

              <div className="hidden space-y-4 lg:block">

              <div>

                <p className="block text-sm font-medium text-neutral-700">{t("title")}</p>

                <p className="mt-1 rounded-md border border-neutral-200 bg-neutral-50 p-2 text-sm text-neutral-900">

                  {autoTitle || t("wo_title_needs_asset")}

                </p>

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

                            : handleSiteChange(e.target.value)

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

                      onChange={(e) => handleSiteChange(e.target.value)}

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



              <div>

                <label className="block text-sm font-medium text-neutral-700">{t("asset")}</label>

                <select

                  className="w-full rounded-md border border-neutral-300 p-2"

                  value={form.asset_id}

                  onChange={(e) => setForm({ ...form, asset_id: e.target.value })}

                  required

                  disabled={!form.site_id}

                >

                  <option value="">{t("select_asset")}</option>

                  {assets.map((a) => (

                    <option key={a.id} value={a.id}>

                      {a.name} ({a.category})

                    </option>

                  ))}

                </select>

              </div>



              <div className="flex justify-end space-x-3 pt-4">

                <button

                  type="button"

                  onClick={dismissCreate}

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

              </div>

            </form>

          </div>

        </div>,

        document.body

      )}



      {reviewTarget && (

        <WorkOrderRequestReviewModal

          workOrder={reviewTarget}

          open

          onClose={closeReviewModal}

          onResolved={() => void fetchOrders()}

        />

      )}



      {/* D FINAL · F Queue — phone card stack */}
      <div className="space-y-2 lg:hidden">
        <p className="text-xs font-semibold text-neutral-500">{t("up_next")}</p>
        <ul className="space-y-2">
          {upNextRows.length === 0 && (
            <li className="rounded-xl border border-neutral-200 bg-neutral-0 px-4 py-6 text-center text-sm text-neutral-500">
              {rows.length === 0 ? t("no_results") : t("queue_empty_title")}
            </li>
          )}
          {upNextRows.map((w) => {
            return (
              <li key={w.id}>
                <Link
                  to={`/work-orders/${w.id}`}
                  className="block rounded-xl border border-neutral-200 bg-neutral-0 px-3 py-3 shadow-sm active:bg-neutral-50"
                >
                  <p className="truncate text-sm font-bold text-neutral-900">
                    {displayWorkOrderTitle(w, i18n.language)}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-neutral-500">
                    {w.asset_name || w.asset_category || w.site_name || ""}
                  </p>
                  <span className="mt-1.5 flex flex-wrap gap-1.5">
                    <span className={workOrderStatusPillClass(w.status)}>{statusLabel(w.status, t)}</span>
                    <span className={urgencyBadgeClass(w.urgency)}>{t(w.urgency)}</span>
                  </span>
                  {canApproveRequests && woView === "requests" && w.status === "requested" ? (
                    <button
                      type="button"
                      className="mt-2 min-h-10 w-full rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setReviewTarget(w);
                      }}
                    >
                      {t("review") || t("actions") || "Review"}
                    </button>
                  ) : null}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Desktop: table */}
      <div className="hidden overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm lg:block">

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

                    {displayWorkOrderTitle(w, i18n.language)}

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


