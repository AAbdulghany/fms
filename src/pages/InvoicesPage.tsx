import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import type { Invoice } from "../lib/types";
import { formatMoneyAmount } from "../lib/formatCurrency";

export function InvoicesPage() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<Invoice[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const res = await apiFetch<Invoice[]>("/invoices");
        setRows(res);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error");
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-neutral-900">{t("invoices")}</h1>
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
                <td className="px-4 py-3">{inv.status}</td>
                <td className="px-4 py-3">
                  {formatMoneyAmount(inv.total_sar, inv.currency || "SAR")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
