import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import type { AssetCriticality, AssetLifecycleStatus } from "../lib/types";

type AssetOutApi = {
  id: string;
  site_id: string;
  name: string;
  category: string;
  model?: string | null;
  serial?: string | null;
  floor?: string | null;
  room?: string | null;
  smart_labels?: string[] | null;
  criticality?: AssetCriticality | null;
  warranty_until?: string | null;
  last_maintenance_date?: string | null;
  installed_on?: string | null;
  max_age_years?: number | null;
  lifecycle_status?: AssetLifecycleStatus | null;
  is_spare?: boolean | null;
};

type Props = {
  open: boolean;
  assetId: string;
  onClose: () => void;
  onSaved: () => void;
};

export function AssetEditModal({ open, assetId, onClose, onSaved }: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [category, setCategory] = useState("general");
  const [model, setModel] = useState("");
  const [serial, setSerial] = useState("");
  const [floor, setFloor] = useState("");
  const [room, setRoom] = useState("");
  const [smartLabels, setSmartLabels] = useState("");
  const [criticality, setCriticality] = useState<AssetCriticality | "">("");
  const [warrantyUntil, setWarrantyUntil] = useState("");
  const [lastMaintenanceDate, setLastMaintenanceDate] = useState("");
  const [installedOn, setInstalledOn] = useState("");
  const [maxAgeYears, setMaxAgeYears] = useState(5);
  const [lifecycleStatus, setLifecycleStatus] = useState<AssetLifecycleStatus | "">("");
  const [isSpare, setIsSpare] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !assetId) return;
    setFetchLoading(true);
    void apiFetch<AssetOutApi>(`/assets/${assetId}`)
      .then((a) => {
        setName(a.name || "");
        setCategory(a.category || "general");
        setModel(a.model || "");
        setSerial(a.serial || "");
        setFloor(a.floor || "");
        setRoom(a.room || "");
        setSmartLabels(a.smart_labels ? a.smart_labels.join(", ") : "");
        setCriticality((a.criticality as AssetCriticality | "") || "");
        setWarrantyUntil(a.warranty_until ? a.warranty_until.slice(0, 10) : "");
        setLastMaintenanceDate(
          a.last_maintenance_date ? a.last_maintenance_date.slice(0, 10) : ""
        );
        setInstalledOn(a.installed_on ? a.installed_on.slice(0, 10) : "");
        setMaxAgeYears(a.max_age_years ?? 5);
        setLifecycleStatus((a.lifecycle_status as AssetLifecycleStatus | "") || "");
        setIsSpare(a.is_spare ?? false);
      })
      .catch(() => setError(t("error")))
      .finally(() => setFetchLoading(false));
  }, [open, assetId, t]);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const smartLabelsArr = smartLabels
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await apiFetch(`/assets/${assetId}`, {
        method: "PATCH",
        json: {
          name: name.trim(),
          category: category.trim() || "general",
          model: model.trim() || null,
          serial: serial.trim() || null,
          floor: floor.trim() || null,
          room: room.trim() || null,
          smart_labels: smartLabelsArr.length ? smartLabelsArr : null,
          criticality: criticality || null,
          warranty_until: warrantyUntil || null,
          last_maintenance_date: lastMaintenanceDate || null,
          installed_on: installedOn || null,
          max_age_years: maxAgeYears,
          lifecycle_status: lifecycleStatus || null,
          is_spare: isSpare,
        },
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl">
        <h2 className="mb-4 text-xl font-bold">{t("edit_asset")}</h2>
        {fetchLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">{t("name")} *</label>
              <input
                required
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("category")}</label>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("serial_number")}</label>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={serial}
                onChange={(e) => setSerial(e.target.value)}
                placeholder={t("optional")}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium">{t("floor")}</label>
                <input
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={floor}
                  onChange={(e) => setFloor(e.target.value)}
                  placeholder={t("optional")}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">{t("room")}</label>
                <input
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={room}
                  onChange={(e) => setRoom(e.target.value)}
                  placeholder={t("optional")}
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("model")}</label>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={t("optional")}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("criticality")}</label>
              <select
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={criticality}
                onChange={(e) => setCriticality(e.target.value as AssetCriticality | "")}
              >
                <option value="">{t("optional")}</option>
                <option value="low">{t("criticality_low")}</option>
                <option value="medium">{t("criticality_medium")}</option>
                <option value="high">{t("criticality_high")}</option>
                <option value="critical">{t("criticality_critical")}</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("lifecycle_status")}</label>
              <select
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-100 disabled:text-neutral-400"
                value={lifecycleStatus}
                onChange={(e) => setLifecycleStatus(e.target.value as AssetLifecycleStatus | "")}
                disabled={lifecycleStatus === "replaced"}
                aria-label={t("lifecycle_status")}
              >
                <option value="">{t("optional")}</option>
                <option value="active">{t("lifecycle_active")}</option>
                <option value="warning">{t("lifecycle_warning")}</option>
                <option value="end_of_life">{t("lifecycle_end_of_life")}</option>
                <option value="replaced" disabled>{t("lifecycle_replaced")}</option>
              </select>
              {lifecycleStatus === "replaced" && (
                <p className="mt-0.5 text-xs text-neutral-500">{t("lifecycle_replaced_locked") || "Status locked — asset is retired / out of service."}</p>
              )}
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={isSpare}
                onChange={(e) => setIsSpare(e.target.checked)}
                className="h-4 w-4 rounded border-neutral-300 text-primary-600"
              />
              {t("spare_device") || "Spare device (swap-out maintenance)"}
            </label>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("smart_labels")}</label>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={smartLabels}
                onChange={(e) => setSmartLabels(e.target.value)}
                placeholder={t("smart_labels_placeholder")}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium">{t("warranty_date")}</label>
                <input
                  type="date"
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={warrantyUntil}
                  onChange={(e) => setWarrantyUntil(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">{t("last_maintenance_date")}</label>
                <input
                  type="date"
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={lastMaintenanceDate}
                  onChange={(e) => setLastMaintenanceDate(e.target.value)}
                />
                <p className="mt-0.5 text-xs text-neutral-500">{t("last_maintenance_date_hint")}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium">{t("installation_date")}</label>
                <input
                  type="date"
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={installedOn}
                  onChange={(e) => setInstalledOn(e.target.value)}
                  max={new Date().toISOString().slice(0, 10)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">{t("max_age_years")}</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={maxAgeYears}
                  onChange={(e) => setMaxAgeYears(Math.max(1, Number(e.target.value)))}
                />
              </div>
            </div>
            {error && <p className="text-sm text-error-main">{error}</p>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="rounded-md px-4 py-2 text-sm hover:bg-neutral-100"
                onClick={onClose}
              >
                {t("cancel")}
              </button>
              <button
                type="submit"
                disabled={loading}
                className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                {loading ? t("loading") : t("save")}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
