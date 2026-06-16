import { FormEvent, Fragment, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";

type ClientRow = {
  id: string;
  legal_name: string;
  code: string;
  status: string;
};

type MaintenanceCompany = {
  id: string;
  name: string;
  status: string;
  client_count: number;
  clients: ClientRow[];
  subscription?: { plan: string; status: string; valid_until?: string | null };
};

type Package = { id: string; code: string; name: string };

const EMPTY_TENANT = {
  tenant_name: "",
  admin_email: "",
  admin_full_name: "",
  admin_password: "",
  package_id: "",
};

export function MaintenanceCompaniesPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<MaintenanceCompany[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_TENANT);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const qs = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
      const [companies, pkgs] = await Promise.all([
        apiFetch<MaintenanceCompany[]>(`/platform/maintenance-companies${qs}`),
        apiFetch<Package[]>("/platform/packages?active_only=true"),
      ]);
      setRows(companies);
      setPackages(pkgs);
      if (!form.package_id && pkgs[0]) {
        setForm((f) => ({ ...f, package_id: pkgs[0].id }));
      }
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreateTenant(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      const res = await apiFetch<{ initial_password?: string }>("/platform/tenants", {
        method: "POST",
        json: {
          tenant_name: form.tenant_name,
          admin_email: form.admin_email,
          admin_full_name: form.admin_full_name,
          admin_password: form.admin_password || undefined,
          package_id: form.package_id,
        },
      });
      setForm({ ...EMPTY_TENANT, package_id: form.package_id });
      setMsg(
        res.initial_password
          ? `${t("saved")} — temp password: ${res.initial_password}`
          : t("saved") || "Saved"
      );
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("error"));
    }
  }

  if (loading) return <div className="p-8">{t("loading")}</div>;

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-semibold">
          {t("maintenance_companies") || "Maintenance companies"}
        </h1>
        <div className="flex gap-2">
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder={t("search") || "Search"}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-md border px-3 py-2 text-sm hover:bg-neutral-50"
          >
            {t("filter") || "Filter"}
          </button>
        </div>
      </div>

      <form onSubmit={onCreateTenant} className="space-y-4 rounded-lg border p-6">
        <h2 className="text-lg font-medium">{t("add_tenant") || "Add maintenance company"}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder="Company name"
            value={form.tenant_name}
            onChange={(e) => setForm({ ...form, tenant_name: e.target.value })}
            required
          />
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={form.package_id}
            onChange={(e) => setForm({ ...form, package_id: e.target.value })}
            required
          >
            {packages.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder="Admin email"
            type="email"
            value={form.admin_email}
            onChange={(e) => setForm({ ...form, admin_email: e.target.value })}
            required
          />
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder="Admin full name"
            value={form.admin_full_name}
            onChange={(e) => setForm({ ...form, admin_full_name: e.target.value })}
            required
          />
        </div>
        {msg && <p className="text-sm text-neutral-600">{msg}</p>}
        <button type="submit" className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white">
          {t("save")}
        </button>
      </form>

      <div className="overflow-hidden rounded-lg border">
        <table className="min-w-full text-sm">
          <thead className="bg-neutral-50 text-left">
            <tr>
              <th className="px-4 py-2">Company</th>
              <th className="px-4 py-2">Plan</th>
              <th className="px-4 py-2">Clients</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((row) => (
              <Fragment key={row.id}>
                <tr
                  className="cursor-pointer hover:bg-neutral-50"
                  onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                >
                  <td className="px-4 py-3 font-medium">{row.name}</td>
                  <td className="px-4 py-3">{row.subscription?.plan ?? "—"}</td>
                  <td className="px-4 py-3">{row.client_count}</td>
                  <td className="px-4 py-3">{row.status}</td>
                </tr>
                {expanded === row.id && (
                  <tr key={`${row.id}-clients`}>
                    <td colSpan={4} className="bg-neutral-50 px-6 py-3">
                      <p className="mb-2 text-xs font-semibold uppercase text-neutral-500">
                        {t("end_clients") || "End clients"}
                      </p>
                      {row.clients.length === 0 ? (
                        <p className="text-neutral-500">—</p>
                      ) : (
                        <ul className="space-y-1">
                          {row.clients.map((c) => (
                            <li key={c.id}>
                              {c.legal_name} <span className="text-neutral-400">({c.code})</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
