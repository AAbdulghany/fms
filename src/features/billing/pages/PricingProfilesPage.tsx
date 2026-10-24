import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";

type Profile = {
  id: string;
  name: string;
  hourly_rate_sar: string | number;
  parts_markup_percent: string | number;
  default_service_fee_sar: string | number;
  emergency_surcharge_percent: string | number;
};

export default function PricingProfilesPage() {
  const { t, i18n } = useTranslation();
  const [rows, setRows] = useState<Profile[]>([]);
  const [name, setName] = useState("");
  const [hourly, setHourly] = useState("150");
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setRows(await apiFetch<Profile[]>("/pricing-profiles"));
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }, [t, i18n.language]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      await apiFetch("/pricing-profiles", {
        method: "POST",
        json: {
          name: name.trim() || "Standard rates",
          hourly_rate_sar: hourly,
          parts_markup_percent: 15,
          default_service_fee_sar: 50,
          emergency_surcharge_percent: 25,
        },
      });
      setName("");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-neutral-900">{t("pricing_profiles")}</h1>
      {err && <p className="text-sm text-red-600">{err}</p>}
      <form onSubmit={onCreate} className="flex flex-wrap gap-2 rounded-lg border border-neutral-200 bg-white p-4">
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          placeholder={t("name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="w-28 rounded border border-neutral-300 px-3 py-2 text-sm"
          type="number"
          value={hourly}
          onChange={(e) => setHourly(e.target.value)}
        />
        <button type="submit" className="rounded bg-neutral-900 px-3 py-2 text-sm text-white">
          {t("add")}
        </button>
      </form>
      <ul className="divide-y rounded-lg border border-neutral-200 bg-white">
        {rows.map((r) => (
          <li key={r.id} className="flex justify-between px-4 py-3 text-sm">
            <span className="font-medium">{r.name}</span>
            <span className="tabular-nums">{r.hourly_rate_sar}/h</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
