import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";

type SiteRow = { id: string; name: string; client_id: string };

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  initialSiteId?: string;
};

export function AssetRegisterModal({ open, onClose, onCreated, initialSiteId }: Props) {
  const { t } = useTranslation();
  const [sites, setSites] = useState<SiteRow[]>([]);
  const [siteId, setSiteId] = useState(initialSiteId || "");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("general");
  const [model, setModel] = useState("");
  const [serial, setSerial] = useState("");
  const [installedOn, setInstalledOn] = useState("");
  const [warrantyUntil, setWarrantyUntil] = useState("");
  const [maxRepair, setMaxRepair] = useState("3");
  const [maxAge, setMaxAge] = useState("5");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setSiteId(initialSiteId || "");
    void (async () => {
      try {
        const data = await apiFetch<SiteRow[]>("/sites");
        setSites(data);
      } catch {
        setSites([]);
      }
    })();
  }, [open, initialSiteId]);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!siteId) {
      setError(t("select_site"));
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await apiFetch("/assets", {
        method: "POST",
        json: {
          site_id: siteId,
          name: name.trim(),
          category: category.trim() || "general",
          model: model.trim() || undefined,
          serial: serial.trim() || undefined,
          installed_on: installedOn || undefined,
          warranty_until: warrantyUntil || undefined,
          max_repair_count: maxRepair ? parseInt(maxRepair, 10) : undefined,
          max_age_years: maxAge ? parseInt(maxAge, 10) : undefined,
        },
      });
      setName("");
      setModel("");
      setSerial("");
      setInstalledOn("");
      setWarrantyUntil("");
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("register_asset")}</h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site")} *</label>
            <select
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={siteId}
              onChange={(e) => setSiteId(e.target.value)}
              disabled={Boolean(initialSiteId)}
            >
              <option value="">{t("select_site")}</option>
              {sites.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("asset_name")} *</label>
            <input
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("asset_category")}</label>
              <input
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("model")}</label>
              <input
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("serial_number")}</label>
            <input
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={serial}
              onChange={(e) => setSerial(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("installation_date")}</label>
              <input
                type="date"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={installedOn}
                onChange={(e) => setInstalledOn(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("warranty_until")}</label>
              <input
                type="date"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={warrantyUntil}
                onChange={(e) => setWarrantyUntil(e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("repair_count")} (max)</label>
              <input
                type="number"
                min={1}
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={maxRepair}
                onChange={(e) => setMaxRepair(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("expected_lifespan")}</label>
              <input
                type="number"
                min={1}
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={maxAge}
                onChange={(e) => setMaxAge(e.target.value)}
              />
            </div>
          </div>
          {error && <p className="text-sm text-error-main">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100" onClick={onClose}>
              {t("cancel")}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? t("loading") : t("create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
