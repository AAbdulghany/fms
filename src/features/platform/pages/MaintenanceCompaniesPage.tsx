import { FormEvent, Fragment, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import { ProvisionCredentialsModal } from "@/features/companies/components/ProvisionCredentialsModal";
import { SlideNotice } from "@/shared/components/SlideNotice";

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
  subscription?: {
    plan: string;
    package_id?: string | null;
    status: string;
    valid_until?: string | null;
  };
};

type Package = { id: string; code: string; name: string };

type Credentials = {
  title: string;
  username: string;
  email: string;
  initialPassword: string;
};

const EMPTY_TENANT = {
  tenant_name: "",
  admin_email: "",
  admin_full_name: "",
  admin_password: "",
  package_id: "",
  valid_until: "",
};

function formatApiError(err: unknown, fallback: string): string {
  if (!(err instanceof Error)) return fallback;
  try {
    const parsed = JSON.parse(err.message) as { detail?: unknown };
    const detail = parsed.detail;
    if (typeof detail === "string") {
      if (detail === "INVALID_PACKAGE") return "No active package — pick a package or seed the pilot DB.";
      if (detail === "EMAIL_ALREADY_EXISTS") return "That admin email is already registered.";
      if (detail === "FORBIDDEN") return "Platform admin access required.";
      if (detail === "CANNOT_DELETE_OWN_TENANT") return "Cannot delete your own platform tenant.";
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === "object" && item && "msg" in item ? String((item as { msg: unknown }).msg) : String(item)))
        .join("; ");
    }
  } catch {
    /* plain Error message */
  }
  return err.message || fallback;
}

export function MaintenanceCompaniesPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<MaintenanceCompany[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_TENANT);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<Credentials | null>(null);
  const [licenseDraft, setLicenseDraft] = useState<Record<string, { package_id: string; valid_until: string; status: string }>>({});

  async function load() {
    setLoading(true);
    setLoadError(null);
    try {
      const qs = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
      const [companies, pkgs] = await Promise.all([
        apiFetch<MaintenanceCompany[]>(`/platform/maintenance-companies${qs}`),
        apiFetch<Package[]>("/platform/packages?active_only=true"),
      ]);
      setRows(companies);
      setPackages(pkgs);
      setForm((f) => {
        if (f.package_id && pkgs.some((p) => p.id === f.package_id)) return f;
        return { ...f, package_id: pkgs[0]?.id ?? "" };
      });
      const drafts: typeof licenseDraft = {};
      for (const row of companies) {
        drafts[row.id] = {
          package_id: row.subscription?.package_id || pkgs[0]?.id || "",
          valid_until: row.subscription?.valid_until?.slice(0, 10) || "",
          status: row.subscription?.status || "active",
        };
      }
      setLicenseDraft(drafts);
    } catch (err) {
      setRows([]);
      setPackages([]);
      setLoadError(formatApiError(err, t("error") || "Failed to load companies"));
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
    if (!form.package_id) {
      setMsg("Select an active subscription package before creating a company.");
      return;
    }
    setSaving(true);
    try {
      const res = await apiFetch<{
        tenant_id: string;
        initial_password?: string;
      }>("/platform/tenants", {
        method: "POST",
        json: {
          tenant_name: form.tenant_name,
          admin_email: form.admin_email,
          admin_full_name: form.admin_full_name,
          admin_password: form.admin_password || undefined,
          package_id: form.package_id,
          valid_until: form.valid_until || undefined,
        },
      });
      const email = form.admin_email.trim().toLowerCase();
      const companyName = form.tenant_name.trim();
      setForm({ ...EMPTY_TENANT, package_id: form.package_id });
      if (res.initial_password) {
        setCredentials({
          title: companyName,
          // Platform-provisioned company admins sign in with email (no separate username).
          username: email,
          email,
          initialPassword: res.initial_password,
        });
        setMsg(t("saved") || "Saved");
      } else {
        setMsg(t("saved") || "Saved");
      }
      await load();
    } catch (err) {
      setMsg(formatApiError(err, t("error") || "Could not create company"));
    } finally {
      setSaving(false);
    }
  }

  async function onDeleteCompany(row: MaintenanceCompany) {
    if (!window.confirm(t("delete_company_confirm"))) return;
    setMsg(null);
    try {
      await apiFetch(`/platform/tenants/${row.id}`, { method: "DELETE" });
      setMsg(t("saved") || "Deleted");
      if (expanded === row.id) setExpanded(null);
      await load();
    } catch (err) {
      setMsg(formatApiError(err, t("error") || "Could not delete company"));
    }
  }

  async function onSaveLicense(tenantId: string) {
    const draft = licenseDraft[tenantId];
    if (!draft?.package_id) {
      setMsg("Select a package before saving the license.");
      return;
    }
    setMsg(null);
    try {
      await apiFetch(`/platform/tenants/${tenantId}/license`, {
        method: "PUT",
        json: {
          package_id: draft.package_id,
          status: draft.status || "active",
          valid_until: draft.valid_until || null,
        },
      });
      setMsg(t("saved") || "Saved");
      await load();
    } catch (err) {
      setMsg(formatApiError(err, t("error") || "Could not update license"));
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

      {loadError && (
        <p className="rounded-md border border-error-main/30 bg-error-light px-4 py-3 text-sm text-error-dark">
          {loadError}
        </p>
      )}

      <form onSubmit={onCreateTenant} className="space-y-4 rounded-lg border p-6">
        <h2 className="text-lg font-medium">{t("add_tenant") || "Add maintenance company"}</h2>
        {packages.length === 0 ? (
          <p className="rounded-md border border-warning-main/40 bg-warning-light px-3 py-2 text-sm text-warning-dark">
            No active packages. Run the pilot seed / platform bootstrap, then refresh.
          </p>
        ) : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder="Company name"
            value={form.tenant_name}
            onChange={(e) => setForm({ ...form, tenant_name: e.target.value })}
            required
            data-testid="platform-tenant-name"
          />
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={form.package_id}
            onChange={(e) => setForm({ ...form, package_id: e.target.value })}
            required
            disabled={packages.length === 0}
            data-testid="platform-tenant-package"
          >
            {packages.length === 0 ? (
              <option value="">No packages</option>
            ) : (
              packages.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))
            )}
          </select>
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder="Admin email"
            type="email"
            value={form.admin_email}
            onChange={(e) => setForm({ ...form, admin_email: e.target.value })}
            required
            data-testid="platform-tenant-admin-email"
          />
          <input
            className="rounded-md border px-3 py-2 text-sm"
            placeholder="Admin full name"
            value={form.admin_full_name}
            onChange={(e) => setForm({ ...form, admin_full_name: e.target.value })}
            required
            data-testid="platform-tenant-admin-name"
          />
          <div>
            <label className="mb-1 block text-xs text-neutral-500">{t("trial_ends")}</label>
            <input
              type="date"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={form.valid_until}
              onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
              data-testid="platform-tenant-valid-until"
            />
          </div>
        </div>
        <p className="text-xs text-neutral-500">
          Leave password blank to auto-generate a temporary password (shown in a copyable dialog after save).
        </p>
        <SlideNotice text={msg} />
        <button
          type="submit"
          disabled={saving || packages.length === 0}
          className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white disabled:opacity-50"
          data-testid="platform-tenant-submit"
        >
          {saving ? t("loading") : t("save")}
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
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-neutral-500">
                  No maintenance companies yet. Register one above.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <Fragment key={row.id}>
                  <tr className="hover:bg-neutral-50">
                    <td
                      className="cursor-pointer px-4 py-3 font-medium"
                      onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                    >
                      {row.name}
                    </td>
                    <td
                      className="cursor-pointer px-4 py-3"
                      onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                    >
                      {row.subscription?.plan ?? "—"}
                      {row.subscription?.valid_until
                        ? ` · until ${row.subscription.valid_until.slice(0, 10)}`
                        : ""}
                    </td>
                    <td
                      className="cursor-pointer px-4 py-3"
                      onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                    >
                      {row.client_count}
                    </td>
                    <td
                      className="cursor-pointer px-4 py-3"
                      onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                    >
                      {row.status}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        className="text-sm text-error-main hover:underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          void onDeleteCompany(row);
                        }}
                        data-testid={`platform-tenant-delete-${row.id}`}
                      >
                        {t("delete_company")}
                      </button>
                    </td>
                  </tr>
                  {expanded === row.id && (
                    <tr key={`${row.id}-detail`}>
                      <td colSpan={5} className="bg-neutral-50 px-6 py-4">
                        <div className="grid gap-6 lg:grid-cols-2">
                          <div>
                            <p className="mb-2 text-xs font-semibold uppercase text-neutral-500">
                              {t("end_clients") || "End clients"}
                            </p>
                            {row.clients.length === 0 ? (
                              <p className="text-neutral-500">—</p>
                            ) : (
                              <ul className="space-y-1">
                                {row.clients.map((c) => (
                                  <li key={c.id}>
                                    {c.legal_name}{" "}
                                    <span className="text-neutral-400">({c.code})</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                          <div className="space-y-3 rounded-md border bg-white p-4">
                            <p className="text-sm font-medium">{t("edit_license")}</p>
                            <div>
                              <label className="mb-1 block text-xs text-neutral-500">Package</label>
                              <select
                                className="w-full rounded-md border px-3 py-2 text-sm"
                                value={licenseDraft[row.id]?.package_id || ""}
                                onChange={(e) =>
                                  setLicenseDraft((d) => ({
                                    ...d,
                                    [row.id]: {
                                      ...(d[row.id] || { package_id: "", valid_until: "", status: "active" }),
                                      package_id: e.target.value,
                                    },
                                  }))
                                }
                              >
                                {packages.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    {p.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="mb-1 block text-xs text-neutral-500">{t("trial_ends")}</label>
                              <input
                                type="date"
                                className="w-full rounded-md border px-3 py-2 text-sm"
                                value={licenseDraft[row.id]?.valid_until || ""}
                                onChange={(e) =>
                                  setLicenseDraft((d) => ({
                                    ...d,
                                    [row.id]: {
                                      ...(d[row.id] || { package_id: "", valid_until: "", status: "active" }),
                                      valid_until: e.target.value,
                                    },
                                  }))
                                }
                              />
                            </div>
                            <div>
                              <label className="mb-1 block text-xs text-neutral-500">Status</label>
                              <select
                                className="w-full rounded-md border px-3 py-2 text-sm"
                                value={licenseDraft[row.id]?.status || "active"}
                                onChange={(e) =>
                                  setLicenseDraft((d) => ({
                                    ...d,
                                    [row.id]: {
                                      ...(d[row.id] || { package_id: "", valid_until: "", status: "active" }),
                                      status: e.target.value,
                                    },
                                  }))
                                }
                              >
                                <option value="active">active</option>
                                <option value="trial">trial</option>
                                <option value="suspended">suspended</option>
                                <option value="cancelled">cancelled</option>
                              </select>
                            </div>
                            <button
                              type="button"
                              className="rounded-md bg-primary-600 px-3 py-2 text-sm text-white hover:bg-primary-700"
                              onClick={() => void onSaveLicense(row.id)}
                            >
                              {t("save")}
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      <ProvisionCredentialsModal
        open={Boolean(credentials)}
        title={credentials?.title || t("initial_password")}
        username={credentials?.username || ""}
        email={credentials?.email || ""}
        initialPassword={credentials?.initialPassword || ""}
        onClose={() => setCredentials(null)}
      />
    </div>
  );
}
