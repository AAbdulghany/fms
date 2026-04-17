import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import type { PaginatedWorkOrders, WorkOrder } from "../lib/types";
import { FilterBar } from "../components/FilterBar";

interface UserMe {
  role: string;
}

interface Company {
  id: string;
  legal_name: string;
}

interface Site {
  id: string;
  name: string;
  client_id: string;
}

export function WorkOrdersPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const [rows, setRows] = useState<WorkOrder[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [form, setForm] = useState({
    title: "",
    description: "",
    urgency: "normal",
    client_id: "",
    site_id: "",
    asset_id: "",
    source: "corrective",
    category: "general",
  });

  const fetchOrders = async () => {
    try {
      // Build query string from search params
      const params = new URLSearchParams();
      searchParams.forEach((value, key) => {
        if (value) params.append(key, value);
      });
      
      const url = `/work-orders${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<PaginatedWorkOrders>(url);
      setRows(res.data);
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

  useEffect(() => {
    void fetchMe();
    void fetchCompanies();
  }, []);

  useEffect(() => {
    void fetchOrders();
  }, [searchParams]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    try {
      await apiFetch("/work-orders", {
        method: "POST",
        json: {
          title: form.title,
          description: form.description,
          urgency: form.urgency,
          client_id: form.client_id,
          site_id: form.site_id,
          asset_id: form.asset_id || undefined,
          source: form.source,
          category: form.category,
        },
      });
      setIsModalOpen(false);
      setForm({ title: "", description: "", urgency: "normal", client_id: "", site_id: "", asset_id: "", source: "corrective", category: "general" });
      void fetchOrders();
    } catch (e: any) {
      console.error("Work Order Creation Error:", e);
      const errMsg = e.response?.data?.detail || e.message || "Error creating work order";
      setErr(errMsg);
    }
  };

  const handleClientChange = (clientId: string) => {
    setForm({ ...form, client_id: clientId, site_id: "" });
    void fetchSites(clientId);
  };

  // Show filters for client_admin, company_admin, super_admin
  const canUseFilters = me && ["client_admin", "company_admin", "super_admin"].includes(me.role);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-neutral-900">{t("work_orders")}</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
        >
          + {t("create_work_order")}
        </button>
      </div>

      {err && <p className="text-error-main">{err}</p>}

      {canUseFilters && (
        <FilterBar
          showStatusFilter
          showUrgencyFilter
          showDateRange
          showSearch
        />
      )}

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("create_work_order")}</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700">{t("title")}</label>
                <input 
                  className="w-full rounded-md border border-neutral-300 p-2"
                  value={form.title}
                  onChange={e => setForm({...form, title: e.target.value})}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700">{t("description")}</label>
                <textarea 
                  className="w-full rounded-md border border-neutral-300 p-2"
                  value={form.description}
                  onChange={e => setForm({...form, description: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700">{t("urgency")}</label>
                  <select 
                    className="w-full rounded-md border border-neutral-300 p-2"
                    value={form.urgency}
                    onChange={e => setForm({...form, urgency: e.target.value})}
                  >
                    <option value="normal">{t("normal")}</option>
                    <option value="urgent">{t("urgent")}</option>
                    <option value="emergency">{t("emergency")}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">{t("source")}</label>
                  <select 
                    className="w-full rounded-md border border-neutral-300 p-2"
                    value={form.source}
                    onChange={e => setForm({...form, source: e.target.value})}
                  >
                    <option value="corrective">{t("corrective")}</option>
                    <option value="preventive">{t("preventive")}</option>
                    <option value="request">{t("request")}</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700">{t("company")}</label>
                  <select
                    className="w-full rounded-md border border-neutral-300 p-2"
                    value={form.client_id}
                    onChange={e => handleClientChange(e.target.value)}
                    required
                  >
                    <option value="">{t("select_company")}</option>
                    {companies.map(c => (
                      <option key={c.id} value={c.id}>{c.legal_name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">{t("site")}</label>
                  <select
                    className="w-full rounded-md border border-neutral-300 p-2"
                    value={form.site_id}
                    onChange={e => setForm({...form, site_id: e.target.value})}
                    required
                    disabled={!form.client_id}
                  >
                    <option value="">{t("select_site")}</option>
                    {sites.filter(s => s.client_id === form.client_id).map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
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
                  {t("create")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
        <table className="min-w-full text-start text-sm">
          <thead className="bg-neutral-100 text-neutral-700">
            <tr>
              <th className="px-4 py-3 font-medium">{t("title")}</th>
              <th className="px-4 py-3 font-medium">{t("status")}</th>
              <th className="px-4 py-3 font-medium">{t("created_by")}</th>
              <th className="px-4 py-3 font-medium">{t("assigned_to")}</th>
              <th className="px-4 py-3 font-medium">ID</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((w) => (
              <tr key={w.id} className="border-t border-neutral-200 hover:bg-neutral-50">
                <td className="px-4 py-3">
                  <Link className="text-primary-600 hover:underline" to={`/work-orders/${w.id}`}>
                    {w.title || w.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs">{w.status}</span>
                </td>
                <td className="px-4 py-3 text-sm text-neutral-700">
                  {w.creator?.full_name || w.creator?.email || "—"}
                </td>
                <td className="px-4 py-3 text-sm text-neutral-700">
                  {w.assignee?.full_name || w.assignee?.email || "—"}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-neutral-500">{w.id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
