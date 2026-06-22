import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch, downloadAuthenticatedFile, openAuthenticatedBlob, resolveApiError } from "../lib/api";
import { formatMoneyAmount } from "../lib/formatCurrency";
import type { Invoice } from "../lib/types";

interface UserMe {
  role: string;
}

const CURRENCIES = ["SAR", "EGP", "USD", "EUR"] as const;

function toDateInput(value?: string | null): string {
  if (!value) return "";
  return value.slice(0, 10);
}

export function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [me, setMe] = useState<UserMe | null>(null);
  const [billingEmail, setBillingEmail] = useState("");
  const [issueDate, setIssueDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [currency, setCurrency] = useState("SAR");
  const [workOrderTitle, setWorkOrderTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [laborHours, setLaborHours] = useState("");
  const [laborRate, setLaborRate] = useState("");
  const [serviceFee, setServiceFee] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [acting, setActing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const canAdmin =
    me?.role === "company_admin" || me?.role === "super_admin";

  const syncForm = (inv: Invoice) => {
    setBillingEmail(inv.billing_email ?? "");
    setIssueDate(toDateInput(inv.issued_at));
    setDueDate(toDateInput(inv.due_date));
    setCurrency(inv.currency || "SAR");
    setWorkOrderTitle(inv.work_order_title ?? "");
    setNotes(inv.notes ?? "");
    setLaborHours(inv.labor_hours ?? "0");
    setLaborRate(inv.labor_rate_sar ?? "0");
    setServiceFee(inv.service_fee_sar ?? "0");
  };

  const load = useCallback(async () => {
    if (!id) return;
    setErr(null);
    setLoading(true);
    try {
      const [inv, user] = await Promise.all([
        apiFetch<Invoice>(`/invoices/${id}`),
        apiFetch<UserMe>("/users/me"),
      ]);
      setInvoice(inv);
      setMe(user);
      syncForm(inv);
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    void load();
  }, [load]);

  async function saveInvoice(e: FormEvent) {
    e.preventDefault();
    if (!id || !invoice || !canAdmin) return;
    setSaving(true);
    setErr(null);
    setMsg(null);
    try {
      const updated = await apiFetch<Invoice>(`/invoices/${id}`, {
        method: "PATCH",
        json: {
          billing_email: billingEmail || null,
          issued_at: issueDate || null,
          due_date: dueDate || null,
          currency,
          work_order_title: workOrderTitle || null,
          notes,
          labor_hours: laborHours === "" ? null : Number(laborHours),
          labor_rate_sar: laborRate === "" ? null : Number(laborRate),
          service_fee_sar: serviceFee === "" ? null : Number(serviceFee),
        },
      });
      setInvoice(updated);
      syncForm(updated);
      setMsg(t("invoice_saved") || "Invoice updated");
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setSaving(false);
    }
  }

  async function runAction(action: "approve" | "send" | "mark-paid") {
    if (!id) return;
    setActing(true);
    setErr(null);
    setMsg(null);
    try {
      const updated = await apiFetch<Invoice>(`/invoices/${id}/${action}`, { method: "POST" });
      setInvoice(updated);
      syncForm(updated);
      setMsg(t(`invoice_${action.replace("-", "_")}_done`) || "Done");
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setActing(false);
    }
  }

  async function recalculateFromWorkOrder() {
    if (!id || !canAdmin || invoice?.status !== "draft") return;
    setActing(true);
    setErr(null);
    setMsg(null);
    try {
      const updated = await apiFetch<Invoice>(`/invoices/${id}/recalculate`, { method: "POST" });
      setInvoice(updated);
      syncForm(updated);
      setMsg(t("invoice_recalculated") || "Invoice recalculated from work order");
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setActing(false);
    }
  }

  async function viewPdf() {
    if (!id) return;
    setErr(null);
    try {
      await openAuthenticatedBlob(`/invoices/${id}/pdf?inline=true`);
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function downloadPdf() {
    if (!id || !invoice) return;
    setErr(null);
    try {
      await downloadAuthenticatedFile(
        `/invoices/${id}/pdf`,
        `invoice-${invoice.number}.pdf`
      );
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[240px] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="space-y-4">
        <p className="text-error-main">{err || t("error")}</p>
        <button type="button" className="text-sm text-primary-600 hover:underline" onClick={() => navigate("/invoices")}>
          {t("back_to_invoices") || "Back to invoices"}
        </button>
      </div>
    );
  }

  const editable = canAdmin && (invoice.status === "draft" || invoice.status === "approved");
  const laborAmountPreview =
    (Number(laborHours) || 0) * (Number(laborRate) || 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <button
            type="button"
            className="mb-2 text-sm text-primary-600 hover:underline"
            onClick={() => navigate("/invoices")}
          >
            ← {t("invoices")}
          </button>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("invoice")} #{invoice.number}
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            {t("status")}:{" "}
            <span className="rounded-full bg-neutral-100 px-2 py-0.5 font-medium text-neutral-800">
              {invoice.status}
            </span>
            {" · "}
            {invoice.client_name}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm hover:bg-neutral-50"
            onClick={() => void viewPdf()}
          >
            {t("view_pdf") || "View PDF"}
          </button>
          <button
            type="button"
            className="rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700"
            onClick={() => void downloadPdf()}
          >
            {t("download") || "Download"}
          </button>
        </div>
      </div>

      {msg && <p className="rounded-md bg-success-light px-3 py-2 text-sm text-success-dark">{msg}</p>}
      {err && <p className="rounded-md bg-error-light px-3 py-2 text-sm text-error-dark">{err}</p>}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          <h2 className="text-base font-semibold text-neutral-800">{t("invoice_details") || "Invoice details"}</h2>

          {editable ? (
            <form onSubmit={(e) => void saveInvoice(e)} className="mt-4 space-y-3">
              <label className="block text-sm">
                <span className="mb-1 block text-xs font-medium text-neutral-600">
                  {t("billing_email") || "Billing email"}
                </span>
                <input
                  type="email"
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  value={billingEmail}
                  onChange={(e) => setBillingEmail(e.target.value)}
                />
              </label>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="mb-1 block text-xs font-medium text-neutral-600">
                    {t("issue_date") || "Issue date"}
                  </span>
                  <input
                    type="date"
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    value={issueDate}
                    onChange={(e) => setIssueDate(e.target.value)}
                  />
                </label>
                <label className="block text-sm">
                  <span className="mb-1 block text-xs font-medium text-neutral-600">
                    {t("due_date") || "Due date"}
                  </span>
                  <input
                    type="date"
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                  />
                </label>
              </div>
              <label className="block text-sm">
                <span className="mb-1 block text-xs font-medium text-neutral-600">
                  {t("currency") || "Currency"}
                </span>
                <select
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
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
              <label className="block text-sm">
                <span className="mb-1 block text-xs font-medium text-neutral-600">
                  {t("work_order") || "Work order"}
                </span>
                <input
                  type="text"
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  value={workOrderTitle}
                  onChange={(e) => setWorkOrderTitle(e.target.value)}
                />
                {invoice.work_order_id && (
                  <Link
                    to={`/work-orders/${invoice.work_order_id}`}
                    className="mt-1 inline-block text-xs text-primary-700 hover:underline"
                  >
                    {t("view_work_order") || "View work order"}
                  </Link>
                )}
              </label>
              <div className="rounded-md border border-neutral-200 p-3">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  {t("invoice_charges") || "Charges"}
                </h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <label className="block text-sm">
                    <span className="mb-1 block text-xs font-medium text-neutral-600">
                      {t("labor_hours") || "Labor hours"}
                    </span>
                    <input
                      type="number"
                      min="0"
                      step="0.25"
                      className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                      value={laborHours}
                      onChange={(e) => setLaborHours(e.target.value)}
                      disabled={!editable}
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block text-xs font-medium text-neutral-600">
                      {t("labor_rate") || "Labor rate (per hour)"}
                    </span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                      value={laborRate}
                      onChange={(e) => setLaborRate(e.target.value)}
                      disabled={!editable}
                    />
                  </label>
                  <label className="block text-sm sm:col-span-2">
                    <span className="mb-1 block text-xs font-medium text-neutral-600">
                      {t("service_fee") || "Service fee"}
                    </span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                      value={serviceFee}
                      onChange={(e) => setServiceFee(e.target.value)}
                      disabled={!editable}
                    />
                  </label>
                </div>
                <p className="mt-2 text-xs text-neutral-500">
                  {t("labor_amount") || "Labor amount"}:{" "}
                  {formatMoneyAmount(String(laborAmountPreview.toFixed(2)), currency)}
                </p>
              </div>
              <label className="block text-sm">
                <span className="mb-1 block text-xs font-medium text-neutral-600">{t("notes") || "Notes"}</span>
                <textarea
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder={t("invoice_notes_placeholder") || ""}
                />
              </label>
              <div className="rounded-md bg-neutral-50 p-3 text-sm">
                <div className="flex justify-between gap-4">
                  <span className="text-neutral-500">{t("subtotal") || "Subtotal"}</span>
                  <span>{formatMoneyAmount(invoice.subtotal_sar, currency)}</span>
                </div>
                <div className="mt-1 flex justify-between gap-4">
                  <span className="text-neutral-500">{t("tax") || "Tax"}</span>
                  <span>{formatMoneyAmount(invoice.tax_sar, currency)}</span>
                </div>
                <div className="mt-2 flex justify-between gap-4 border-t border-neutral-200 pt-2 font-semibold">
                  <span>{t("total")}</span>
                  <span>{formatMoneyAmount(invoice.total_sar, currency)}</span>
                </div>
              </div>
              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-neutral-800 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                {saving ? t("loading") : t("save")}
              </button>
            </form>
          ) : (
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("billing_email") || "Billing email"}</dt>
                <dd>{billingEmail || "—"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("issue_date") || "Issue date"}</dt>
                <dd>{issueDate || "—"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("due_date") || "Due date"}</dt>
                <dd>{dueDate || "—"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("currency") || "Currency"}</dt>
                <dd>{currency}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("work_order")}</dt>
                <dd>{workOrderTitle || "—"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("labor_hours") || "Labor hours"}</dt>
                <dd>{laborHours || "0"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("labor_rate") || "Labor rate"}</dt>
                <dd>{formatMoneyAmount(laborRate || "0", currency)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("labor_amount") || "Labor amount"}</dt>
                <dd>{formatMoneyAmount(invoice.labor_amount_sar ?? "0", currency)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-neutral-500">{t("service_fee") || "Service fee"}</dt>
                <dd>{formatMoneyAmount(serviceFee || "0", currency)}</dd>
              </div>
              <div className="flex justify-between gap-4 border-t border-neutral-100 pt-2">
                <dt className="text-neutral-500">{t("total")}</dt>
                <dd className="font-semibold">{formatMoneyAmount(invoice.total_sar, currency)}</dd>
              </div>
              {notes && (
                <div className="border-t border-neutral-100 pt-2">
                  <dt className="text-neutral-500">{t("notes") || "Notes"}</dt>
                  <dd className="mt-1 whitespace-pre-wrap">{notes}</dd>
                </div>
              )}
            </dl>
          )}
        </div>

        {canAdmin && (
          <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
            <h2 className="text-base font-semibold text-neutral-800">{t("actions")}</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {invoice.status === "draft" && (
                <button
                  type="button"
                  disabled={acting}
                  className="rounded-md border border-primary-600 px-3 py-2 text-sm text-primary-700 disabled:opacity-50"
                  onClick={() => void recalculateFromWorkOrder()}
                >
                  {t("recalculate_invoice") || "Recalculate from work order"}
                </button>
              )}
              {invoice.status === "draft" && (
                <button
                  type="button"
                  disabled={acting}
                  className="rounded-md bg-success-dark px-3 py-2 text-sm text-white disabled:opacity-50"
                  onClick={() => void runAction("approve")}
                >
                  {t("approve_invoice") || "Approve"}
                </button>
              )}
              {(invoice.status === "draft" || invoice.status === "approved") && (
                <button
                  type="button"
                  disabled={acting}
                  className="rounded-md bg-primary-600 px-3 py-2 text-sm text-white disabled:opacity-50"
                  onClick={() => void runAction("send")}
                >
                  {t("send_email")}
                </button>
              )}
              {invoice.status === "sent" && (
                <button
                  type="button"
                  disabled={acting}
                  className="rounded-md bg-neutral-800 px-3 py-2 text-sm text-white disabled:opacity-50"
                  onClick={() => void runAction("mark-paid")}
                >
                  {t("mark_paid") || "Mark paid"}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
        <table className="min-w-full text-start text-sm">
          <thead className="bg-neutral-100 text-neutral-700">
            <tr>
              <th className="px-4 py-3 font-medium">{t("description")}</th>
              <th className="px-4 py-3 font-medium">{t("quantity") || "Qty"}</th>
              <th className="px-4 py-3 font-medium">{t("unit_price") || "Unit price"}</th>
              <th className="px-4 py-3 font-medium">{t("amount") || "Amount"}</th>
            </tr>
          </thead>
          <tbody>
            {invoice.line_items.map((line, idx) => (
              <tr key={idx} className="border-t border-neutral-200">
                <td className="px-4 py-3">{line.description}</td>
                <td className="px-4 py-3">{line.quantity}</td>
                <td className="px-4 py-3">
                  {formatMoneyAmount(line.unit_price_sar, currency)}
                </td>
                <td className="px-4 py-3 font-medium">
                  {formatMoneyAmount(line.amount_sar, currency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
