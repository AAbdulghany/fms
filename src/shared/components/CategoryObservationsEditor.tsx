import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { ObservationFieldDef } from "@/lib/reportSchema";

type Props = {
  templateId: string;
  templateName: string;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
};

const DEFAULT_CATEGORY = "_default";

function emptyField(): ObservationFieldDef {
  return {
    id: `field_${Date.now()}`,
    type: "textarea",
    label: "",
    required: false,
    rows: 4,
    options: [],
  };
}

export function CategoryObservationsEditor({ templateId, templateName, open, onClose, onSaved }: Props) {
  const { t } = useTranslation();
  const [categories, setCategories] = useState<Record<string, ObservationFieldDef[]>>({});
  const [assetCategories, setAssetCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState(DEFAULT_CATEGORY);
  const [newCategory, setNewCategory] = useState("");
  const [fields, setFields] = useState<ObservationFieldDef[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [obs, cats] = await Promise.all([
        apiFetch<{ categories: Record<string, ObservationFieldDef[]> }>(
          `/report-templates/${templateId}/observations`
        ),
        apiFetch<string[]>("/report-templates/asset-categories"),
      ]);
      setCategories(obs.categories);
      setAssetCategories(cats);
      const initial = obs.categories[DEFAULT_CATEGORY] ?? [];
      setSelectedCategory(DEFAULT_CATEGORY);
      setFields(initial.length ? initial.map((f) => ({ ...f })) : []);
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }, [templateId, t]);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  useEffect(() => {
    if (!open) return;
    const catFields = categories[selectedCategory];
    setFields(catFields ? catFields.map((f) => ({ ...f })) : []);
  }, [selectedCategory, categories, open]);

  if (!open) return null;

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    setMsg(null);
    try {
      const cleaned = fields
        .filter((f) => f.label.trim())
        .map((f) => ({
          ...f,
          id: f.id.trim(),
          label: f.label.trim(),
          options: f.type === "checklist" ? (f.options ?? []).filter(Boolean) : undefined,
        }));
      const res = await apiFetch<{ categories: Record<string, ObservationFieldDef[]> }>(
        `/report-templates/${templateId}/observations/${encodeURIComponent(selectedCategory)}`,
        { method: "PUT", json: { fields: cleaned } }
      );
      setCategories(res.categories);
      setMsg(t("observations_saved") || "Observations saved");
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteCategory() {
    if (selectedCategory === DEFAULT_CATEGORY) return;
    if (!window.confirm(t("delete_category_confirm") || "Remove this category checklist?")) return;
    setErr(null);
    try {
      const res = await apiFetch<{ categories: Record<string, ObservationFieldDef[]> }>(
        `/report-templates/${templateId}/observations/${encodeURIComponent(selectedCategory)}`,
        { method: "DELETE" }
      );
      setCategories(res.categories);
      setSelectedCategory(DEFAULT_CATEGORY);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("error"));
    }
  }

  function addCategory() {
    const key = newCategory.trim();
    if (!key || categories[key]) return;
    setCategories((c) => ({ ...c, [key]: [] }));
    setSelectedCategory(key);
    setFields([]);
    setNewCategory("");
  }

  const categoryOptions = [
    DEFAULT_CATEGORY,
    ...Object.keys(categories).filter((k) => k !== DEFAULT_CATEGORY),
    ...assetCategories.filter((c) => !categories[c]),
  ];
  const uniqueCategories = Array.from(new Set(categoryOptions));

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/40" onMouseDown={onClose} />
      <div
        className="fixed left-1/2 top-8 z-50 max-h-[90vh] w-full max-w-3xl -translate-x-1/2 overflow-y-auto rounded-xl border border-neutral-200 bg-neutral-0 p-6 shadow-xl"
        role="dialog"
        aria-modal
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-neutral-900">
              {t("edit_observations") || "Edit observation checklist"}
            </h2>
            <p className="mt-1 text-sm text-neutral-500">{templateName}</p>
          </div>
          <button type="button" className="text-sm text-neutral-600 hover:text-neutral-900" onClick={onClose}>
            {t("close")}
          </button>
        </div>

        {loading ? (
          <p className="py-8 text-center text-sm text-neutral-500">{t("loading")}</p>
        ) : (
          <form onSubmit={(e) => void handleSave(e)} className="space-y-4">
            <div className="flex flex-wrap items-end gap-3">
              <div className="min-w-[12rem] flex-1">
                <label className="mb-1 block text-xs font-medium text-neutral-600">
                  {t("asset_category") || "Asset category"}
                </label>
                <select
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  {uniqueCategories.map((c) => (
                    <option key={c} value={c}>
                      {c === DEFAULT_CATEGORY ? t("default_checklist") || "Default (all assets)" : c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex min-w-[10rem] flex-1 gap-2">
                <input
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                  placeholder={t("new_category") || "New category…"}
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                />
                <button
                  type="button"
                  className="shrink-0 rounded-md border border-neutral-300 px-3 py-2 text-sm hover:bg-neutral-50"
                  onClick={addCategory}
                >
                  {t("add")}
                </button>
              </div>
            </div>

            <p className="text-xs text-neutral-500">
              {t("observations_editor_hint") ||
                "Customize checklist fields per asset category. Work orders use the matching category, otherwise the default."}
            </p>

            <div className="space-y-3">
              {fields.map((field, idx) => (
                <div key={field.id + idx} className="rounded-lg border border-neutral-200 p-3">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs text-neutral-500">{t("field_id") || "Field ID"}</label>
                      <input
                        className="w-full rounded-md border border-neutral-300 px-2 py-1.5 font-mono text-sm"
                        value={field.id}
                        onChange={(e) => {
                          const next = [...fields];
                          next[idx] = { ...next[idx], id: e.target.value };
                          setFields(next);
                        }}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-neutral-500">{t("field_type") || "Type"}</label>
                      <select
                        className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm"
                        value={field.type}
                        onChange={(e) => {
                          const next = [...fields];
                          next[idx] = {
                            ...next[idx],
                            type: e.target.value as ObservationFieldDef["type"],
                          };
                          setFields(next);
                        }}
                      >
                        <option value="textarea">Text area</option>
                        <option value="text">Text</option>
                        <option value="checklist">Checklist</option>
                      </select>
                    </div>
                    <div className="sm:col-span-2">
                      <label className="mb-1 block text-xs text-neutral-500">{t("label") || "Label"}</label>
                      <input
                        required
                        className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm"
                        value={field.label}
                        onChange={(e) => {
                          const next = [...fields];
                          next[idx] = { ...next[idx], label: e.target.value };
                          setFields(next);
                        }}
                      />
                    </div>
                    {field.type === "checklist" && (
                      <div className="sm:col-span-2">
                        <label className="mb-1 block text-xs text-neutral-500">
                          {t("options_comma") || "Options (comma-separated)"}
                        </label>
                        <input
                          className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm"
                          value={(field.options ?? []).join(", ")}
                          onChange={(e) => {
                            const next = [...fields];
                            next[idx] = {
                              ...next[idx],
                              options: e.target.value.split(",").map((o) => o.trim()).filter(Boolean),
                            };
                            setFields(next);
                          }}
                        />
                      </div>
                    )}
                    <label className="flex items-center gap-2 text-sm text-neutral-700">
                      <input
                        type="checkbox"
                        checked={!!field.required}
                        onChange={(e) => {
                          const next = [...fields];
                          next[idx] = { ...next[idx], required: e.target.checked };
                          setFields(next);
                        }}
                      />
                      {t("required") || "Required"}
                    </label>
                  </div>
                  <button
                    type="button"
                    className="mt-2 text-xs text-error-main hover:underline"
                    onClick={() => setFields(fields.filter((_, i) => i !== idx))}
                  >
                    {t("remove") || "Remove"}
                  </button>
                </div>
              ))}
            </div>

            <button
              type="button"
              className="text-sm text-primary-600 hover:underline"
              onClick={() => setFields([...fields, emptyField()])}
            >
              + {t("add_field") || "Add field"}
            </button>

            {msg && <p className="rounded-md bg-success-light px-3 py-2 text-sm text-success-dark">{msg}</p>}
            {err && <p className="rounded-md bg-error-light px-3 py-2 text-sm text-error-dark">{err}</p>}

            <div className="flex flex-wrap justify-between gap-2 border-t border-neutral-100 pt-4">
              {selectedCategory !== DEFAULT_CATEGORY && categories[selectedCategory] && (
                <button
                  type="button"
                  className="rounded-md border border-error-main px-3 py-2 text-sm text-error-main"
                  onClick={() => void handleDeleteCategory()}
                >
                  {t("delete_category") || "Delete category"}
                </button>
              )}
              <div className="ms-auto flex gap-2">
                <button type="button" className="rounded-md px-4 py-2 text-sm text-neutral-600" onClick={onClose}>
                  {t("cancel")}
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  {saving ? t("loading") : t("save")}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
