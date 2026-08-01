import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import { ProvisionCredentialsModal } from "@/components/ProvisionCredentialsModal";

type Props = {
  open: boolean;
  siteId: string;
  siteName: string;
  onClose: () => void;
  onAssigned: () => void;
};

export function SiteAssignManagerModal({ open, siteId, siteName, onClose, onAssigned }: Props) {
  const { t } = useTranslation();
  const [managerFullName, setManagerFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creds, setCreds] = useState<{ username: string; email: string; initialPassword: string } | null>(null);

  if (!open) return null;

  if (creds) {
    return (
      <ProvisionCredentialsModal
        open
        title={t("site_manager_assigned_credentials")}
        username={creds.username}
        email={creds.email}
        initialPassword={creds.initialPassword}
        onClose={() => {
          setCreds(null);
          onAssigned();
          onClose();
        }}
      />
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<{
        manager_username: string;
        manager_email: string;
        initial_password: string;
      }>(`/sites/${siteId}/assign-manager`, {
        method: "POST",
        json: { manager_full_name: managerFullName.trim() },
      });
      setManagerFullName("");
      setCreds({
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <h2 className="mb-1 text-xl font-bold text-neutral-900">{t("assign_site_manager_title")}</h2>
        <p className="mb-4 text-sm text-neutral-600">
          {t("assign_site_manager_blurb", { site: siteName })}
        </p>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">
              {t("site_manager_name")} *
            </label>
            <input
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={managerFullName}
              onChange={(e) => setManagerFullName(e.target.value)}
              placeholder={t("site_manager_name_placeholder")}
            />
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
              {loading ? t("loading") : t("assign")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
