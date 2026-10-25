import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";
import { SlideNotice } from "@/shared/components/SlideNotice";

type Contract = {
  id: string;
  client_id: string;
  pricing_profile_id: string;
  name: string;
  currency: string;
  status: string;
};
type Client = { id: string; legal_name: string };
type Profile = { id: string; name: string };

export default function ContractsPage() {
  const { t, i18n } = useTranslation();
  const [rows, setRows] = useState<Contract[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [clientId, setClientId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [c, cl, pr] = await Promise.all([
        apiFetch<Contract[]>("/contracts"),
        apiFetch<Client[]>("/clients"),
        apiFetch<Profile[]>("/pricing-profiles"),
      ]);
      setRows(c);
      setClients(cl);
      setProfiles(pr);
      if (!clientId && cl[0]) setClientId(cl[0].id);
      if (!profileId && pr[0]) setProfileId(pr[0].id);
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }, [t, i18n.language, clientId, profileId]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initial load only
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      await apiFetch("/contracts", {
        method: "POST",
        json: {
          client_id: clientId,
          pricing_profile_id: profileId,
          name: "Default",
          currency: "SAR",
        },
      });
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  const clientName = (id: string) => clients.find((c) => c.id === id)?.legal_name ?? id;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-neutral-900">{t("contracts")}</h1>
      <SlideNotice text={err} tone="error" />
      <form onSubmit={onCreate} className="flex flex-wrap gap-2 rounded-lg border border-neutral-200 bg-white p-4">
        <select className="rounded border px-3 py-2 text-sm" value={clientId} onChange={(e) => setClientId(e.target.value)}>
          {clients.map((c) => (
            <option key={c.id} value={c.id}>
              {c.legal_name}
            </option>
          ))}
        </select>
        <select className="rounded border px-3 py-2 text-sm" value={profileId} onChange={(e) => setProfileId(e.target.value)}>
          {profiles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button type="submit" className="rounded bg-neutral-900 px-3 py-2 text-sm text-white">
          {t("add")}
        </button>
      </form>
      <ul className="divide-y rounded-lg border border-neutral-200 bg-white">
        {rows.map((r) => (
          <li key={r.id} className="px-4 py-3 text-sm">
            <span className="font-medium">{r.name}</span>
            <span className="ms-2 text-neutral-600">{clientName(r.client_id)}</span>
            <span className="ms-2 tabular-nums text-neutral-500">{r.currency}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
