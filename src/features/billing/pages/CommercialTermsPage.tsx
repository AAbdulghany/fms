/**
 * Commercial Terms — General (default for all) + per-client custom terms.
 * Draft invoices can be recalculated; paid/sent/approved stay snapshotted.
 */
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";
import { SlideNotices } from "@/shared/components/SlideNotice";
import { activePillClass, chip, tone } from "@/shared/lib/palette";

type Client = { id: string; legal_name: string };
type Profile = {
  id: string;
  name: string;
  hourly_rate_sar: string | number;
  parts_markup_percent: string | number;
  default_service_fee_sar: string | number;
  emergency_surcharge_percent: string | number;
};
type Contract = {
  id: string;
  client_id: string;
  pricing_profile_id: string;
  name: string;
  currency: string;
  status: string;
  tax_rate_percent?: string | number | null;
  tax_inclusive?: boolean;
};
type TaxProfile = {
  id: string;
  rate_percent: string | number;
  tax_inclusive: boolean;
  is_default: boolean;
};
type InvoiceRow = { id: string; client_id: string; status: string; number: string };

const CURRENCIES = ["SAR", "EGP", "USD", "EUR"];
const GENERAL_NAME = "General";

type EditorTarget =
  | { kind: "general" }
  | { kind: "contract"; contract: Contract }
  | { kind: "new" };

export default function CommercialTermsPage() {
  const { t, i18n } = useTranslation();
  const [clients, setClients] = useState<Client[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [defaultTax, setDefaultTax] = useState<TaxProfile | null>(null);
  const [generalProfile, setGeneralProfile] = useState<Profile | null>(null);
  const [editor, setEditor] = useState<EditorTarget | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const [clientId, setClientId] = useState("");
  const [hourly, setHourly] = useState("150");
  const [markup, setMarkup] = useState("15");
  const [fee, setFee] = useState("50");
  const [emergency, setEmergency] = useState("25");
  const [currency, setCurrency] = useState("SAR");
  const [taxRate, setTaxRate] = useState("15");
  const [taxInclusive, setTaxInclusive] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const [cl, pr, ct, tax] = await Promise.all([
        apiFetch<Client[]>("/clients"),
        apiFetch<Profile[]>("/pricing-profiles"),
        apiFetch<Contract[]>("/contracts"),
        apiFetch<TaxProfile[]>("/tax-profiles"),
      ]);
      setClients(cl);
      setProfiles(pr);
      setContracts(ct.filter((c) => c.status === "active"));
      const def = tax.find((r) => r.is_default) ?? tax[0] ?? null;
      setDefaultTax(def);
      setGeneralProfile(pr.find((p) => p.name === GENERAL_NAME) ?? null);
      if (!clientId && cl[0]) setClientId(cl[0].id);
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }, [t, i18n.language, clientId]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openGeneral() {
    setEditor({ kind: "general" });
    const gp = generalProfile;
    setHourly(String(gp?.hourly_rate_sar ?? "150"));
    setMarkup(String(gp?.parts_markup_percent ?? "15"));
    setFee(String(gp?.default_service_fee_sar ?? "50"));
    setEmergency(String(gp?.emergency_surcharge_percent ?? "25"));
    setCurrency("SAR");
    setTaxRate(String(defaultTax?.rate_percent ?? "15"));
    setTaxInclusive(!!defaultTax?.tax_inclusive);
    setMsg(null);
  }

  function openContract(c: Contract) {
    setEditor({ kind: "contract", contract: c });
    setClientId(c.client_id);
    const p = profiles.find((x) => x.id === c.pricing_profile_id);
    setHourly(String(p?.hourly_rate_sar ?? "150"));
    setMarkup(String(p?.parts_markup_percent ?? "15"));
    setFee(String(p?.default_service_fee_sar ?? "50"));
    setEmergency(String(p?.emergency_surcharge_percent ?? "25"));
    setCurrency(c.currency || "SAR");
    setTaxRate(
      c.tax_rate_percent != null && c.tax_rate_percent !== ""
        ? String(c.tax_rate_percent)
        : String(defaultTax?.rate_percent ?? "15")
    );
    setTaxInclusive(
      c.tax_rate_percent != null ? !!c.tax_inclusive : !!defaultTax?.tax_inclusive
    );
    setMsg(null);
  }

  function openNew() {
    setEditor({ kind: "new" });
    setHourly("150");
    setMarkup("15");
    setFee("50");
    setEmergency("25");
    setCurrency("SAR");
    setTaxRate(String(defaultTax?.rate_percent ?? "15"));
    setTaxInclusive(!!defaultTax?.tax_inclusive);
    if (!clientId && clients[0]) setClientId(clients[0].id);
    setMsg(null);
  }

  async function applyToOpenInvoices(forClientId: string | null) {
    const invoices = await apiFetch<InvoiceRow[]>("/invoices").catch(() => [] as InvoiceRow[]);
    const editable = invoices.filter(
      (inv) =>
        inv.status === "draft" &&
        (forClientId == null || inv.client_id === forClientId)
    );
    let ok = 0;
    let skipped = 0;
    for (const inv of editable) {
      try {
        await apiFetch(`/invoices/${inv.id}/recalculate`, { method: "POST" });
        ok += 1;
      } catch {
        skipped += 1;
      }
    }
    const locked = invoices.filter(
      (inv) =>
        inv.status !== "draft" &&
        (forClientId == null || inv.client_id === forClientId)
    ).length;
    setMsg(
      t("commercial_terms_applied", { ok, skipped, locked }) ||
        `Applied to ${ok} draft invoice(s). ${locked} completed/sent invoice(s) kept as snapshots.`
    );
  }

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!editor) return;
    setErr(null);
    setMsg(null);
    try {
      if (editor.kind === "general") {
        await apiFetch("/pricing-profiles", {
          method: "POST",
          json: {
            name: GENERAL_NAME,
            hourly_rate_sar: hourly,
            parts_markup_percent: markup,
            default_service_fee_sar: fee,
            emergency_surcharge_percent: emergency,
          },
        });
        if (defaultTax) {
          await apiFetch(`/tax-profiles/${defaultTax.id}`, {
            method: "PATCH",
            json: { rate_percent: taxRate, tax_inclusive: taxInclusive },
          });
        }
        await applyToOpenInvoices(null);
      } else {
        const cid = editor.kind === "contract" ? editor.contract.client_id : clientId;
        if (!cid) {
          setErr(t("select_company"));
          return;
        }
        const clientName = clients.find((c) => c.id === cid)?.legal_name ?? "Client";
        const created = await apiFetch<Profile>("/pricing-profiles", {
          method: "POST",
          json: {
            name: `${clientName} rates`,
            hourly_rate_sar: hourly,
            parts_markup_percent: markup,
            default_service_fee_sar: fee,
            emergency_surcharge_percent: emergency,
          },
        });
        if (editor.kind === "contract") {
          await apiFetch(`/contracts/${editor.contract.id}`, {
            method: "PATCH",
            json: {
              pricing_profile_id: created.id,
              currency,
              tax_rate_percent: taxRate,
              tax_inclusive: taxInclusive,
            },
          });
        } else {
          await apiFetch("/contracts", {
            method: "POST",
            json: {
              client_id: cid,
              pricing_profile_id: created.id,
              name: "Custom",
              currency,
              tax_rate_percent: taxRate,
              tax_inclusive: taxInclusive,
            },
          });
        }
        await applyToOpenInvoices(cid);
      }
      setEditor(null);
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  const clientName = (id: string) => clients.find((c) => c.id === id)?.legal_name ?? id;

  async function onDeleteContract(c: Contract) {
    const label = clientName(c.client_id);
    if (!window.confirm(t("confirm_delete_commercial_term", { name: label }) || `Delete terms for ${label}?`)) {
      return;
    }
    setErr(null);
    setMsg(null);
    try {
      await apiFetch(`/contracts/${c.id}`, { method: "DELETE" });
      setMsg(t("commercial_term_deleted") || "Commercial term deleted.");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  return (
    <div className="space-y-3 lg:space-y-6" data-testid="commercial-terms-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 lg:text-3xl lg:font-semibold">{t("commercial_terms")}</h1>
          <p className="mt-1 hidden text-sm text-neutral-600 lg:block">{t("commercial_terms_help")}</p>
        </div>
        <button
          type="button"
          data-testid="new-commercial-term"
          className="min-h-11 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          onClick={openNew}
        >
          + {t("new_commercial_term") || "New commercial term"}
        </button>
      </div>

      <SlideNotices success={msg} error={err} />

      <div className="space-y-3">
        <div className="rounded-xl border border-neutral-200 bg-neutral-0 px-3 py-2.5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-sm font-bold text-neutral-900">
                  {t("general_commercial_term") || "General (default)"}
                </h2>
                <span className={`${chip} ${tone.primary}`}>
                  {t("term_default")}
                </span>
              </div>
              <p className="mt-0.5 hidden text-xs text-neutral-500 lg:block">
                {t("general_commercial_term_help") ||
                  "Applied to every client unless a custom term exists."}
              </p>
              <p className="mt-1 text-xs text-neutral-500">
                {generalProfile ? (
                  <bdi dir="ltr">
                    {`${generalProfile.hourly_rate_sar}/h · VAT ${defaultTax?.rate_percent ?? "—"}%`}
                  </bdi>
                ) : (
                  t("not_configured") || "Not configured yet — edit to create."
                )}
              </p>
            </div>
            <button
              type="button"
              className="shrink-0 rounded-lg border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-50"
              onClick={openGeneral}
            >
              {t("edit") || "Edit"}
            </button>
          </div>
        </div>

        {contracts.length === 0 ? (
          <p className="text-sm text-neutral-500">
            {t("no_custom_commercial_terms") || "No custom client terms yet."}
          </p>
        ) : (
          contracts.map((c) => {
            const p = profiles.find((x) => x.id === c.pricing_profile_id);
            return (
              <div key={c.id} className="rounded-xl border border-neutral-200 bg-neutral-0 px-3 py-2.5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-sm font-bold text-neutral-900">{clientName(c.client_id)}</h2>
                      <span className={activePillClass(true)}>
                        {t(c.status) || c.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-neutral-500">
                      <bdi dir="ltr">
                        {`${c.currency} · ${p ? `${p.hourly_rate_sar}/h` : "—"}`}
                      </bdi>
                      {" · "}
                      {c.tax_rate_percent != null ? (
                        <bdi dir="ltr">{`VAT ${c.tax_rate_percent}%`}</bdi>
                      ) : (
                        t("uses_general") || "uses General"
                      )}
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-50"
                      onClick={() => openContract(c)}
                    >
                      {t("edit") || "Edit"}
                    </button>
                    <button
                      type="button"
                      data-testid="delete-commercial-term"
                      className="rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
                      onClick={() => void onDeleteContract(c)}
                    >
                      {t("delete") || "Delete"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {editor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <form
            onSubmit={onSave}
            className="max-h-[90vh] w-full max-w-lg space-y-4 overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
          >
            <h2 className="text-lg font-semibold">
              {editor.kind === "general"
                ? t("general_commercial_term") || "General"
                : editor.kind === "new"
                  ? t("new_commercial_term") || "New commercial term"
                  : t("edit") || "Edit"}
            </h2>

            {editor.kind === "new" && (
              <label className="block text-sm">
                {t("company") || "Client"}
                <select
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  required
                >
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.legal_name}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm">
                {t("hourly_rate") || "Hourly rate"}
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                  type="number"
                  step="0.01"
                  value={hourly}
                  onChange={(e) => setHourly(e.target.value)}
                />
              </label>
              <label className="block text-sm">
                {t("parts_markup") || "Parts markup %"}
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                  type="number"
                  step="0.01"
                  value={markup}
                  onChange={(e) => setMarkup(e.target.value)}
                />
              </label>
              <label className="block text-sm">
                {t("service_fee") || "Service fee"}
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                  type="number"
                  step="0.01"
                  value={fee}
                  onChange={(e) => setFee(e.target.value)}
                />
              </label>
              <label className="block text-sm">
                {t("emergency_surcharge") || "Emergency %"}
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                  type="number"
                  step="0.01"
                  value={emergency}
                  onChange={(e) => setEmergency(e.target.value)}
                />
              </label>
              {editor.kind !== "general" && (
                <label className="block text-sm">
                  {t("currency") || "Currency"}
                  <select
                    className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                  >
                    {CURRENCIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label className="block text-sm">
                {t("vat_rate_percent") || "VAT %"}
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base lg:text-sm"
                  type="number"
                  step="0.001"
                  value={taxRate}
                  onChange={(e) => setTaxRate(e.target.value)}
                />
              </label>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={taxInclusive}
                onChange={(e) => setTaxInclusive(e.target.checked)}
              />
              {t("tax_inclusive")}
            </label>
            <p className="text-xs text-neutral-500">
              {t("commercial_terms_snapshot_note") ||
                "Saving recalculates draft invoices only. Sent / paid / approved invoices keep their snapshotted amounts."}
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="rounded border px-4 py-2 text-sm"
                onClick={() => setEditor(null)}
              >
                {t("cancel")}
              </button>
              <button type="submit" className="rounded bg-neutral-900 px-4 py-2 text-sm text-white">
                {t("save")}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
