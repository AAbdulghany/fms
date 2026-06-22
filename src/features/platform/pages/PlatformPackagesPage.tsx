import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";

type Package = {
  id: string;
  code: string;
  name: string;
  features_json: string[];
  limits_json: Record<string, number>;
  is_active: boolean;
};

const EMPTY_FORM = {
  code: "",
  name: "",
  features_json: "assets,invoices",
  max_users: "10",
  max_sites: "5",
};

export function PlatformPackagesPage() {
  const { t } = useTranslation();
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const rows = await apiFetch<Package[]>("/platform/packages");
      setPackages(rows);
    } catch {
      setPackages([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      await apiFetch<Package>("/platform/packages", {
        method: "POST",
        json: {
          code: form.code.trim().toLowerCase(),
          name: form.name.trim(),
          features_json: form.features_json.split(",").map((s) => s.trim()).filter(Boolean),
          limits_json: {
            max_users: Number(form.max_users) || 10,
            max_sites: Number(form.max_sites) || 5,
          },
        },
      });
      setForm(EMPTY_FORM);
      setMsg(t("saved") || "Saved");
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("error"));
    } finally {
      setSaving(false);
    }
  }

  async function deactivate(id: string) {
    try {
      await apiFetch(`/platform/packages/${id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("error"));
    }
  }

  if (loading) return <div className="p-8">{t("loading")}</div>;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-semibold">{t("platform_packages") || "Subscription packages"}</h1>

      <form onSubmit={onCreate} className="space-y-4 rounded-lg border p-6">
        <h2 className="text-lg font-medium">{t("create_package") || "Create package"}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium">Code</label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Name</label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium">Features (comma-separated)</label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              value={form.features_json}
              onChange={(e) => setForm({ ...form, features_json: e.target.value })}
            />
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

      <div className="overflow-hidden rounded-lg border">
        <table className="min-w-full divide-y divide-neutral-200 text-sm">
          <thead className="bg-neutral-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Code</th>
              <th className="px-4 py-2 text-left font-medium">Name</th>
              <th className="px-4 py-2 text-left font-medium">Features</th>
              <th className="px-4 py-2 text-left font-medium">Active</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {packages.map((p) => (
              <tr key={p.id}>
                <td className="px-4 py-2 font-mono">{p.code}</td>
                <td className="px-4 py-2">{p.name}</td>
                <td className="px-4 py-2 text-neutral-600">{p.features_json.join(", ")}</td>
                <td className="px-4 py-2">{p.is_active ? "Yes" : "No"}</td>
                <td className="px-4 py-2 text-right">
                  {p.is_active && (
                    <button
                      type="button"
                      onClick={() => void deactivate(p.id)}
                      className="text-sm text-error-main hover:underline"
                    >
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
