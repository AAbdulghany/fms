import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { AssetCriticality, AssetType, User, UserRole } from "@/lib/types";
import { AssetTypePicker } from "@/features/assets/components/AssetTypePicker";
import { localizedName } from "@/features/assets/hooks/useAssetTypes";
import { useVerticals, verticalName } from "@/shared/hooks/useVerticals";

function hasTypeDefaults(ty: AssetType): boolean {
  return (
    ty.default_max_age_years != null ||
    ty.default_criticality != null ||
    ty.default_frequency != null
  );
}

type SiteRow = { id: string; name: string; client_id: string; company_name?: string | null };
type TemplateRow = { id: string; name: string };
type ClientRow = { id: string; legal_name: string; vertical_code?: string | null };

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
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const [me, setMe] = useState<User | null>(null);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [sites, setSites] = useState<SiteRow[]>([]);
  const [templates, setTemplates] = useState<TemplateRow[]>([]);
  const [assetTypes, setAssetTypes] = useState<AssetType[]>([]);
  const [assetTypesLoading, setAssetTypesLoading] = useState(false);
  const { verticals } = useVerticals(open);

  const [clientId, setClientId] = useState(initialClientId || "");
  const [siteId, setSiteId] = useState(initialSiteId || "");
  const [name, setName] = useState("");

  // A1: type picker state
  const [assetTypeId, setAssetTypeId] = useState("");
  const [freeTextCategory, setFreeTextCategory] = useState("general");

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

  // A1: track which lifecycle fields the user has explicitly touched
  const touched = useRef<Set<string>>(new Set());

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

  // Effective client for vertical lookups
  const effectiveClientId =
    lockedClientId ||
    clientId ||
    lockedClient?.id ||
    (clients.length === 1 ? clients[0].id : "");
  const effectiveClient = clients.find((c) => c.id === effectiveClientId);

  // ── Load asset types whenever effective client changes ──────────────────
  useEffect(() => {
    if (!open) return;
    setAssetTypesLoading(true);
    const url = effectiveClientId
      ? `/asset-types?client_id=${encodeURIComponent(effectiveClientId)}`
      : "/asset-types";
    void apiFetch<AssetType[]>(url)
      .then(setAssetTypes)
      .catch(() => setAssetTypes([]))
      .finally(() => setAssetTypesLoading(false));
  }, [open, effectiveClientId]);

  // ── Prefill lifecycle defaults when asset type changes ──────────────────
  useEffect(() => {
    if (!assetTypeId) return;
    const ty = assetTypes.find((t) => t.id === assetTypeId);
    if (!ty) return;

    if (!touched.current.has("maxAgeYears") && ty.default_max_age_years != null) {
      setMaxAgeYears(ty.default_max_age_years);
    }
    if (!touched.current.has("criticality") && ty.default_criticality != null) {
      setCriticality(ty.default_criticality as AssetCriticality);
    }
    if (!touched.current.has("frequency") && ty.default_frequency != null) {
      setFrequency(ty.default_frequency);
    }
    const tplKnown =
      ty.default_report_template_id != null &&
      templates.some((tm) => tm.id === ty.default_report_template_id);
    if (!touched.current.has("templateId") && tplKnown) {
      setTemplateId(ty.default_report_template_id as string);
    }
    // Schedule section is pre-filled only when the type supplies both values.
    // The client still sends `schedule` explicitly; the user can switch it off.
    if (
      !touched.current.has("scheduleEnabled") &&
      ty.default_frequency != null &&
      tplKnown
    ) {
      setScheduleEnabled(true);
    }
  }, [assetTypeId, assetTypes, templates]);

  // ── Initial load (me, templates, clients, sites) ────────────────────────
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

  function resetForm() {
    setName("");
    setAssetTypeId("");
    setFreeTextCategory("general");
    touched.current = new Set();
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
    setFrequency("monthly");
    setTemplateId("");
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const eff = lockedClientId || clientId || lockedClient?.id;
    const effSiteId = siteId || (siteOptions.length === 1 ? siteOptions[0].id : "");

    if (!effSiteId) {
      setError(t("select_site"));
      return;
    }
    if (canPickClient && !eff) {
      setError(t("select_company"));
      return;
    }
    if (scheduleEnabled && !templateId) {
      setError(t("template_required"));
      return;
    }
    // Require asset type when library is non-empty
    if (assetTypes.length > 0 && !assetTypeId) {
      setError(t("select_asset_type"));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const smartLabelsArr = smartLabels
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const body: Record<string, unknown> = {
        site_id: effSiteId,
        name: name.trim(),
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
        schedule: scheduleEnabled ? { template_id: templateId, frequency } : undefined,
      };

      // A1: prefer asset_type_id; fall back to free-text category for pre-backfill tenants
      if (assetTypeId) {
        body.asset_type_id = assetTypeId;
      } else {
        body.category = freeTextCategory.trim() || "general";
      }

      await apiFetch("/assets", { method: "POST", json: body });
      resetForm();
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

  // Vertical label for the "Recommended for …" optgroup
  const vertical = verticals.find((v) => v.code === effectiveClient?.vertical_code);
  const verticalLabel = vertical
    ? verticalName(vertical, lang)
    : (effectiveClient?.vertical_code ?? undefined);
  const selectedType = assetTypes.find((ty) => ty.id === assetTypeId);

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

          {/* ── A1: Asset Type Picker ──────────────────────────────────── */}
          <div>
            <label className="mb-1 block text-sm font-medium">{t("asset_type")} *</label>
            <AssetTypePicker
              types={assetTypes}
              value={assetTypeId}
              onChange={(id) => {
                setAssetTypeId(id);
              }}
              loading={assetTypesLoading}
              userRole={me?.role}
              verticalLabel={verticalLabel}
              freeTextCategory={freeTextCategory}
              onFreeTextChange={setFreeTextCategory}
              required
            />
            {selectedType && hasTypeDefaults(selectedType) && (
              <p className="mt-1 text-xs text-neutral-500">
                {t("type_defaults_applied", { name: localizedName(selectedType, lang) })}
              </p>
            )}
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
              onChange={(e) => {
                touched.current.add("criticality");
                setCriticality(e.target.value as AssetCriticality | "");
              }}
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
                onChange={(e) => {
                  touched.current.add("maxAgeYears");
                  setMaxAgeYears(Math.max(1, Number(e.target.value)));
                }}
              />
            </div>
          </div>
          {currentAgeYears !== null && (
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-500">
                {t("current_age")}
              </label>
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
            {t("spare_device")}
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={scheduleEnabled}
              onChange={(e) => {
                touched.current.add("scheduleEnabled");
                setScheduleEnabled(e.target.checked);
              }}
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
                  onChange={(e) => {
                    touched.current.add("frequency");
                    setFrequency(e.target.value);
                  }}
                >
                  <option value="daily">{t("frequency_daily")}</option>
                  <option value="weekly">{t("frequency_weekly")}</option>
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
                  onChange={(e) => {
                    touched.current.add("templateId");
                    setTemplateId(e.target.value);
                  }}
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
              {loading ? t("loading") : t("create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
