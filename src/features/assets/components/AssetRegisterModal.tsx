import { FormEvent, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { AssetCriticality, User, UserRole } from "@/lib/types";

type SiteRow = { id: string; name: string; client_id: string; company_name?: string | null };
type TemplateRow = { id: string; name: string };
type ClientRow = { id: string; legal_name: string };

const PICK_CLIENT_ROLES = new Set<UserRole>([
  "company_admin",
  "company_engineer",
  "super_admin",
  "super_user",
  "sw_dev",
]);

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  initialSiteId?: string;
  initialClientId?: string;
};

export function AssetRegisterModal({
  open,
  onClose,
  onCreated,
  initialSiteId,
  initialClientId,
}: Props) {
  const { t } = useTranslation();
  const [me, setMe] = useState<User | null>(null);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [sites, setSites] = useState<SiteRow[]>([]);
  const [templates, setTemplates] = useState<TemplateRow[]>([]);
  const [clientId, setClientId] = useState(initialClientId || "");
  const [siteId, setSiteId] = useState(initialSiteId || "");
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
  const [isSpare, setIsSpare] = useState(false);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [frequency, setFrequency] = useState("monthly");
  const [templateId, setTemplateId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentAgeYears = installedOn
    ? Math.max(0, (Date.now() - new Date(installedOn).getTime()) / (365.25 * 24 * 3600 * 1000))
    : null;

  const canPickClient = me ? PICK_CLIENT_ROLES.has(me.role) : false;
  const lockedClientId =
    me?.role === "client_admin" && me.client_id ? me.client_id : null;

  const siteOptions = useMemo(() => {
    if (canPickClient && clientId) {
      return sites.filter((s) => s.client_id === clientId);
    }
    return sites;
  }, [canPickClient, clientId, sites]);

  const lockedClient = useMemo(() => {
    const id = lockedClientId || (canPickClient ? null : clientId);
    if (!id) return null;
    const fromClients = clients.find((c) => c.id === id);
    if (fromClients) return fromClients;
    const fromSite = sites.find((s) => s.client_id === id);
    if (fromSite) {
      return { id, legal_name: fromSite.company_name || id.slice(0, 8) };
    }
    return null;
  }, [lockedClientId, canPickClient, clientId, clients, sites]);

  const showClientPicker = canPickClient && clients.length > 1;
  const showLockedClient = !canPickClient || clients.length === 1;
  const showSitePicker = siteOptions.length !== 1;

  useEffect(() => {
    if (!open) return;
    setSiteId(initialSiteId || "");
    setClientId(initialClientId || "");
    void (async () => {
      try {
        const user = await apiFetch<User>("/users/me");
        setMe(user);
        const tmplData = await apiFetch<TemplateRow[]>("/report-templates");
        setTemplates(tmplData);

        if (PICK_CLIENT_ROLES.has(user.role)) {
          const clientData = await apiFetch<ClientRow[]>("/clients");
          setClients(clientData);
          const cid = initialClientId || (clientData.length === 1 ? clientData[0].id : "");
          setClientId(cid);
          const siteUrl = cid ? `/sites?client_id=${cid}` : "/sites";
          const siteData = await apiFetch<SiteRow[]>(siteUrl);
          setSites(siteData);
          if (initialSiteId) {
            setSiteId(initialSiteId);
          } else if (siteData.length === 1) {
            setSiteId(siteData[0].id);
          }
        } else {
          const siteData = await apiFetch<SiteRow[]>("/sites");
          setSites(siteData);
          if (user.role === "client_admin" && user.client_id) {
            setClientId(user.client_id);
          } else if (siteData.length === 1) {
            setClientId(siteData[0].client_id);
            setSiteId(initialSiteId || siteData[0].id);
          }
          if (user.client_id) {
            try {
              const clientData = await apiFetch<ClientRow[]>("/clients");
              setClients(clientData);
            } catch {
              setClients([]);
            }
          }
        }
      } catch {
        setSites([]);
        setClients([]);
        setTemplates([]);
      }
    })();
  }, [open, initialSiteId, initialClientId]);

  useEffect(() => {
    if (!open || !canPickClient || !clientId) return;
    void apiFetch<SiteRow[]>(`/sites?client_id=${clientId}`).then((siteData) => {
      setSites(siteData);
      if (initialSiteId && siteData.some((s) => s.id === initialSiteId)) {
        setSiteId(initialSiteId);
      } else if (siteData.length === 1) {
        setSiteId(siteData[0].id);
      } else {
        setSiteId("");
      }
    });
  }, [open, canPickClient, clientId, initialSiteId]);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const effectiveClientId = lockedClientId || clientId || lockedClient?.id;
    const effectiveSiteId =
      siteId || (siteOptions.length === 1 ? siteOptions[0].id : "");

    if (!effectiveSiteId) {
      setError(t("select_site"));
      return;
    }
    if (canPickClient && !effectiveClientId) {
      setError(t("select_company"));
      return;
    }
    if (scheduleEnabled && !templateId) {
      setError(t("template_required"));
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const smartLabelsArr = smartLabels
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await apiFetch("/assets", {
        method: "POST",
        json: {
          site_id: effectiveSiteId,
          name: name.trim(),
          category: category.trim() || "general",
          model: model.trim() || undefined,
          serial: serial.trim() || undefined,
          floor: floor.trim() || undefined,
          room: room.trim() || undefined,
          smart_labels: smartLabelsArr.length ? smartLabelsArr : undefined,
          criticality: criticality || undefined,
          warranty_until: warrantyUntil || undefined,
          last_maintenance_date: lastMaintenanceDate || undefined,
          installed_on: installedOn || undefined,
          max_age_years: maxAgeYears,
          is_spare: isSpare,
          schedule: scheduleEnabled
            ? { template_id: templateId, frequency }
            : undefined,
        },
      });
      setName("");
      setModel("");
      setSerial("");
      setFloor("");
      setRoom("");
      setSmartLabels("");
      setCriticality("");
      setWarrantyUntil("");
      setLastMaintenanceDate("");
      setInstalledOn("");
      setMaxAgeYears(5);
      setIsSpare(false);
      setScheduleEnabled(false);
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  const displayClient =
    lockedClient ||
    (clients.length === 1 ? clients[0] : null) ||
    (clientId ? clients.find((c) => c.id === clientId) : null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl">
        <h2 className="mb-4 text-xl font-bold">{t("register_asset")}</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          {showClientPicker && (
            <div>
              <label className="mb-1 block text-sm font-medium">{t("company")} *</label>
              <select
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
              >
                <option value="">{t("select_company")}</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.legal_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {showLockedClient && displayClient && (
            <div>
              <label className="mb-1 block text-sm font-medium">{t("company")}</label>
              <input
                readOnly
                className="w-full rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm"
                value={displayClient.legal_name}
              />
            </div>
          )}

          {showSitePicker ? (
            <div>
              <label className="mb-1 block text-sm font-medium">{t("site")} *</label>
              <select
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                disabled={canPickClient && !clientId && clients.length > 1}
              >
                <option value="">{t("select_site")}</option>
                {siteOptions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            siteOptions[0] && (
              <div>
                <label className="mb-1 block text-sm font-medium">{t("site")}</label>
                <input
                  readOnly
                  className="w-full rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm"
                  value={siteOptions[0].name}
                />
              </div>
            )
          )}

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
                placeholder="N/A"
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
          {currentAgeYears !== null && (
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-500">{t("current_age")}</label>
              <input
                readOnly
                className="w-full rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-700"
                value={`${currentAgeYears.toFixed(1)} ${t("years")}`}
              />
            </div>
          )}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={isSpare}
              onChange={(e) => setIsSpare(e.target.checked)}
              className="h-4 w-4 rounded border-neutral-300 text-primary-600"
            />
            {t("spare_device") || "Spare device (swap-out maintenance)"}
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={scheduleEnabled}
              onChange={(e) => setScheduleEnabled(e.target.checked)}
            />
            {t("enable_maintenance_schedule")}
          </label>
          {scheduleEnabled && (
            <div className="space-y-3 rounded-lg border border-neutral-200 p-3">
              <div>
                <label className="mb-1 block text-sm">{t("frequency")}</label>
                <select
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                >
                  <option value="monthly">{t("frequency_monthly")}</option>
                  <option value="quarterly">{t("frequency_quarterly")}</option>
                  <option value="yearly">{t("frequency_yearly")}</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm">{t("report_template")}</label>
                <select
                  required
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={templateId}
                  onChange={(e) => setTemplateId(e.target.value)}
                >
                  <option value="">{t("select_template")}</option>
                  {templates.map((tm) => (
                    <option key={tm.id} value={tm.id}>
                      {tm.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
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
              {t("create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
