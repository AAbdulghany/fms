import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";

type Props = {
  open: boolean;
  companyId: string;
  initialLegalName: string;
  initialCode: string;
  onClose: () => void;
  onSaved: () => void;
};

export function CompanyEditModal({ open, companyId, initialLegalName, initialCode, onClose, onSaved }: Props) {
  const { t } = useTranslation();
  const [legalName, setLegalName] = useState(initialLegalName);
  const [code, setCode] = useState(initialCode);

  useEffect(() => {
    if (open) {
      setLegalName(initialLegalName);
      setCode(initialCode);
    }
  }, [open, initialLegalName, initialCode]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      <div className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("edit_company")}</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("company_name")} *</label>
            <input
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={legalName}
              onChange={(e) => setLegalName(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("company_code")}</label>
            <input
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
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
              {loading ? t("loading") : t("save")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
