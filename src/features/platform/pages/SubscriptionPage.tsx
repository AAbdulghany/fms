import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";

type Package = {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
};

type Tenant = {
  id: string;
  name: string;
  status: string;
};

type Subscription = {
  plan: string;
  package_id?: string | null;
  status: string;
  valid_until?: string | null;
  max_sites: number;
  max_users: number;
  features: string[];
};

export function SubscriptionPage() {
  const { t } = useTranslation();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [tenantId, setTenantId] = useState<string>("");
  const [sub, setSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [tenantRows, packageRows] = await Promise.all([
          apiFetch<Tenant[]>("/platform/tenants"),
          apiFetch<Package[]>("/platform/packages?active_only=true"),
        ]);
        setTenants(tenantRows);
        setPackages(packageRows);
        if (tenantRows.length > 0) setTenantId(tenantRows[0].id);
      } catch {
        setTenants([]);
        setPackages([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    void apiFetch<Subscription>(`/platform/tenants/${tenantId}/license`)
      .then(setSub)
      .catch(() => setSub(null));
  }, [tenantId]);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!tenantId || !sub?.package_id) return;
    setSaving(true);
    setMsg(null);
    try {
      const updated = await apiFetch<Subscription>(`/platform/tenants/${tenantId}/license`, {
        method: "PUT",
        json: {
          package_id: sub.package_id,
          status: sub.status,
          valid_until: sub.valid_until?.slice(0, 10) || null,
        },
      });
      setSub(updated);
      setMsg(t("saved") || "Saved");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("error"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="p-8">{t("loading")}</div>;
  if (!sub) return <div className="p-8 text-error-main">{t("error")}</div>;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-2xl font-semibold">{t("subscription") || "Tenant license"}</h1>
      <form onSubmit={onSave} className="space-y-4 rounded-lg border p-6">
        <div>
          <label className="block text-sm font-medium">{t("tenant") || "Tenant"}</label>
          <select
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
          >
            {tenants.map((tn) => (
              <option key={tn.id} value={tn.id}>
                {tn.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium">{t("plan") || "Package"}</label>
          <select
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            value={sub.package_id || sub.plan}
            onChange={(e) => {
              const pkg = packages.find((p) => p.id === e.target.value || p.code === e.target.value);
              setSub({
                ...sub,
                package_id: pkg?.id ?? e.target.value,
                plan: pkg?.code ?? sub.plan,
              });
            }}
          >
            {packages.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.code})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium">{t("status")}</label>
          <select
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            value={sub.status}
            onChange={(e) => setSub({ ...sub, status: e.target.value })}
          >
            <option value="active">Active</option>
            <option value="trial">Trial</option>
            <option value="suspended">Suspended</option>
            <option value="expired">Expired</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium">{t("valid_until") || "Valid until"}</label>
          <input
            type="date"
            className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            value={sub.valid_until?.slice(0, 10) || ""}
            onChange={(e) => setSub({ ...sub, valid_until: e.target.value || null })}
          />
        </div>
        <div className="rounded-md bg-neutral-50 p-3 text-xs text-neutral-600">
          <div>Features: {sub.features.join(", ") || "—"}</div>
          <div>
            Limits: {sub.max_users} users, {sub.max_sites} sites
          </div>
        </div>
        {msg && <p className="text-sm text-neutral-600">{msg}</p>}
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {t("save")}
        </button>
      </form>
    </div>
  );
}
