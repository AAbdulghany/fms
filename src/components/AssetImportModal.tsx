import { useState } from "react";
import { useTranslation } from "react-i18next";

type PreviewRow = {
  row: number;
  site_code: string;
  name: string;
  category: string;
  serial?: string | null;
  status: string;
  errors: string[];
};

type Props = {
  open: boolean;
  onClose: () => void;
  onDone: () => void;
};

export function AssetImportModal({ open, onClose, onDone }: Props) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<{ valid_count: number; error_count: number; rows: PreviewRow[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function runPreview() {
    if (!file) return;
    setLoading(true);
    setError(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/assets/import/preview", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      setPreview(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  async function commitImport() {
    if (!file || !preview || preview.error_count > 0) return;
    setLoading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("/api/v1/assets/import", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      onDone();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl">
        <h2 className="mb-4 text-xl font-bold">{t("import_csv") || "Import CSV"}</h2>
        <input type="file" accept=".csv" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setPreview(null); }} />
        <div className="mt-4 flex gap-2">
          <button type="button" className="rounded-md bg-neutral-100 px-4 py-2 text-sm" onClick={() => void runPreview()} disabled={!file || loading}>
            {t("preview") || "Preview"}
          </button>
        </div>
        {preview && (
          <div className="mt-4">
            <p className="text-sm">{preview.valid_count} valid, {preview.error_count} errors</p>
            <table className="mt-2 w-full text-xs">
              <tbody>
                {preview.rows.slice(0, 20).map((r) => (
                  <tr key={r.row} className={r.status === "error" ? "text-error-main" : ""}>
                    <td className="py-1">{r.row}</td>
                    <td>{r.site_code}</td>
                    <td>{r.name}</td>
                    <td>{r.errors.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {preview.error_count === 0 && (
              <button type="button" className="mt-4 rounded-md bg-primary-600 px-4 py-2 text-sm text-white" onClick={() => void commitImport()} disabled={loading}>
                {t("import") || "Import"}
              </button>
            )}
          </div>
        )}
        {error && <p className="mt-2 text-sm text-error-main">{error}</p>}
        <button type="button" className="mt-4 text-sm text-neutral-600" onClick={onClose}>{t("close")}</button>
      </div>
    </div>
  );
}
