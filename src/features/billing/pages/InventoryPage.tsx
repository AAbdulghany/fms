/**
 * Inventory — spare parts, spare whole assets, raw materials.
 * One-by-one create, CSV bulk import, and inline field edits.
 */
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";

type InvItem = {
  id: string;
  sku: string;
  name: string;
  name_en: string;
  name_ar: string;
  unit_cost_sar: string | number;
  kind: string;
  qty_on_hand: string | number;
};

type KindFilter = "all" | "part" | "spare_asset" | "raw_material";
type Kind = "part" | "spare_asset" | "raw_material";

function parseCsv(text: string): {
  sku: string;
  name_en: string;
  name_ar: string;
  unit_cost_sar: string;
  kind: string;
  qty_on_hand: string;
}[] {
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length < 2) return [];
  const header = lines[0].toLowerCase().split(",").map((h) => h.trim());
  const idx = (name: string) => header.indexOf(name);
  const iSku = idx("sku");
  const iEn = idx("name_en") >= 0 ? idx("name_en") : idx("name");
  const iAr = idx("name_ar");
  const iCost = idx("unit_cost_sar") >= 0 ? idx("unit_cost_sar") : idx("cost");
  const iKind = idx("kind");
  const iQty = idx("qty_on_hand") >= 0 ? idx("qty_on_hand") : idx("qty");
  const out = [];
  for (const line of lines.slice(1)) {
    const cols = line.split(",").map((c) => c.trim());
    const sku = iSku >= 0 ? cols[iSku] : cols[0];
    if (!sku) continue;
    out.push({
      sku,
      name_en: iEn >= 0 ? cols[iEn] || "" : "",
      name_ar: iAr >= 0 ? cols[iAr] || "" : "",
      unit_cost_sar: iCost >= 0 ? cols[iCost] || "0" : "0",
      kind: iKind >= 0 ? cols[iKind] || "part" : "part",
      qty_on_hand: iQty >= 0 ? cols[iQty] || "0" : "0",
    });
  }
  return out;
}

export default function InventoryPage() {
  const { t, i18n } = useTranslation();
  const [rows, setRows] = useState<InvItem[]>([]);
  const [filter, setFilter] = useState<KindFilter>("all");
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [bulkText, setBulkText] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<InvItem>>({});

  const [sku, setSku] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [nameAr, setNameAr] = useState("");
  const [cost, setCost] = useState("0");
  const [qty, setQty] = useState("0");
  const [kind, setKind] = useState<Kind>("part");

  const load = useCallback(async () => {
    setErr(null);
    try {
      setRows(await apiFetch<InvItem[]>("/parts-catalog"));
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }, [t, i18n.language]);

  useEffect(() => {
    void load();
  }, [load]);

  const visible = useMemo(() => {
    if (filter === "all") return rows;
    return rows.filter((r) => r.kind === filter);
  }, [rows, filter]);

  function kindLabel(k: string) {
    if (k === "raw_material") return t("inventory_kind_raw");
    if (k === "spare_asset") return t("inventory_kind_spare_asset") || "Spare asset";
    return t("inventory_kind_part");
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    try {
      await apiFetch("/parts-catalog", {
        method: "POST",
        json: {
          sku: sku.trim(),
          name_en: nameEn.trim(),
          name_ar: nameAr.trim(),
          unit_cost_sar: cost,
          kind,
          qty_on_hand: qty,
        },
      });
      setSku("");
      setNameEn("");
      setNameAr("");
      setCost("0");
      setQty("0");
      setMsg(t("saved") || "Saved");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function onBulk(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    const items = parseCsv(bulkText);
    if (!items.length) {
      setErr(t("parts_bulk_empty") || "No rows parsed");
      return;
    }
    try {
      const result = await apiFetch<{ created: number; updated: number; skipped: number }>(
        "/parts-catalog/bulk",
        { method: "POST", json: { items } }
      );
      setMsg(
        t("parts_bulk_result", {
          created: result.created,
          updated: result.updated,
          skipped: result.skipped,
        }) || `Created ${result.created}, updated ${result.updated}`
      );
      setBulkText("");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  function startEdit(item: InvItem) {
    setEditingId(item.id);
    setEditDraft({ ...item });
  }

  async function saveEdit() {
    if (!editingId) return;
    setErr(null);
    try {
      await apiFetch(`/parts-catalog/${editingId}`, {
        method: "PATCH",
        json: {
          name_en: editDraft.name_en,
          name_ar: editDraft.name_ar,
          unit_cost_sar: editDraft.unit_cost_sar,
          kind: editDraft.kind,
          qty_on_hand: editDraft.qty_on_hand,
        },
      });
      setEditingId(null);
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  const lang = i18n.language;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4" data-testid="inventory-page">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">{t("inventory")}</h1>
        <p className="mt-1 text-sm text-neutral-600">{t("inventory_help")}</p>
      </div>

      {err && <p className="text-sm text-red-600">{err}</p>}
      {msg && <p className="text-sm text-emerald-700">{msg}</p>}

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["all", t("all") || "All"],
            ["part", t("inventory_kind_part")],
            ["spare_asset", t("inventory_kind_spare_asset") || "Spare asset"],
            ["raw_material", t("inventory_kind_raw")],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={`rounded-lg px-3 py-1.5 text-sm ${
              filter === id ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <form
        onSubmit={onCreate}
        className="grid gap-3 rounded-lg border border-neutral-200 bg-white p-4 sm:grid-cols-3"
      >
        <h2 className="sm:col-span-3 text-sm font-semibold text-neutral-800">
          {t("add_inventory_item") || "Add item"}
        </h2>
        <input
          required
          className="rounded border px-3 py-2 text-sm"
          placeholder="SKU"
          value={sku}
          onChange={(e) => setSku(e.target.value)}
        />
        <select
          className="rounded border px-3 py-2 text-sm"
          value={kind}
          onChange={(e) => setKind(e.target.value as Kind)}
        >
          <option value="part">{t("inventory_kind_part")}</option>
          <option value="spare_asset">{t("inventory_kind_spare_asset") || "Spare asset (replacement)"}</option>
          <option value="raw_material">{t("inventory_kind_raw")}</option>
        </select>
        <input
          className="rounded border px-3 py-2 text-sm"
          placeholder={t("name_en") || "Name EN"}
          value={nameEn}
          onChange={(e) => setNameEn(e.target.value)}
        />
        <input
          dir="rtl"
          className="rounded border px-3 py-2 text-sm"
          placeholder={t("name_ar") || "Name AR"}
          value={nameAr}
          onChange={(e) => setNameAr(e.target.value)}
        />
        <input
          type="number"
          step="0.01"
          className="rounded border px-3 py-2 text-sm"
          placeholder={t("unit_cost") || "Unit cost"}
          value={cost}
          onChange={(e) => setCost(e.target.value)}
        />
        <input
          type="number"
          step="0.01"
          className="rounded border px-3 py-2 text-sm"
          placeholder={t("qty_on_hand") || "Qty"}
          value={qty}
          onChange={(e) => setQty(e.target.value)}
        />
        <div className="sm:col-span-3">
          <button type="submit" className="rounded bg-neutral-900 px-4 py-2 text-sm text-white">
            {t("save")}
          </button>
        </div>
      </form>

      <form onSubmit={onBulk} className="space-y-2 rounded-lg border border-neutral-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-neutral-800">
          {t("import_csv") || "Import CSV"}
        </h2>
        <p className="text-xs text-neutral-500">
          sku,name_en,name_ar,unit_cost_sar,kind,qty_on_hand — kind = part | spare_asset | raw_material
        </p>
        <textarea
          className="h-28 w-full rounded border px-3 py-2 font-mono text-xs"
          value={bulkText}
          onChange={(e) => setBulkText(e.target.value)}
          placeholder={"sku,name_en,name_ar,unit_cost_sar,kind,qty_on_hand\nFILT-01,HEPA Filter,فلتر,120,part,10"}
        />
        <button type="submit" className="rounded border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-50">
          {t("import_csv") || "Import CSV"}
        </button>
      </form>

      <div className="overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="border-b bg-neutral-50 text-xs uppercase text-neutral-500">
            <tr>
              <th className="px-3 py-2 text-start">SKU</th>
              <th className="px-3 py-2 text-start">{t("name")}</th>
              <th className="px-3 py-2 text-start">{t("inventory_kind")}</th>
              <th className="px-3 py-2 text-start">{t("unit_cost") || "Cost"}</th>
              <th className="px-3 py-2 text-start">{t("qty_on_hand") || "Qty"}</th>
              <th className="px-3 py-2 text-start">{t("actions") || "Actions"}</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {visible.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-neutral-400">
                  {t("no_results") || "No items"}
                </td>
              </tr>
            ) : (
              visible.map((item) => {
                const editing = editingId === item.id;
                return (
                  <tr key={item.id}>
                    <td className="px-3 py-2 font-mono text-xs">{item.sku}</td>
                    <td className="px-3 py-2">
                      {editing ? (
                        <div className="flex flex-col gap-1">
                          <input
                            className="rounded border px-2 py-1 text-xs"
                            value={String(editDraft.name_en ?? "")}
                            onChange={(e) => setEditDraft((d) => ({ ...d, name_en: e.target.value }))}
                          />
                          <input
                            dir="rtl"
                            className="rounded border px-2 py-1 text-xs"
                            value={String(editDraft.name_ar ?? "")}
                            onChange={(e) => setEditDraft((d) => ({ ...d, name_ar: e.target.value }))}
                          />
                        </div>
                      ) : lang.startsWith("ar") ? (
                        item.name_ar || item.name_en || item.name
                      ) : (
                        item.name_en || item.name
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {editing ? (
                        <select
                          className="rounded border px-2 py-1 text-xs"
                          value={String(editDraft.kind ?? "part")}
                          onChange={(e) => setEditDraft((d) => ({ ...d, kind: e.target.value }))}
                        >
                          <option value="part">{t("inventory_kind_part")}</option>
                          <option value="spare_asset">
                            {t("inventory_kind_spare_asset") || "Spare asset"}
                          </option>
                          <option value="raw_material">{t("inventory_kind_raw")}</option>
                        </select>
                      ) : (
                        kindLabel(item.kind)
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {editing ? (
                        <input
                          type="number"
                          step="0.01"
                          className="w-24 rounded border px-2 py-1 text-xs"
                          value={String(editDraft.unit_cost_sar ?? 0)}
                          onChange={(e) =>
                            setEditDraft((d) => ({ ...d, unit_cost_sar: e.target.value }))
                          }
                        />
                      ) : (
                        item.unit_cost_sar
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {editing ? (
                        <input
                          type="number"
                          step="0.01"
                          className="w-20 rounded border px-2 py-1 text-xs"
                          value={String(editDraft.qty_on_hand ?? 0)}
                          onChange={(e) =>
                            setEditDraft((d) => ({ ...d, qty_on_hand: e.target.value }))
                          }
                        />
                      ) : (
                        item.qty_on_hand
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {editing ? (
                        <div className="flex gap-1">
                          <button
                            type="button"
                            className="rounded bg-neutral-900 px-2 py-1 text-xs text-white"
                            onClick={() => void saveEdit()}
                          >
                            {t("save")}
                          </button>
                          <button
                            type="button"
                            className="rounded border px-2 py-1 text-xs"
                            onClick={() => setEditingId(null)}
                          >
                            {t("cancel")}
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="rounded border px-2 py-1 text-xs hover:bg-neutral-50"
                          onClick={() => startEdit(item)}
                        >
                          {t("edit") || "Edit"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
