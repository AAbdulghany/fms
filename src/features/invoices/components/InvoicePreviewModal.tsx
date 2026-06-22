import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, openAuthenticatedBlob, resolveApiError } from "@/lib/api";
import { formatMoneyAmount } from "@/lib/formatCurrency";
import type { Invoice, WorkOrder, PaginatedWorkOrders } from "@/lib/types";

type Preview = {
  work_order_id: string;
  work_order_title: string;
  client_name: string;
  site_name: string;
  technician_name?: string | null;
  currency: string;
  labor_hours: string;
  labor_rate_sar: string;
  labor_amount_sar: string;
  parts: { description: string; quantity: string; amount_sar: string }[];
  service_fee_sar: string;
  emergency_surcharge_sar: string;
  subtotal_sar: string;
  tax_sar: string;
  total_sar: string;
  work_summary: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
  onGenerated: () => void;
};

function invoiceErrorMessage(
  err: unknown,
  t: (key: string) => string,
  lang: string
): string {
  return resolveApiError(err, t, lang, t("error_generic"));
}

export function InvoicePreviewModal({ open, onClose, onGenerated }: Props) {
  const { t, i18n } = useTranslation();
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [selectedWoId, setSelectedWoId] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [generated, setGenerated] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setPreview(null);
    setGenerated(null);
    setSelectedWoId("");
    setError(null);
    void apiFetch<PaginatedWorkOrders>("/work-orders?page_size=100").then((res) => {
      setWorkOrders(res.data.filter((wo) => ["verified", "closed"].includes(wo.status)));
    });
  }, [open]);

  useEffect(() => {
    if (!selectedWoId) {
      setPreview(null);
      setError(null);
      return;
    }
    setPreviewLoading(true);
    setError(null);
    void apiFetch<Preview>(`/work-orders/${selectedWoId}/invoice-preview`)
      .then((data) => {
        setPreview(data);
        setError(null);
      })
      .catch((e) => {
        setPreview(null);
        setError(invoiceErrorMessage(e, t, i18n.language));
      })
      .finally(() => setPreviewLoading(false));
  }, [selectedWoId, t, i18n.language]);

  if (!open) return null;

  async function onConfirm(e: FormEvent) {
    e.preventDefault();
    if (!selectedWoId) return;
    setLoading(true);
    setError(null);
    try {
      const inv = await apiFetch<Invoice>(`/work-orders/${selectedWoId}/generate-invoice`, { method: "POST" });
      setGenerated(inv);
      onGenerated();
    } catch (err) {
      setError(invoiceErrorMessage(err, t, i18n.language));
    } finally {
      setLoading(false);
    }
  }

  async function printPdf() {
    if (!generated) return;
    setError(null);
    try {
      await openAuthenticatedBlob(`/invoices/${generated.id}/pdf?inline=true`);
    } catch (err) {
      setError(invoiceErrorMessage(err, t, i18n.language));
    }
  }

  async function sendInvoice() {
    if (!generated) return;
    setLoading(true);
    try {
      await apiFetch(`/invoices/${generated.id}/send`, { method: "POST" });
      onClose();
    } catch (err) {
      setError(invoiceErrorMessage(err, t, i18n.language));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog">
        <h2 className="mb-4 text-xl font-bold">{t("generate_invoice")}</h2>
        {!generated ? (
          <form onSubmit={onConfirm} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">{t("select_work_order")}</label>
              <select
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
            {previewLoading && (
              <p className="text-sm text-neutral-500">{t("loading")}</p>
            )}
            {preview && (
              <div className="rounded-lg border border-neutral-200 p-4 text-sm space-y-2">
                <p>
                  <strong>{preview.work_order_title}</strong> — {preview.client_name} / {preview.site_name}
                </p>
                <p>
                  {t("labor")}: {preview.labor_hours}h @ {formatMoneyAmount(preview.labor_rate_sar, preview.currency)}/h —{" "}
                  {formatMoneyAmount(preview.labor_amount_sar, preview.currency)}
                </p>
                {Number(preview.service_fee_sar) > 0 && (
                  <p>
                    {t("service_fee")}: {formatMoneyAmount(preview.service_fee_sar, preview.currency)}
                  </p>
                )}
                {preview.parts.map((p, i) => (
                  <p key={i}>
                    {p.description} × {p.quantity} — {formatMoneyAmount(p.amount_sar, preview.currency)}
                  </p>
                ))}
                <p className="font-semibold">
                  {t("total")}: {formatMoneyAmount(preview.total_sar, preview.currency)}
                </p>
                {preview.work_summary && (
                  <p className="text-neutral-600">{preview.work_summary.slice(0, 200)}</p>
                )}
              </div>
            )}
            {error && <p className="text-sm text-error-main">{error}</p>}
            <div className="flex justify-end gap-2">
              <button type="button" className="rounded-md px-4 py-2 text-sm hover:bg-neutral-100" onClick={onClose}>
                {t("cancel")}
              </button>
              <button
                type="submit"
                disabled={loading || !preview}
                className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                {t("confirm_generate")}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <p className="text-sm">
              {t("invoice_created")} #{generated.number}
            </p>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="rounded-md bg-neutral-100 px-4 py-2 text-sm" onClick={printPdf}>
                {t("print")}
              </button>
              <button
                type="button"
                className="rounded-md bg-primary-600 px-4 py-2 text-sm text-white"
                onClick={() => void sendInvoice()}
                disabled={loading}
              >
                {t("send_email")}
              </button>
              <button type="button" className="rounded-md px-4 py-2 text-sm" onClick={onClose}>
                {t("close")}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
