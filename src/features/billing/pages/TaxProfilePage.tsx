import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";

type TaxProfile = {
  id: string;
  name: string;
  rate_percent: string | number;
  tax_inclusive: boolean;
  rounding: string;
  is_default: boolean;
};

export default function TaxProfilePage() {
  const { t, i18n } = useTranslation();
  const [profile, setProfile] = useState<TaxProfile | null>(null);
  const [rate, setRate] = useState("15");
  const [inclusive, setInclusive] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const rows = await apiFetch<TaxProfile[]>("/tax-profiles");
      const def = rows.find((r) => r.is_default) ?? rows[0] ?? null;
      setProfile(def);
      if (def) {
        setRate(String(def.rate_percent));
        setInclusive(!!def.tax_inclusive);
      }
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }, [t, i18n.language]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!profile) return;
    setErr(null);
    setMsg(null);
    try {
      await apiFetch(`/tax-profiles/${profile.id}`, {
        method: "PATCH",
        json: {
          rate_percent: rate,
          tax_inclusive: inclusive,
        },
      });
      setMsg(t("tax_saved_note"));
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-neutral-900">{t("tax_profile")}</h1>
      <p className="text-sm text-neutral-600">{t("tax_profile_help")}</p>
      {err && <p className="text-sm text-red-600">{err}</p>}
      {msg && <p className="text-sm text-emerald-700">{msg}</p>}
      {profile && (
        <form onSubmit={onSave} className="space-y-4 rounded-lg border border-neutral-200 bg-white p-4">
          <label className="block text-sm">
            <span className="text-neutral-700">{t("vat_rate_percent")}</span>
            <input
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
              type="number"
              step="0.001"
              min="0"
              value={rate}
              onChange={(e) => setRate(e.target.value)}
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-neutral-800">
            <input type="checkbox" checked={inclusive} onChange={(e) => setInclusive(e.target.checked)} />
            {t("tax_inclusive")}
          </label>
          <button type="submit" className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white">
            {t("save")}
          </button>
        </form>
      )}
    </div>
  );
}
