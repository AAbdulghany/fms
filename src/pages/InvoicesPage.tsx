import { useEffect, useState, type MouseEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch, downloadAuthenticatedFile, resolveApiError } from "../lib/api";
import type { Invoice } from "../lib/types";
import { formatMoneyAmount } from "../lib/formatCurrency";
import { InvoicePreviewModal } from "../components/InvoicePreviewModal";

export function InvoicesPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [rows, setRows] = useState<Invoice[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [generateOpen, setGenerateOpen] = useState(false);

  const loadInvoices = () => {
    void (async () => {
      try {
        const res = await apiFetch<Invoice[]>("/invoices");
        setRows(res);
      } catch (e) {
        setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
      }
    })();
  };

  useEffect(() => {
    loadInvoices();
  }, []);

  async function handleDownload(inv: Invoice, e: MouseEvent) {
    e.stopPropagation();
    try {
      await downloadAuthenticatedFile(`/invoices/${inv.id}/pdf`, `invoice-${inv.number}.pdf`);
    } catch (error) {
      setErr(resolveApiError(error, t, i18n.language, t("error_generic")));
    }
  }

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

      {err && <p className="rounded-md bg-error-light px-3 py-2 text-sm text-error-dark">{err}</p>}

      <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
        <table className="min-w-full text-start text-sm">
          <thead className="bg-neutral-100 text-neutral-700">
            <tr>
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">{t("status")}</th>
              <th className="px-4 py-3 font-medium">{t("invoice_currency")} / Total</th>
              <th className="px-4 py-3 font-medium">{t("actions")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((inv) => (
              <tr
                key={inv.id}
                className="cursor-pointer border-t border-neutral-200 transition-colors hover:bg-neutral-50"
                onClick={() => navigate(`/invoices/${inv.id}`)}
              >
                <td className="px-4 py-3 font-mono text-xs">{inv.number}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      inv.status === "paid"
                        ? "bg-success-light text-success-dark"
                        : inv.status === "draft"
                          ? "bg-neutral-200 text-neutral-600"
                          : "bg-warning-light text-warning-dark"
                    }`}
                  >
                    {inv.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {formatMoneyAmount(inv.total_sar, inv.currency || "SAR")}
                </td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    className="me-3 text-xs text-primary-600 hover:underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/invoices/${inv.id}`);
                    }}
                  >
                    {t("view") || "View"}
                  </button>
                  <button
                    type="button"
                    className="text-xs text-primary-600 hover:underline"
                    onClick={(e) => void handleDownload(inv, e)}
                  >
                    {t("download") || "Download"}
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-sm text-neutral-500">
                  {t("no_results")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <InvoicePreviewModal
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        onGenerated={() => loadInvoices()}
      />
    </div>
  );
}
