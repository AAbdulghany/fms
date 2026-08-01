import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import { ProvisionCredentialsModal } from "@/components/ProvisionCredentialsModal";

type ProvisionCreds = { username: string; email: string; initialPassword: string };

type Props = {
  open: boolean;
  clientId: string;
  /** "provision" (default): creates site + site manager. "add-only": creates site only, no manager. */
  mode?: "provision" | "add-only";
  defaultCity?: string;
  defaultCountry?: string;
  defaultTimezone?: string;
  onClose: () => void;
  onProvisioned?: (creds: ProvisionCreds) => void;
  onAdded?: () => void;
};

function buildAddressJson(city: string, country: string) {
  const address: Record<string, string> = {};
  if (city.trim()) address.city = city.trim();
  if (country.trim()) address.country = country.trim();
  return address;
}

export function SiteProvisionModal({
  open,
  clientId,
  mode = "provision",
  defaultCity = "",
  defaultCountry = "",
  defaultTimezone,
  onClose,
  onProvisioned,
  onAdded,
}: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [managerName, setManagerName] = useState("");
  const [timezone, setTimezone] = useState(
    () => defaultTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Riyadh"
  );
  const [city, setCity] = useState(defaultCity);
  const [country, setCountry] = useState(defaultCountry);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creds, setCreds] = useState<ProvisionCreds | null>(null);

  useEffect(() => {
    if (open) {
      setName("");
      setManagerName("");
      setTimezone(
        defaultTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Riyadh"
      );
      setCity(defaultCity);
      setCountry(defaultCountry);
      setError(null);
      setCreds(null);
    }
  }, [open, defaultCity, defaultCountry, defaultTimezone]);

  if (!open) return null;

  const isAddOnly = mode === "add-only";

  if (creds) {
    return (
      <ProvisionCredentialsModal
        open
        title={t("site_created_credentials")}
        username={creds.username}
        email={creds.email}
        initialPassword={creds.initialPassword}
        onClose={() => {
          setCreds(null);
          onProvisioned?.(creds);
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
      const address_json = buildAddressJson(city, country);
      const tz = timezone.trim() || "Asia/Riyadh";

      if (isAddOnly) {
        await apiFetch("/sites", {
          method: "POST",
          json: {
            client_id: clientId,
            name: name.trim(),
            timezone: tz,
            address_json,
          },
        });
        onAdded?.();
        onClose();
      } else {
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
            timezone: tz,
            ...(city.trim() ? { city: city.trim() } : {}),
            ...(country.trim() ? { country: country.trim() } : {}),
          },
        });
        setCreds({
          username: res.manager_username,
          email: res.manager_email,
          initialPassword: res.initial_password,
        });
        onAdded?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        className="w-full max-w-md rounded-xl bg-neutral-0 p-6 shadow-xl"
        role="dialog"
        aria-modal
        data-testid={isAddOnly ? "site-add-modal" : "site-provision-modal"}
      >
        <h2 className="mb-4 text-xl font-bold text-neutral-900">
          {isAddOnly ? t("add_site") : t("add_site_manager_title")}
        </h2>
        <p className="mb-4 text-sm text-neutral-600">
          {isAddOnly ? t("site_add_blurb") : t("site_provision_blurb")}
        </p>
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
          {!isAddOnly && (
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site_manager_name")} *</label>
              <input
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={managerName}
                onChange={(e) => setManagerName(e.target.value)}
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-700">{t("site_timezone")}</label>
            <input
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm font-mono text-xs"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            />
            <p className="mt-0.5 text-xs text-neutral-400">{t("timezone_auto_detected")}</p>
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
