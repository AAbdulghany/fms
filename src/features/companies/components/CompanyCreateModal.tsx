import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { Vertical } from "@/lib/types";
import { ProvisionCredentialsModal } from "@/features/companies/components/ProvisionCredentialsModal";

type Props = {
  open: boolean;
  onClose: () => void;
  /** Called after the user dismisses the credentials modal (if provision succeeded). */
  onCreated: (companyId?: string) => void;
};

/** Emoji icon mapped to a vertical code. */
const VERTICAL_ICONS: Record<string, string> = {
  hospital: "🏥",
  hotel: "🏨",
  office: "🏢",
  retail: "🛍️",
  industrial: "🏭",
  education: "🏫",
  other: "···",
};

export function CompanyCreateModal({ open, onClose, onCreated }: Props) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const [legalName, setLegalName] = useState("");
  const [managerFullName, setManagerFullName] = useState("");
  const [verticalCode, setVerticalCode] = useState("");
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [verticalsLoading, setVerticalsLoading] = useState(false);
  const [siteName, setSiteName] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [timezone, setTimezone] = useState(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Riyadh"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creds, setCreds] = useState<{
    companyId: string;
    companyCode: string;
    username: string;
    email: string;
    initialPassword: string;
  } | null>(null);

  // Load verticals from API
  useEffect(() => {
    if (!open) return;
    setVerticalsLoading(true);
    void apiFetch<Vertical[]>("/verticals")
      .then(setVerticals)
      .catch(() => setVerticals([]))
      .finally(() => setVerticalsLoading(false));
  }, [open]);

  useEffect(() => {
    if (!open) {
      setCreds(null);
      setLegalName("");
      setManagerFullName("");
      setVerticalCode("");
      setSiteName("");
      setCity("");
      setCountry("");
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Riyadh");
      setError(null);
    }
  }, [open]);

  function closeAll() {
    const companyId = creds?.companyId;
    setCreds(null);
    onClose();
    if (companyId) {
      onCreated(companyId);
    }
  }

  if (!open) return null;

  if (creds) {
    return (
      <ProvisionCredentialsModal
        open
        title={t("company_created_credentials")}
        username={creds.username}
        email={creds.email}
        initialPassword={creds.initialPassword}
        extraLines={[
          { label: t("company_id_label"), value: creds.companyId },
          { label: t("company_code"), value: creds.companyCode },
        ]}
        onClose={closeAll}
      />
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<{
        company_id: string;
        company_code: string;
        manager_username: string;
        manager_email: string;
        initial_password: string;
      }>("/clients/provision", {
        method: "POST",
        json: {
          legal_name: legalName.trim(),
          manager_full_name: managerFullName.trim(),
          vertical_code: verticalCode || undefined,
          // Keep dual-write: send activity_type mapped from vertical_code for backward compat
          activity_type: verticalCode || undefined,
          site_name: siteName.trim(),
          city: city.trim(),
          country: country.trim(),
          timezone: timezone.trim() || "Asia/Riyadh",
        },
      });

      setLegalName("");
      setManagerFullName("");
      setVerticalCode("");
      setSiteName("");
      setCity("");
      setCountry("");
      setCreds({
        companyId: res.company_id,
        companyCode: res.company_code,
        username: res.manager_username,
        email: res.manager_email,
        initialPassword: res.initial_password,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  /** Vertical display name in active language. */
  function verticalLabel(v: Vertical): string {
    return lang.startsWith("ar") ? v.name_ar : v.name_en;
  }

  // Fallback cards when API returns no verticals
  const fallbackVerticals: Vertical[] = [
    { id: "hospital", code: "hospital", name_en: "Hospital", name_ar: "مستشفى" },
    { id: "hotel", code: "hotel", name_en: "Hotel", name_ar: "فندق" },
    { id: "office", code: "office", name_en: "Office", name_ar: "مكاتب" },
    { id: "retail", code: "retail", name_en: "Retail", name_ar: "تجزئة" },
    { id: "industrial", code: "industrial", name_en: "Industrial", name_ar: "صناعي" },
    { id: "education", code: "education", name_en: "Education", name_ar: "تعليمي" },
    { id: "other", code: "other", name_en: "Other", name_ar: "أخرى" },
  ];
  const displayVerticals = verticals.length > 0 ? verticals : fallbackVerticals;

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div
          className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl"
          role="dialog"
          aria-modal
        >
          <h2 className="mb-2 text-xl font-bold text-neutral-900">{t("create_company")}</h2>
          <p className="mb-4 text-sm text-neutral-600">{t("company_provision_blurb")}</p>
          <form onSubmit={onSubmit} className="space-y-4">

            {/* Company fields */}
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                {t("company_name")} *
              </label>
              <input
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={legalName}
                onChange={(e) => setLegalName(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                {t("company_manager_name")} *
              </label>
              <input
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={managerFullName}
                onChange={(e) => setManagerFullName(e.target.value)}
              />
            </div>

            {/* ── A1: Vertical picker cards ──────────────────────────────── */}
            <div>
              <label className="mb-2 block text-sm font-medium text-neutral-700">
                {t("vertical")} *
              </label>
              {verticalsLoading ? (
                <div className="flex items-center gap-2 text-sm text-neutral-500">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-400 border-t-transparent" />
                  {t("loading")}
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                  {displayVerticals.map((v) => {
                    const selected = verticalCode === v.code;
                    return (
                      <button
                        key={v.code}
                        type="button"
                        onClick={() => setVerticalCode(v.code)}
                        className={[
                          "flex flex-col items-center gap-1 rounded-lg border-2 px-2 py-3 text-center transition-all",
                          "focus:outline-none focus:ring-2 focus:ring-primary-500",
                          selected
                            ? "border-primary-600 bg-primary-50 text-primary-700 shadow-sm"
                            : "border-neutral-200 bg-white text-neutral-700 hover:border-primary-300 hover:shadow-sm",
                        ].join(" ")}
                        aria-pressed={selected}
                        aria-label={verticalLabel(v)}
                      >
                        <span className="text-2xl leading-none" aria-hidden>
                          {VERTICAL_ICONS[v.code] ?? "🏗️"}
                        </span>
                        <span className="text-xs font-medium leading-tight">{verticalLabel(v)}</span>
                      </button>
                    );
                  })}
                </div>
              )}
              {!verticalCode && (
                <p className="mt-1 text-xs text-error-main">{t("select_vertical")}</p>
              )}
              {verticalCode === "other" && (
                <p className="mt-1 rounded bg-neutral-100 px-2 py-1 text-xs text-neutral-600">
                  {t("vertical_other_hint")}
                </p>
              )}
            </div>

            {/* First site fields */}
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
                {t("first_site_label")}
              </p>
              <p className="text-xs text-neutral-500">{t("first_site_hint")}</p>
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">
                  {t("site_name")} *
                </label>
                <input
                  required
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  value={siteName}
                  onChange={(e) => setSiteName(e.target.value)}
                  placeholder={t("site_name_placeholder")}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">
                    {t("city")} *
                  </label>
                  <input
                    required
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="e.g. Riyadh"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">
                    {t("country")} *
                  </label>
                  <input
                    required
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    placeholder="e.g. Saudi Arabia"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">
                  {t("site_timezone")} *
                </label>
                <input
                  required
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm font-mono text-xs"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                />
                <p className="mt-0.5 text-xs text-neutral-400">{t("timezone_auto_detected")}</p>
              </div>
            </div>

            {error && <p className="text-sm text-error-main">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100"
                onClick={onClose}
              >
                {t("cancel")}
              </button>
              <button
                type="submit"
                disabled={loading || !verticalCode}
                className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
              >
                {loading ? t("loading") : t("create")}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
