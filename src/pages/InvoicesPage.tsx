import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import type { Invoice, WorkOrder, PaginatedWorkOrders } from "../lib/types";
import { formatMoneyAmount } from "../lib/formatCurrency";

type GenerateInvoiceModalProps = {
  open: boolean;
  onClose: () => void;
  onGenerated: () => void;
};

function GenerateInvoiceModal({ open, onClose, onGenerated }: GenerateInvoiceModalProps) {
  const { t } = useTranslation();
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [selectedWoId, setSelectedWoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setFetching(true);
    void (async () => {
      try {
        const res = await apiFetch<PaginatedWorkOrders>(
          "/work-orders?page_size=100"
        );
        const eligible = res.data.filter((wo) =>
          ["verified", "closed", "completed"].includes(wo.status)
        );
        setWorkOrders(eligible);
      } catch {
        setWorkOrders([]);
      } finally {
        setFetching(false);
      }
    })();
  }, [open]);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedWoId) return;
    setLoading(true);
    setError(null);
    try {
      await apiFetch(`/work-orders/${selectedWoId}/generate-invoice`, {
        method: "POST",
      });
      setSelectedWoId("");
      onGenerated();
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
        <h2 className="mb-4 text-xl font-bold text-neutral-900">{t("generate_invoice")}</h2>
        {fetching ? (
          <div className="flex h-32 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
          </div>
        ) : workOrders.length === 0 ? (
          <p className="text-sm text-neutral-600">{t("no_eligible_work_orders")}</p>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("select_work_order")} *</label>
              <select
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={selectedWoId}
                onChange={(e) => setSelectedWoId(e.target.value)}
              >
                <option value="">{t("select_work_order")}</option>
                {workOrders.map((wo) => (
                  <option key={wo.id} value={wo.id}>
                    {wo.title || wo.id.slice(0, 8)} — {wo.status}
                  </option>
                ))}
              </select>
            </div>
            {error && <p className="text-sm text-error-main">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100" onClick={onClose}>
                {t("cancel")}
              </button>
              <button
                type="submit"
                disabled={loading || !selectedWoId}
                className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
              >
                {loading ? t("loading") : t("generate_invoice")}
              </button>
            </div>
          </form>
        )}
        {workOrders.length === 0 && !fetching && (
          <div className="mt-4 flex justify-end">
            <button type="button" className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100" onClick={onClose}>
              {t("close")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function InvoicesPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<Invoice[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [generateOpen, setGenerateOpen] = useState(false);

  const loadInvoices = () => {
    void (async () => {
      try {
        const res = await apiFetch<Invoice[]>("/invoices");
        setRows(res);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error");
      }
    })();
  };

  useEffect(() => {
    loadInvoices();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-neutral-900">{t("invoices")}</h1>
        <button
          type="button"
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          onClick={() => setGenerateOpen(true)}
        >
          + {t("generate_invoice")}
        </button>
      </div>
      {err && <p className="text-error-main">{err}</p>}
      <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
        <table className="min-w-full text-start text-sm">
          <thead className="bg-neutral-100 text-neutral-700">
            <tr>
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">{t("status")}</th>
              <th className="px-4 py-3 font-medium">{t("invoice_currency")} / Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((inv) => (
              <tr key={inv.id} className="border-t border-neutral-200">
                <td className="px-4 py-3 font-mono text-xs">{inv.number}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    inv.status === "paid" ? "bg-success-light text-success-dark"
                    : inv.status === "draft" ? "bg-neutral-200 text-neutral-600"
                    : "bg-warning-light text-warning-dark"
                  }`}>{inv.status}</span>
                </td>
                <td className="px-4 py-3">
                  {formatMoneyAmount(inv.total_sar, inv.currency || "SAR")}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-sm text-neutral-500">{t("no_results")}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <GenerateInvoiceModal
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        onGenerated={() => loadInvoices()}
      />
    </div>
  );
}
