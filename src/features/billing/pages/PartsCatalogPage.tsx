import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch, resolveApiError } from "@/lib/api";

type Part = {
  id: string;
  sku: string;
  name: string;
  name_en?: string;
  name_ar?: string;
  unit_cost_sar: string | number;
};

type BulkResult = { created: number; updated: number; skipped: number; errors: string[] };

function partLabel(p: Part, lang: string): string {
  if (lang.startsWith("ar")) return p.name_ar || p.name || p.name_en || p.sku;
  return p.name_en || p.name || p.name_ar || p.sku;
}

function parseCsv(text: string): Array<{
  sku: string;
  name_en: string;
  name_ar: string;
  unit_cost_sar: string;
}> {
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
  const iCost = idx("unit_cost_sar");
  const rows = [];
  for (const line of lines.slice(1)) {
    const cols = line.split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
    const sku = iSku >= 0 ? cols[iSku] : "";
    if (!sku) continue;
    rows.push({
      sku,
      name_en: iEn >= 0 ? cols[iEn] || "" : "",
      name_ar: iAr >= 0 ? cols[iAr] || "" : "",
      unit_cost_sar: iCost >= 0 ? cols[iCost] || "0" : "0",
    });
  }
  return rows;
}

export default function PartsCatalogPage() {
  const { t, i18n } = useTranslation();
  const [parts, setParts] = useState<Part[]>([]);
  const [sku, setSku] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [nameAr, setNameAr] = useState("");
  const [cost, setCost] = useState("0");
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [bulkText, setBulkText] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      setParts(await apiFetch<Part[]>("/parts-catalog"));
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setLoading(false);
    }
  }, [t, i18n.language]);

  useEffect(() => {
    void load();
  }, [load]);

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
        },
      });
      setSku("");
      setNameEn("");
      setNameAr("");
      setCost("0");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function downloadTemplate() {
    setErr(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/parts-catalog/template.csv", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("template failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "parts-catalog-template.csv";
      a.click();
      URL.revokeObjectURL(url);
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
      setErr(t("parts_bulk_empty"));
      return;
    }
    try {
      const result = await apiFetch<BulkResult>("/parts-catalog/bulk", {
        method: "POST",
        json: { items },
      });
      setMsg(
        t("parts_bulk_result", {
          created: result.created,
          updated: result.updated,
          skipped: result.skipped,
        })
      );
      setBulkText("");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  const sorted = useMemo(
    () => [...parts].sort((a, b) => a.sku.localeCompare(b.sku)),
    [parts]
  );

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-neutral-900">{t("parts_catalog")}</h1>
      {err && <p className="text-sm text-red-600">{err}</p>}
      {msg && <p className="text-sm text-emerald-700">{msg}</p>}

      <form
        onSubmit={onCreate}
        className="grid gap-3 rounded-lg border border-neutral-200 bg-white p-4 sm:grid-cols-5"
      >
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          placeholder={t("sku")}
          value={sku}
          onChange={(e) => setSku(e.target.value)}
          required
        />
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          placeholder={t("name_en")}
          value={nameEn}
          onChange={(e) => setNameEn(e.target.value)}
          required
        />
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          placeholder={t("name_ar")}
          value={nameAr}
          onChange={(e) => setNameAr(e.target.value)}
          dir="rtl"
        />
        <input
          className="rounded border border-neutral-300 px-3 py-2 text-sm"
          type="number"
          step="0.01"
          min="0"
          placeholder={t("unit_cost")}
          value={cost}
          onChange={(e) => setCost(e.target.value)}
        />
        <button type="submit" className="rounded bg-neutral-900 px-3 py-2 text-sm font-medium text-white">
          {t("add_part")}
        </button>
      </form>

      <section className="space-y-3 rounded-lg border border-neutral-200 bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-neutral-900">{t("parts_bulk_title")}</h2>
          <button
            type="button"
            onClick={() => void downloadTemplate()}
            className="text-sm text-primary-700 underline"
          >
            {t("parts_download_template")}
          </button>
        </div>
        <p className="text-xs text-neutral-500">{t("parts_bulk_help")}</p>
        <form onSubmit={onBulk} className="space-y-2">
          <textarea
            className="h-28 w-full rounded border border-neutral-300 px-3 py-2 font-mono text-xs"
            placeholder={"sku,name_en,name_ar,unit_cost_sar"}
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
          />
          <button type="submit" className="rounded bg-neutral-800 px-3 py-2 text-sm text-white">
            {t("parts_bulk_import")}
          </button>
        </form>
      </section>

      {loading ? (
        <p className="text-sm text-neutral-500">{t("loading")}</p>
      ) : sorted.length === 0 ? (
        <p className="text-sm text-neutral-500">{t("parts_empty")}</p>
      ) : (
        <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
          {sorted.map((p) => (
            <li key={p.id} className="flex items-center justify-between gap-3 px-4 py-3 text-sm">
              <span>
                <span className="font-medium text-neutral-900">{p.sku}</span>
                <span className="ms-2 text-neutral-700">{partLabel(p, i18n.language)}</span>
                <span className="ms-2 block text-xs text-neutral-400 sm:inline">
                  EN: {p.name_en || p.name} · AR: {p.name_ar || "—"}
                </span>
              </span>
              <span className="tabular-nums text-neutral-800">{p.unit_cost_sar}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
