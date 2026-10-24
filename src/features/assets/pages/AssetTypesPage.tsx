/**
 * A1 — Asset Types Library page.
 * Route: /asset-types
 * Guard: company_admin / super_admin only (FeatureRoute "assets").
 *
 * Two tabs:
 *  1. My Types — tenant library: list, origin badges, archive/restore.
 *  2. Catalog — browse platform templates, filter by vertical, adopt.
 */
import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { AssetType, AssetTypeTemplate, Vertical } from "@/lib/types";
import { localizedName } from "@/features/assets/hooks/useAssetTypes";

// ── Origin badge ─────────────────────────────────────────────────────────────
function OriginBadge({ origin }: { origin: AssetType["origin"] }) {
  const { t } = useTranslation();
  const map: Record<AssetType["origin"], { label: string; cls: string }> = {
    catalog: { label: t("origin_catalog"), cls: "bg-primary-100 text-primary-700" },
    custom: { label: t("origin_custom"), cls: "bg-emerald-100 text-emerald-700" },
    legacy: { label: t("origin_legacy"), cls: "bg-neutral-200 text-neutral-600" },
  };
  const { label, cls } = map[origin] ?? map.legacy;
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

// ── Inline archive confirm ────────────────────────────────────────────────────
function ArchiveConfirm({
  name,
  onConfirm,
  onCancel,
}: {
  name: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  return (
    <span className="flex items-center gap-2 text-sm">
      <span className="text-neutral-600">
        {t("archive_type")} &ldquo;{name}&rdquo;?
      </span>
      <button
        onClick={onConfirm}
        className="rounded bg-error-main px-2 py-0.5 text-xs text-white hover:bg-error-dark"
      >
        {t("confirm")}
      </button>
      <button
        onClick={onCancel}
        className="text-xs text-neutral-500 underline hover:text-neutral-700"
      >
        {t("cancel")}
      </button>
    </span>
  );
}

// ── Create / Edit modal ───────────────────────────────────────────────────────
type TypeFormProps = {
  open: boolean;
  editId?: string | null;
  initialData?: Partial<AssetType>;
  verticals: Vertical[];
  onClose: () => void;
  onSaved: () => void;
};

function TypeFormModal({ open, editId, initialData, verticals, onClose, onSaved }: TypeFormProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const isEdit = Boolean(editId);

  const [nameEn, setNameEn] = useState(initialData?.name_en ?? "");
  const [nameAr, setNameAr] = useState(initialData?.name_ar ?? "");
  const [code, setCode] = useState(initialData?.code ?? "");
  const [maxAge, setMaxAge] = useState<number | "">(initialData?.default_max_age_years ?? "");
  const [maxRepairs, setMaxRepairs] = useState<number | "">(
    initialData?.default_max_repair_count ?? ""
  );
  const [criticality, setCriticality] = useState(initialData?.default_criticality ?? "");
  const [frequency, setFrequency] = useState(initialData?.default_frequency ?? "");
  const [selectedVerticals, setSelectedVerticals] = useState<string[]>(
    initialData?.vertical_codes ?? []
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyPm, setApplyPm] = useState(false);

  useEffect(() => {
    if (open) {
      setNameEn(initialData?.name_en ?? "");
      setNameAr(initialData?.name_ar ?? "");
      setCode(initialData?.code ?? "");
      setMaxAge(initialData?.default_max_age_years ?? "");
      setMaxRepairs(initialData?.default_max_repair_count ?? "");
      setCriticality(initialData?.default_criticality ?? "");
      setFrequency(initialData?.default_frequency ?? "");
      setSelectedVerticals(initialData?.vertical_codes ?? []);
      setApplyPm(false);
      setError(null);
    }
  }, [open, initialData]);

  if (!open) return null;

  function toggleVertical(code: string) {
    setSelectedVerticals((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = {
        name_en: nameEn.trim(),
        name_ar: nameAr.trim(),
        ...(!isEdit ? { code: code.trim() } : {}),
        default_max_age_years: maxAge === "" ? null : Number(maxAge),
        default_max_repair_count: maxRepairs === "" ? null : Number(maxRepairs),
        default_criticality: criticality || null,
        default_frequency: frequency || null,
        vertical_codes: selectedVerticals,
      };
      if (isEdit) {
        const qs = applyPm ? "?apply_schedules=true" : "";
        await apiFetch(`/asset-types/${editId}${qs}`, { method: "PATCH", json: body });
      } else {
        await apiFetch("/asset-types", { method: "POST", json: body });
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  const vLabel = (v: Vertical) => (lang.startsWith("ar") ? v.name_ar : v.name_en);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl"
        data-testid="asset-type-form-modal"
      >
        <h2 className="mb-4 text-xl font-bold">
          {isEdit ? t("edit") : t("custom_type")} — {t("asset_type")}
        </h2>
        <form onSubmit={onSubmit} className="space-y-4">
          {!isEdit && (
            <div>
              <label className="mb-1 block text-sm font-medium">
                {t("template_code")} *
              </label>
              <input
                required
                data-testid="asset-type-code"
                className="w-full rounded-md border px-3 py-2 text-sm font-mono"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. hvac_chiller"
                pattern="[A-Za-z0-9][A-Za-z0-9 _\-]*"
              />
              <p className="mt-0.5 text-xs text-neutral-500">
                Immutable slug. Lowercase, no spaces preferred.
              </p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">
                {t("name")} (EN) *
              </label>
              <input
                required
                data-testid="asset-type-name-en"
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                placeholder="e.g. Chiller"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                {t("name")} (AR) *
              </label>
              <input
                required
                dir="rtl"
                data-testid="asset-type-name-ar"
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={nameAr}
                onChange={(e) => setNameAr(e.target.value)}
                placeholder="مثال: مبرد"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">{t("max_age_years")}</label>
              <input
                type="number"
                min={1}
                max={100}
                data-testid="asset-type-max-age"
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={maxAge}
                onChange={(e) => setMaxAge(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder={t("optional")}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("max_repairs_label")}</label>
              <input
                type="number"
                min={0}
                max={1000}
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={maxRepairs}
                onChange={(e) =>
                  setMaxRepairs(e.target.value === "" ? "" : Number(e.target.value))
                }
                placeholder={t("optional")}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">{t("criticality")}</label>
              <select
                data-testid="asset-type-criticality"
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={criticality}
                onChange={(e) => setCriticality(e.target.value)}
              >
                <option value="">{t("optional")}</option>
                <option value="low">{t("criticality_low")}</option>
                <option value="medium">{t("criticality_medium")}</option>
                <option value="high">{t("criticality_high")}</option>
                <option value="critical">{t("criticality_critical")}</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">{t("frequency")}</label>
              <select
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
              >
                <option value="">{t("optional")}</option>
                <option value="monthly">{t("frequency_monthly")}</option>
                <option value="quarterly">{t("frequency_quarterly")}</option>
                <option value="semi_annual">{t("frequency_semi_annual")}</option>
                <option value="yearly">{t("frequency_yearly")}</option>
              </select>
            </div>
          </div>

          {isEdit && (
            <label className="flex items-start gap-2 text-sm text-neutral-800">
              <input
                type="checkbox"
                className="mt-1"
                checked={applyPm}
                onChange={(e) => setApplyPm(e.target.checked)}
              />
              <span>
                <span className="font-medium">{t("apply_pm_schedules")}</span>
                <span className="mt-0.5 block text-xs text-neutral-500">
                  {t("apply_pm_schedules_help")}
                </span>
              </span>
            </label>
          )}

          {verticals.length > 0 && (
            <div>
              <label className="mb-2 block text-sm font-medium">{t("vertical")}</label>
              <div className="flex flex-wrap gap-2">
                {verticals.map((v) => {
                  const sel = selectedVerticals.includes(v.code);
                  return (
                    <button
                      key={v.code}
                      type="button"
                      onClick={() => toggleVertical(v.code)}
                      className={[
                        "rounded-full border px-3 py-1 text-xs transition-all",
                        sel
                          ? "border-primary-600 bg-primary-100 text-primary-700"
                          : "border-neutral-300 bg-white text-neutral-600 hover:border-primary-400",
                      ].join(" ")}
                    >
                      {vLabel(v)}
                    </button>
                  );
                })}
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
              data-testid="asset-type-form-submit"
              disabled={loading}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white disabled:opacity-50"
            >
              {loading ? t("loading") : t("save")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function AssetTypesPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const [tab, setTab] = useState<"library" | "catalog">("library");

  // Library
  const [types, setTypes] = useState<AssetType[]>([]);
  const [libLoading, setLibLoading] = useState(false);
  const [includeInactive, setIncludeInactive] = useState(false);
  const [archiveConfirmId, setArchiveConfirmId] = useState<string | null>(null);
  const [editType, setEditType] = useState<AssetType | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Catalog
  const [templates, setTemplates] = useState<AssetTypeTemplate[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [selectedTemplateIds, setSelectedTemplateIds] = useState<string[]>([]);
  const [adoptLoading, setAdoptLoading] = useState(false);
  const [adoptResult, setAdoptResult] = useState<string | null>(null);

  // Shared
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [filterVertical, setFilterVertical] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Load verticals once
  useEffect(() => {
    void apiFetch<Vertical[]>("/verticals")
      .then(setVerticals)
      .catch(() => setVerticals([]));
  }, []);

  // Load library
  function loadLibrary() {
    setLibLoading(true);
    const url = includeInactive ? "/asset-types?include_inactive=true" : "/asset-types";
    void apiFetch<AssetType[]>(url)
      .then(setTypes)
      .catch(() => setTypes([]))
      .finally(() => setLibLoading(false));
  }

  useEffect(() => {
    loadLibrary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeInactive]);

  // Load catalog when tab is selected
  useEffect(() => {
    if (tab !== "catalog") return;
    setCatalogLoading(true);
    const url = filterVertical
      ? `/asset-type-catalog?vertical=${encodeURIComponent(filterVertical)}`
      : "/asset-type-catalog";
    void apiFetch<AssetTypeTemplate[]>(url)
      .then(setTemplates)
      .catch(() => setTemplates([]))
      .finally(() => setCatalogLoading(false));
  }, [tab, filterVertical]);

  async function archiveType(id: string, restore = false) {
    await apiFetch(`/asset-types/${id}`, {
      method: "PATCH",
      json: { is_active: restore },
    });
    setArchiveConfirmId(null);
    loadLibrary();
  }

  async function adoptSelected() {
    if (selectedTemplateIds.length === 0) return;
    setAdoptLoading(true);
    setAdoptResult(null);
    try {
      const res = await apiFetch<{
        created: AssetType[];
        skipped: { template_id: string; reason: string }[];
      }>("/asset-types/adopt", {
        method: "POST",
        json: { template_ids: selectedTemplateIds },
      });
      const newCount = res.created.length;
      const skipCount = res.skipped.length;
      setAdoptResult(
        t("adopt_result", { created: newCount, skipped: skipCount }) ||
          `Adopted ${newCount} type(s). ${skipCount} already existed.`
      );
      setSelectedTemplateIds([]);
      // Refresh the catalog so adopted flag updates
      const url = filterVertical
        ? `/asset-type-catalog?vertical=${encodeURIComponent(filterVertical)}`
        : "/asset-type-catalog";
      void apiFetch<AssetTypeTemplate[]>(url)
        .then(setTemplates)
        .catch(() => null);
    } catch (err) {
      setAdoptResult(err instanceof Error ? err.message : t("error"));
    } finally {
      setAdoptLoading(false);
    }
  }

  function toggleTemplate(id: string) {
    setSelectedTemplateIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  // Filtered library
  const filteredTypes = types.filter((ty) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      ty.name_en.toLowerCase().includes(q) ||
      ty.name_ar.toLowerCase().includes(q) ||
      ty.code.toLowerCase().includes(q);
    const matchesVertical =
      !filterVertical || ty.vertical_codes.includes(filterVertical);
    return matchesSearch && matchesVertical;
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">{t("asset_types")}</h1>
          <p className="mt-1 text-sm text-neutral-500">{t("asset_types_page_desc")}</p>
        </div>
        {tab === "library" && (
          <div className="flex flex-wrap gap-2">
            {import.meta.env.DEV && (
              <button
                type="button"
                data-testid="asset-type-archive-all"
                title="Dev only — wipe library during local setup"
                className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 hover:bg-amber-100"
                onClick={() => {
                  if (!window.confirm(t("archive_all_types_confirm"))) return;
                  void apiFetch<{ archived: number }>("/asset-types/archive-all", {
                    method: "POST",
                  }).then(() => loadLibrary());
                }}
              >
                {t("archive_all_types")} (DEV)
              </button>
            )}
            <button
              data-testid="asset-type-create-button"
              onClick={() => setShowCreateModal(true)}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            >
              + {t("custom_type")}
            </button>
          </div>
        )}
      </div>
      <p className="mb-4 text-xs text-neutral-500">
        {t("asset_types_catalog_help") ||
          "Catalog = platform starter templates you can adopt. Your library is what appears when registering assets; edit or archive individual rows below. Typing a new name on Register also creates a type."}
      </p>

      {/* Tabs */}
      <div className="mb-4 flex gap-0 border-b border-neutral-200">
        {(["library", "catalog"] as const).map((tabId) => (
          <button
            key={tabId}
            onClick={() => setTab(tabId)}
            className={[
              "px-4 py-2 text-sm font-medium transition-colors",
              tab === tabId
                ? "border-b-2 border-primary-600 text-primary-600"
                : "text-neutral-500 hover:text-neutral-700",
            ].join(" ")}
          >
            {tabId === "library" ? t("asset_types") : t("adopt_from_catalog")}
          </button>
        ))}
      </div>

      {/* ── Tab: Library ────────────────────────────────────────────────── */}
      {tab === "library" && (
        <>
          {/* Filters */}
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <input
              type="search"
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm w-48"
              placeholder={t("search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label={t("search")}
            />
            {verticals.length > 0 && (
              <select
                className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={filterVertical}
                onChange={(e) => setFilterVertical(e.target.value)}
                aria-label={t("select_vertical")}
              >
                <option value="">{t("all_verticals")}</option>
                {verticals.map((v) => (
                  <option key={v.code} value={v.code}>
                    {lang.startsWith("ar") ? v.name_ar : v.name_en}
                  </option>
                ))}
              </select>
            )}
            <label className="flex items-center gap-1.5 text-sm text-neutral-600">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
                className="h-4 w-4"
              />
              {t("include_archived")}
            </label>
          </div>

          {/* Table */}
          {libLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-neutral-100" />
              ))}
            </div>
          ) : filteredTypes.length === 0 ? (
            <div className="rounded-xl border-2 border-dashed border-neutral-200 py-16 text-center">
              <p className="text-lg font-medium text-neutral-500">{t("no_asset_types_yet")}</p>
              <p className="mt-1 text-sm text-neutral-400">{t("no_asset_types_admin")}</p>
              <div className="mt-4 flex justify-center gap-3">
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white"
                >
                  + {t("custom_type")}
                </button>
                <button
                  onClick={() => setTab("catalog")}
                  className="rounded-md border border-neutral-300 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
                >
                  {t("adopt_from_catalog")}
                </button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-neutral-200">
              <table className="w-full text-sm">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("name")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("template_code")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("origin_label")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("max_age_years")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("asset_count_label")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("status")}</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {filteredTypes.map((ty) => (
                    <tr key={ty.id} className={ty.is_active ? "" : "opacity-50"}>
                      <td className="px-4 py-3 font-medium">
                        {localizedName(ty, lang)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-neutral-500">{ty.code}</td>
                      <td className="px-4 py-3">
                        <OriginBadge origin={ty.origin} />
                      </td>
                      <td className="px-4 py-3 text-neutral-600">
                        {ty.default_max_age_years != null ? `${ty.default_max_age_years} yr` : "—"}
                      </td>
                      <td className="px-4 py-3 text-neutral-600">
                        {ty.asset_count ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs font-medium ${ty.is_active ? "text-emerald-600" : "text-neutral-400"}`}
                        >
                          {ty.is_active ? t("active") : t("archived")}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {archiveConfirmId === ty.id ? (
                          <ArchiveConfirm
                            name={localizedName(ty, lang)}
                            onConfirm={() => void archiveType(ty.id, false)}
                            onCancel={() => setArchiveConfirmId(null)}
                          />
                        ) : (
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => setEditType(ty)}
                              className="text-xs text-primary-600 hover:underline"
                            >
                              {t("edit")}
                            </button>
                            {ty.is_active ? (
                              <button
                                onClick={() => setArchiveConfirmId(ty.id)}
                                className="text-xs text-neutral-500 hover:text-error-main hover:underline"
                              >
                                {t("archive")}
                              </button>
                            ) : (
                              <button
                                onClick={() => void archiveType(ty.id, true)}
                                className="text-xs text-emerald-600 hover:underline"
                              >
                                {t("restore")}
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* ── Tab: Catalog ─────────────────────────────────────────────────── */}
      {tab === "catalog" && (
        <>
          {/* Adopt result banner */}
          {adoptResult && (
            <div className="mb-4 rounded-lg border border-primary-200 bg-primary-50 px-4 py-3 text-sm text-primary-700">
              {adoptResult}
              <button
                onClick={() => setAdoptResult(null)}
                className="ms-3 text-xs text-primary-500 underline"
              >
                {t("close")}
              </button>
            </div>
          )}

          {/* Vertical filter */}
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <select
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={filterVertical}
              onChange={(e) => setFilterVertical(e.target.value)}
              aria-label={t("select_vertical")}
            >
              <option value="">{t("all_verticals")}</option>
              {verticals.map((v) => (
                <option key={v.code} value={v.code}>
                  {lang.startsWith("ar") ? v.name_ar : v.name_en}
                </option>
              ))}
            </select>
            {selectedTemplateIds.length > 0 && (
              <button
                onClick={() => void adoptSelected()}
                disabled={adoptLoading}
                className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {adoptLoading
                  ? t("loading")
                  : `${t("adopt_selected")} (${selectedTemplateIds.length})`}
              </button>
            )}
          </div>

          {/* Catalog list */}
          {catalogLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-neutral-100" />
              ))}
            </div>
          ) : templates.length === 0 ? (
            <p className="py-12 text-center text-neutral-500">{t("no_results")}</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-neutral-200">
              <table className="w-full text-sm">
                <thead className="border-b border-neutral-200 bg-neutral-50">
                  <tr>
                    <th className="w-8 px-3 py-3" />
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("name")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("template_code")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("max_age_years")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("criticality")}</th>
                    <th className="px-4 py-3 text-start font-medium text-neutral-600">{t("status")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {templates.map((tmpl) => {
                    const adopted = tmpl.adopted ?? false;
                    const checked = selectedTemplateIds.includes(tmpl.id);
                    return (
                      <tr key={tmpl.id} className={adopted ? "opacity-60" : ""}>
                        <td className="px-3 py-3">
                          <input
                            type="checkbox"
                            className="h-4 w-4 rounded"
                            checked={checked}
                            disabled={adopted}
                            onChange={() => toggleTemplate(tmpl.id)}
                            aria-label={localizedName(tmpl, lang)}
                          />
                        </td>
                        <td className="px-4 py-3 font-medium">{localizedName(tmpl, lang)}</td>
                        <td className="px-4 py-3 font-mono text-xs text-neutral-500">{tmpl.code}</td>
                        <td className="px-4 py-3 text-neutral-600">
                          {tmpl.default_max_age_years != null
                            ? `${tmpl.default_max_age_years} yr`
                            : "—"}
                        </td>
                        <td className="px-4 py-3 capitalize text-neutral-600">
                          {tmpl.default_criticality ?? "—"}
                        </td>
                        <td className="px-4 py-3">
                          {adopted ? (
                            <span className="text-xs font-medium text-emerald-600">
                              {t("already_adopted")}
                            </span>
                          ) : (
                            <span className="text-xs text-neutral-400">—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Create/Edit modal */}
      <TypeFormModal
        open={showCreateModal}
        verticals={verticals}
        onClose={() => setShowCreateModal(false)}
        onSaved={() => {
          setShowCreateModal(false);
          loadLibrary();
        }}
      />
      {editType && (
        <TypeFormModal
          open
          editId={editType.id}
          initialData={editType}
          verticals={verticals}
          onClose={() => setEditType(null)}
          onSaved={() => {
            setEditType(null);
            loadLibrary();
          }}
        />
      )}
    </div>
  );
}
