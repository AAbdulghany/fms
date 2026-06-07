import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";

type Props = {
  open: boolean;
  clientId: string;
  onClose: () => void;
  onProvisioned: (creds: { username: string; email: string; initialPassword: string }) => void;
};

export function SiteProvisionModal({ open, clientId, onClose, onProvisioned }: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [managerName, setManagerName] = useState("");
  const [timezone, setTimezone] = useState("Asia/Riyadh");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<{
        manager_username: string;
        manager_email: string;
        initial_password: string;
      }>("/sites/provision", {
        method: "POST",
        json: {
          client_id: clientId,
          name: name.trim(),
          manager_full_name: managerName.trim(),
          timezone: timezone.trim() || "Asia/Riyadh",
          ...(city.trim() ? { city: city.trim() } : {}),
          ...(country.trim() ? { country: country.trim() } : {}),
        },
      });
      setName("");
      setManagerName("");
      setCity("");
      setCountry("");
      onProvisioned({
        username: res.manager_username,
        email: res.manager_email,
        initialPassword: res.initial_password,
      });
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
        <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("add_site")}</h2>
        <p className="mb-4 text-sm text-neutral-600">{t("site_provision_blurb")}</p>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site_name")} *</label>
            <input
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site_manager_name")} *</label>
            <input
              required
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={managerName}
              onChange={(e) => setManagerName(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site_timezone")}</label>
            <input
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("city")}</label>
              <input
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g. Riyadh"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("country")}</label>
              <input
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder="e.g. Saudi Arabia"
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
