import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiFetch } from "@/lib/api";
import { LocationTree, type LocationTreeNode } from "@/components/LocationTree";

interface SiteRow {
  id: string;
  client_id: string;
  name: string;
}

export default function LocationsPage() {
  const { t } = useTranslation();
  const [sites, setSites] = useState<SiteRow[]>([]);
  const [siteId, setSiteId] = useState("");
  const [tree, setTree] = useState<LocationTreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const rows = await apiFetch<SiteRow[]>("/sites");
        setSites(rows);
        if (rows.length && !siteId) {
          setSiteId(rows[0].id);
        }
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!siteId) return;
    void (async () => {
      try {
        const data = await apiFetch<LocationTreeNode[]>(`/locations/tree?site_id=${siteId}`);
        setTree(data);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error");
      }
    })();
  }, [siteId]);

  if (loading) {
    return (
      <div className="flex min-h-[240px] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-neutral-900">{t("locations")}</h1>
      {err && <p className="text-sm text-error-main">{err}</p>}

      <div className="max-w-md">
        <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site")}</label>
        <select
          className="w-full rounded-md border border-neutral-300 px-3 py-2"
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
        >
          {sites.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      <LocationTree nodes={tree} />
    </div>
  );
}
