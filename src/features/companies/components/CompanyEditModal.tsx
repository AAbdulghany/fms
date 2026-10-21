import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { Vertical } from "@/lib/types";

type Props = {
  open: boolean;
  companyId: string;
  initialLegalName: string;
  initialCode: string;
  initialVerticalCode?: string | null;
  onClose: () => void;
  onSaved: () => void;
};

export function CompanyEditModal({
  open,
  companyId,
  initialLegalName,
  initialCode,
  initialVerticalCode,
  onClose,
  onSaved,
}: Props) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const [legalName, setLegalName] = useState(initialLegalName);
  const [code, setCode] = useState(initialCode);
  const [verticalCode, setVerticalCode] = useState(initialVerticalCode || "");
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLegalName(initialLegalName);
      setCode(initialCode);
      setVerticalCode(initialVerticalCode || "");
    }
  }, [open, initialLegalName, initialCode, initialVerticalCode]);

  // Load verticals once when modal opens
  useEffect(() => {
    if (!open) return;
    void apiFetch<Vertical[]>("/verticals")
      .then(setVerticals)
      .catch(() => setVerticals([]));
  }, [open]);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiFetch(`/clients/${companyId}`, {
        method: "PATCH",
        json: {
          legal_name: legalName.trim(),
          code: code.trim(),
          ...(verticalCode ? { vertical_code: verticalCode } : {}),
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

  function verticalLabel(v: Vertical): string {
    return lang.startsWith("ar") ? v.name_ar : v.name_en;
  }

  // Fallback if API returns nothing
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl"
        role="dialog"
        aria-modal
      >
        <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("edit_company")}</h2>
        <form onSubmit={onSubmit} className="space-y-4">
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
              {t("company_code")}
            </label>
            <input
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </div>

          {/* ── A1: Vertical select ──────────────────────────────────────── */}
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">
              {t("vertical")}
            </label>
            <select
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={verticalCode}
              onChange={(e) => setVerticalCode(e.target.value)}
            >
              <option value="">{t("select_vertical")}</option>
              {displayVerticals.map((v) => (
                <option key={v.code} value={v.code}>
                  {verticalLabel(v)}
                </option>
              ))}
            </select>
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
              disabled={loading}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? t("loading") : t("save")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
