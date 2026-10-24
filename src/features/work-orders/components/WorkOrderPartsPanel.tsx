import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";

type Part = { id: string; sku: string; name: string; unit_cost_sar: string | number };
type WoPart = {
  id: string;
  part_id: string;
  quantity: string | number;
  unit_cost_sar: string | number;
  part_sku?: string | null;
  part_name?: string | null;
};

type Props = { workOrderId: string; canEdit: boolean };

export function WorkOrderPartsPanel({ workOrderId, canEdit }: Props) {
  const { t, i18n } = useTranslation();
  const [catalog, setCatalog] = useState<Part[]>([]);
  const [lines, setLines] = useState<WoPart[]>([]);
  const [partId, setPartId] = useState("");
  const [qty, setQty] = useState("1");
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const [parts, woParts] = await Promise.all([
        apiFetch<Part[]>("/parts-catalog"),
        apiFetch<WoPart[]>(`/work-orders/${workOrderId}/parts`),
      ]);
      setCatalog(parts);
      setLines(woParts);
      if (!partId && parts[0]) setPartId(parts[0].id);
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }, [workOrderId, t, i18n.language, partId]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workOrderId]);

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    if (!partId) return;
    try {
      await apiFetch(`/work-orders/${workOrderId}/parts`, {
        method: "POST",
        body: JSON.stringify({ part_id: partId, quantity: qty }),
      });
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function onRemove(lineId: string) {
    try {
      await apiFetch(`/work-orders/${workOrderId}/parts/${lineId}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  return (
    <section className="mt-6 rounded-lg border border-neutral-200 bg-white p-4" data-testid="wo-parts-panel">
      <h2 className="mb-3 text-sm font-semibold text-neutral-900">{t("parts_used_section")}</h2>
      {err && <p className="mb-2 text-sm text-red-600">{err}</p>}
      {canEdit && (
        <form onSubmit={onAdd} className="mb-3 flex flex-wrap gap-2">
          <select
            className="rounded border border-neutral-300 px-2 py-1.5 text-sm"
            value={partId}
            onChange={(e) => setPartId(e.target.value)}
          >
            {catalog.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} — {p.name}
              </option>
            ))}
          </select>
          <input
            className="w-20 rounded border border-neutral-300 px-2 py-1.5 text-sm"
            type="number"
            min="0.001"
            step="0.001"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
          <button type="submit" className="rounded bg-neutral-900 px-3 py-1.5 text-sm text-white">
            {t("add_part")}
          </button>
        </form>
      )}
      <ul className="divide-y text-sm">
        {lines.length === 0 && <li className="py-2 text-neutral-500">{t("no_parts_on_wo")}</li>}
        {lines.map((l) => (
          <li key={l.id} className="flex items-center justify-between py-2">
            <span>
              {l.part_sku} · {l.part_name} × {l.quantity}
            </span>
            {canEdit && (
              <button type="button" className="text-red-600" onClick={() => void onRemove(l.id)}>
                {t("remove")}
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
