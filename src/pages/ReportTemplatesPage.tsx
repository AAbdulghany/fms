import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";
import { CategoryObservationsEditor } from "../components/CategoryObservationsEditor";

type TemplateRow = {
  id: string;
  name: string;
  code?: string | null;
  version?: number;
};

type SyncResult = { created: number; updated: number; unchanged: number };

export default function ReportTemplatesPage() {
  const { t } = useTranslation();
  const [templates, setTemplates] = useState<TemplateRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [editorTemplate, setEditorTemplate] = useState<TemplateRow | null>(null);

  const load = async () => {
    setError(null);
    try {
      const data = await apiFetch<TemplateRow[]>("/report-templates");
      setTemplates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [t]);

  async function syncStandard() {
    setSyncing(true);
    setError(null);
    setMsg(null);
    try {
      const result = await apiFetch<SyncResult>("/report-templates/sync-standard", { method: "POST" });
      setMsg(
        t("template_sync_done", {
          created: result.created,
          updated: result.updated,
          unchanged: result.unchanged,
        }) ||
          `Sync complete — created: ${result.created}, updated: ${result.updated}, unchanged: ${result.unchanged}`
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("error"));
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900">{t("report_templates")}</h1>
          <p className="mt-1 text-sm text-neutral-500">{t("report_templates_admin_desc") || t("report_templates_desc")}</p>
        </div>
        <button
          type="button"
          disabled={syncing}
          onClick={() => void syncStandard()}
          className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          {syncing ? t("loading") : t("sync_std_template") || "Sync STD-INSP v2"}
        </button>
      </div>

      {msg && <p className="rounded-md bg-success-light px-4 py-3 text-sm text-success-dark">{msg}</p>}
      {error && (
        <div className="rounded-lg border border-error-main bg-error-light px-4 py-3 text-sm text-error-dark">
          {error}
        </div>
      )}

      {templates.length === 0 && !error ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-12 text-center shadow-sm">
          <p className="text-sm font-medium text-neutral-600">{t("no_report_templates")}</p>
          <button
            type="button"
            className="mt-4 text-sm text-primary-600 hover:underline"
            onClick={() => void syncStandard()}
          >
            {t("sync_std_template") || "Sync STD-INSP v2"}
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-neutral-200 bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("template_name")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("template_code")}
                  </th>
                  <th className="px-6 py-3 text-start text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("version") || "Version"}
                  </th>
                  <th className="px-6 py-3 text-end text-xs font-medium uppercase tracking-wider text-neutral-500">
                    {t("actions") || "Actions"}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {templates.map((tpl) => (
                  <tr key={tpl.id} className="transition-colors hover:bg-neutral-50">
                    <td className="px-6 py-4">
                      <span className="text-sm font-semibold text-neutral-900">{tpl.name}</span>
                    </td>
                    <td className="px-6 py-4">
                      {tpl.code ? (
                        <span className="font-mono text-sm text-neutral-700">{tpl.code}</span>
                      ) : (
                        <span className="text-sm text-neutral-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-600">v{tpl.version ?? 1}</td>
                    <td className="px-6 py-4 text-end">
                      <button
                        type="button"
                        className="text-sm font-medium text-primary-700 hover:underline"
                        onClick={() => setEditorTemplate(tpl)}
                      >
                        {t("edit_observations") || "Edit observations"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {editorTemplate && (
        <CategoryObservationsEditor
          templateId={editorTemplate.id}
          templateName={editorTemplate.name}
          open
          onClose={() => setEditorTemplate(null)}
          onSaved={() => void load()}
        />
      )}
    </div>
  );
}
