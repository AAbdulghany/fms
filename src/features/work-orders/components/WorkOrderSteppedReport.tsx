import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";

type Answers = Record<string, unknown>;

type CatalogPart = {
  id: string;
  sku: string;
  name: string;
  name_en?: string;
  name_ar?: string;
  qty_on_hand?: string | number;
};

export type PartsUsedLine = {
  part_id: string;
  name: string;
  sku: string;
  quantity: number;
};

const CORRECTIVE_SYMPTOMS = [
  "No power / won't start",
  "Overheating",
  "Leak",
  "Noise / vibration",
  "Not cooling / heating",
  "Alarm / trip",
  "Other",
] as const;

const CONDITIONS = ["Good", "Fair", "Poor", "Critical"] as const;

function wholeQty(value: unknown): number {
  const n = Math.round(Number(value));
  return Number.isFinite(n) && n >= 1 ? n : 1;
}

function asPartsUsed(raw: unknown): PartsUsedLine[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((r): r is Record<string, unknown> => !!r && typeof r === "object")
    .map((r) => ({
      part_id: String(r.part_id || ""),
      name: String(r.name || r.part_name || ""),
      sku: String(r.sku || r.part_sku || ""),
      quantity: wholeQty(r.quantity ?? r.qty ?? 1),
    }))
    .filter((r) => r.part_id || r.name || r.sku);
}

export interface WorkOrderSteppedReportProps {
  woSource: string;
  workOrderId?: string;
  answers: Answers;
  setAnswers: React.Dispatch<React.SetStateAction<Answers>>;
  photos: Record<string, File[]>;
  setPhotos: React.Dispatch<React.SetStateAction<Record<string, File[]>>>;
  canEdit: boolean;
  isDraft: boolean;
  jobStartedAt?: string | null;
  jobHours?: number | null;
  pdfLang: "ar" | "en";
  setPdfLang: (lang: "ar" | "en") => void;
  onSave: () => Promise<void> | void;
  onSubmit: () => Promise<void> | void;
  /** Last-step label. Technicians send for a manager; a manager approves directly. */
  submitLabel?: string;
  saving?: boolean;
  /** When true, omit Save/Submit (phone sticky bar owns them). Keep Back/Next. */
  hideSaveSubmit?: boolean;
}

function ChipGrid({
  options,
  value,
  disabled,
  onChange,
}: {
  options: readonly string[];
  value: string;
  disabled?: boolean;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const active = value === opt;
        return (
          <button
            key={opt}
            type="button"
            disabled={disabled}
            onClick={() => onChange(opt)}
            className={
              active
                ? "rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-neutral-0"
                : "rounded-md border border-neutral-300 bg-neutral-0 px-3 py-2 text-sm text-neutral-800 hover:border-primary-400"
            }
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

function PartsInventoryPicker({
  lines,
  editable,
  workOrderId,
  onChange,
}: {
  lines: PartsUsedLine[];
  editable: boolean;
  workOrderId?: string;
  onChange: (next: PartsUsedLine[]) => void;
}) {
  const { t, i18n } = useTranslation();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<CatalogPart[]>([]);
  const [searching, setSearching] = useState(false);
  const [pending, setPending] = useState<CatalogPart | null>(null);
  const [qty, setQty] = useState("1");

  useEffect(() => {
    const q = query.trim();
    if (q.length < 1) {
      setHits([]);
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setSearching(true);
      void apiFetch<CatalogPart[]>(
        `/parts-catalog?q=${encodeURIComponent(q)}`
      )
        .then((rows) => {
          if (!cancelled) setHits(rows.slice(0, 12));
        })
        .catch(() => {
          if (!cancelled) setHits([]);
        })
        .finally(() => {
          if (!cancelled) setSearching(false);
        });
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  function partLabel(p: CatalogPart): string {
    const localized =
      i18n.language?.startsWith("ar")
        ? p.name_ar || p.name || p.name_en
        : p.name_en || p.name || p.name_ar;
    return `${p.sku} — ${localized || p.sku}`;
  }

  async function addPending() {
    if (!pending || !editable) return;
    const quantity = wholeQty(qty);
    const line: PartsUsedLine = {
      part_id: pending.id,
      name: pending.name_en || pending.name || pending.name_ar || pending.sku,
      sku: pending.sku,
      quantity,
    };
    const withoutDup = lines.filter((l) => l.part_id !== line.part_id);
    onChange([...withoutDup, line]);
    if (workOrderId) {
      try {
        await apiFetch(`/work-orders/${workOrderId}/parts`, {
          method: "POST",
          body: JSON.stringify({ part_id: line.part_id, quantity: String(quantity) }),
        });
      } catch {
        /* report answers still hold the line */
      }
    }
    setPending(null);
    setQty("1");
    setQuery("");
    setHits([]);
  }

  function updateQty(partId: string, nextQty: number) {
    onChange(
      lines.map((l) =>
        l.part_id === partId ? { ...l, quantity: wholeQty(nextQty) } : l
      )
    );
  }

  function removeLine(partId: string) {
    onChange(lines.filter((l) => l.part_id !== partId));
  }

  return (
    <div className="space-y-3 rounded-md border border-neutral-200 bg-neutral-50 p-3">
      <label className="block text-sm text-neutral-700">
        {t("report_search_spare_parts") || "Search spare parts"}
        <input
          type="search"
          className="mt-1 w-full rounded-md border border-neutral-300 bg-neutral-0 px-3 py-2 text-sm"
          disabled={!editable}
          placeholder={t("report_search_spare_parts_ph") || "SKU or name…"}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPending(null);
          }}
          autoComplete="off"
        />
      </label>
      {searching && (
        <p className="text-xs text-neutral-500">{t("loading") || "Loading…"}</p>
      )}
      {!pending && hits.length > 0 && (
        <ul className="max-h-40 overflow-auto rounded-md border border-neutral-200 bg-neutral-0 text-sm">
          {hits.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                disabled={!editable}
                className="w-full px-3 py-2 text-start hover:bg-neutral-100"
                onClick={() => {
                  setPending(p);
                  setHits([]);
                  setQuery(partLabel(p));
                  setQty("1");
                }}
              >
                {partLabel(p)}
              </button>
            </li>
          ))}
        </ul>
      )}
      {pending && (
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-sm text-neutral-700">
            {t("quantity") || "Qty"}
            <input
              type="number"
              min={1}
              step={1}
              inputMode="numeric"
              className="ms-2 w-24 rounded-md border border-neutral-300 bg-neutral-0 px-2 py-1.5 text-sm"
              disabled={!editable}
              value={wholeQty(qty)}
              onChange={(e) => setQty(String(wholeQty(e.target.value)))}
            />
          </label>
          <button
            type="button"
            disabled={!editable}
            className="rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-neutral-0"
            onClick={() => void addPending()}
          >
            {t("add_part") || "Add part"}
          </button>
          <button
            type="button"
            className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700"
            onClick={() => {
              setPending(null);
              setQuery("");
            }}
          >
            {t("cancel") || "Cancel"}
          </button>
        </div>
      )}
      <ul className="divide-y divide-neutral-200 text-sm">
        {lines.length === 0 && (
          <li className="py-1 text-neutral-500">
            {t("report_parts_none_yet") || "No parts added yet"}
          </li>
        )}
        {lines.map((l) => (
          <li key={l.part_id || l.sku} dir="ltr" className="flex items-center gap-3 py-2">
            <span className="min-w-0 flex-1 text-left text-neutral-800">{l.name || l.sku}</span>
            {editable && (
              <button
                type="button"
                className="shrink-0 text-sm text-red-600"
                onClick={() => removeLine(l.part_id)}
              >
                {t("remove") || "Remove"}
              </button>
            )}
            <input
              type="number"
              min={1}
              step={1}
              inputMode="numeric"
              aria-label={t("quantity") || "Qty"}
              className="w-16 shrink-0 rounded border border-neutral-300 bg-neutral-0 px-2 py-1 text-right text-sm"
              disabled={!editable}
              value={wholeQty(l.quantity)}
              onChange={(e) => updateQty(l.part_id, wholeQty(e.target.value))}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function WorkOrderSteppedReport({
  woSource,
  workOrderId,
  answers,
  setAnswers,
  photos,
  setPhotos,
  canEdit,
  isDraft,
  jobStartedAt,
  jobHours,
  pdfLang,
  setPdfLang,
  onSave,
  onSubmit,
  submitLabel,
  saving,
  hideSaveSubmit = false,
}: WorkOrderSteppedReportProps) {
  const { t } = useTranslation();
  const isPreventive = woSource === "preventive";
  const totalSteps = isPreventive ? 2 : 3;
  const [step, setStep] = useState(1);
  const editable = canEdit && isDraft;
  const partsUsed = asPartsUsed(answers.parts_used);

  const roundResult = String(answers.round_result ?? "");
  const needsIssueStep = isPreventive && roundResult === "Done with issues";

  const condition = String(answers.overall_condition ?? "");
  const needsPhoto = condition === "Poor" || condition === "Critical";

  const clockLabel = useMemo(() => {
    if (jobHours != null && jobHours > 0) {
      return `${jobHours.toFixed(2)} h`;
    }
    if (jobStartedAt) {
      try {
        return `${t("report_clock_running") || "Clock running"} · ${new Date(jobStartedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
      } catch {
        return t("report_clock_running") || "Clock running";
      }
    }
    return t("report_clock_auto") || "Time logs when you start and submit";
  }, [jobHours, jobStartedAt, t]);

  function setField(id: string, value: unknown) {
    setAnswers((a) => {
      const next = { ...a, [id]: value };
      if (id === "round_result" && value === "Done OK") {
        next.overall_condition = next.overall_condition || "Good";
        next.issue_notes = "";
      }
      if (id === "replaced_parts" && value === "No") {
        next.parts_used = [];
        next.parts_note = "";
      }
      return next;
    });
  }

  function canAdvance(): boolean {
    if (!isPreventive) {
      if (step === 1) return Boolean(answers.symptom);
      if (step === 2) {
        if (!String(answers.fix_action ?? "").trim()) return false;
        if (!answers.replaced_parts) return false;
        if (answers.replaced_parts === "Yes" && partsUsed.length === 0) return false;
        return true;
      }
      if (step === 3) {
        if (!answers.overall_condition) return false;
        if (needsPhoto && !(photos.photo_documentation?.length)) return false;
        return true;
      }
    } else {
      if (step === 1) return Boolean(answers.round_result);
      if (step === 2) {
        if (needsIssueStep && !String(answers.issue_notes ?? "").trim()) return false;
        if (!answers.overall_condition) return false;
        if (needsPhoto && !(photos.photo_documentation?.length)) return false;
        return true;
      }
    }
    return false;
  }

  async function handleNext() {
    if (!canAdvance()) return;
    if (isPreventive && step === 1 && roundResult === "Done OK") {
      setField("overall_condition", answers.overall_condition || "Good");
      await onSave();
      await onSubmit();
      return;
    }
    if (step < totalSteps) {
      setStep((s) => s + 1);
      return;
    }
    await onSave();
    await onSubmit();
  }

  const isLastStep =
    step >= totalSteps || (isPreventive && step === 1 && roundResult === "Done OK");

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5" aria-label={`Step ${step} of ${totalSteps}`}>
          {Array.from({ length: totalSteps }, (_, i) => (
            <span
              key={i}
              className={
                i + 1 <= step
                  ? "h-2 w-6 rounded-full bg-primary-600"
                  : "h-2 w-6 rounded-full bg-neutral-200"
              }
            />
          ))}
          <span className="ms-2 text-xs text-neutral-500">
            {step}/{totalSteps}
          </span>
        </div>
        <span className="rounded-md bg-neutral-100 px-2 py-1 text-xs font-medium text-neutral-700">
          {isPreventive
            ? t("report_profile_preventive") || "Preventive"
            : t("report_profile_corrective") || "Corrective"}
        </span>
      </div>

      <p className="rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-700">
        {clockLabel}
      </p>

      {!isPreventive && step === 1 && (
        <section className="space-y-3">
          <h3 className="text-base font-semibold text-neutral-900">
            {t("report_step_symptom") || "What was wrong?"}
          </h3>
          <ChipGrid
            options={CORRECTIVE_SYMPTOMS}
            value={String(answers.symptom ?? "")}
            disabled={!editable}
            onChange={(v) => setField("symptom", v)}
          />
          <input
            type="text"
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            placeholder={t("report_field_symptom_detail") || "More detail (optional)"}
            disabled={!editable}
            value={String(answers.symptom_detail ?? "")}
            onChange={(e) => setField("symptom_detail", e.target.value)}
          />
        </section>
      )}

      {!isPreventive && step === 2 && (
        <section className="space-y-3">
          <h3 className="text-base font-semibold text-neutral-900">
            {t("report_step_fix") || "What did you do?"}
          </h3>
          <textarea
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            rows={3}
            disabled={!editable}
            placeholder={t("report_field_fix_action") || "Action taken"}
            value={String(answers.fix_action ?? "")}
            onChange={(e) => setField("fix_action", e.target.value)}
          />
          <p className="text-sm text-neutral-700">{t("report_field_replaced_parts") || "Replaced parts?"}</p>
          <ChipGrid
            options={["No", "Yes"]}
            value={String(answers.replaced_parts ?? "")}
            disabled={!editable}
            onChange={(v) => setField("replaced_parts", v)}
          />
          {answers.replaced_parts === "Yes" && (
            <PartsInventoryPicker
              lines={partsUsed}
              editable={editable}
              workOrderId={workOrderId}
              onChange={(next) => setField("parts_used", next)}
            />
          )}
        </section>
      )}

      {!isPreventive && step === 3 && (
        <section className="space-y-3">
          <h3 className="text-base font-semibold text-neutral-900">
            {t("report_step_close") || "Close out"}
          </h3>
          <p className="text-sm text-neutral-700">{t("report_field_overall_condition") || "Overall condition"}</p>
          <ChipGrid
            options={CONDITIONS}
            value={condition}
            disabled={!editable}
            onChange={(v) => setField("overall_condition", v)}
          />
          {needsPhoto && (
            <div>
              <label className="mb-1 block text-sm text-neutral-700">
                {t("report_field_photo_documentation") || "Photos"} *
              </label>
              <input
                type="file"
                accept="image/*"
                multiple
                disabled={!editable}
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  setPhotos((p) => ({ ...p, photo_documentation: files }));
                }}
                className="w-full text-sm text-neutral-600"
              />
            </div>
          )}
        </section>
      )}

      {isPreventive && step === 1 && (
        <section className="space-y-3">
          <h3 className="text-base font-semibold text-neutral-900">
            {t("report_step_round") || "Round result"}
          </h3>
          <ChipGrid
            options={["Done OK", "Done with issues"]}
            value={roundResult}
            disabled={!editable}
            onChange={(v) => setField("round_result", v)}
          />
          <p className="text-xs text-neutral-500">
            {t("report_round_ok_hint") || "Done OK submits in one tap after Next."}
          </p>
        </section>
      )}

      {isPreventive && step === 2 && (
        <section className="space-y-3">
          <h3 className="text-base font-semibold text-neutral-900">
            {t("report_step_issues") || "Issues & condition"}
          </h3>
          {needsIssueStep && (
            <textarea
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              rows={3}
              disabled={!editable}
              placeholder={t("report_field_issue_notes") || "What needs attention"}
              value={String(answers.issue_notes ?? "")}
              onChange={(e) => setField("issue_notes", e.target.value)}
            />
          )}
          <p className="text-sm text-neutral-700">{t("report_field_overall_condition") || "Overall condition"}</p>
          <ChipGrid
            options={CONDITIONS}
            value={condition}
            disabled={!editable}
            onChange={(v) => setField("overall_condition", v)}
          />
          {needsPhoto && (
            <div>
              <label className="mb-1 block text-sm text-neutral-700">
                {t("report_field_photo_documentation") || "Photos"} *
              </label>
              <input
                type="file"
                accept="image/*"
                multiple
                disabled={!editable}
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  setPhotos((p) => ({ ...p, photo_documentation: files }));
                }}
                className="w-full text-sm text-neutral-600"
              />
            </div>
          )}
        </section>
      )}

      {isDraft && (
        <div className="flex flex-wrap items-center gap-3 border-t border-neutral-100 pt-4">
          <label className="text-sm text-neutral-700">
            {t("report_pdf_language") || "PDF language"}
            <select
              className="ms-2 rounded-md border border-neutral-300 px-2 py-1.5 text-sm"
              value={pdfLang}
              onChange={(e) => setPdfLang(e.target.value as "ar" | "en")}
            >
              <option value="ar">{t("report_pdf_lang_ar") || "Arabic (AR)"}</option>
              <option value="en">{t("report_pdf_lang_en") || "English (EN)"}</option>
            </select>
          </label>
        </div>
      )}

      {isDraft && editable && (
        <div className="flex flex-wrap gap-2 pt-2">
          {step > 1 && (
            <button
              type="button"
              className="min-h-11 rounded-xl border border-neutral-300 px-4 py-2 text-sm font-semibold text-neutral-700"
              onClick={() => setStep((s) => Math.max(1, s - 1))}
            >
              {t("back") || "Back"}
            </button>
          )}
          {!hideSaveSubmit && (
            <button
              type="button"
              className="min-h-11 rounded-xl border border-neutral-300 px-4 py-2 text-sm font-semibold text-neutral-700"
              disabled={!!saving}
              onClick={() => void onSave()}
            >
              {t("save_report") || "Save"}
            </button>
          )}
          <button
            type="button"
            className="min-h-11 flex-1 rounded-xl bg-secondary-500 px-4 py-2 text-sm font-semibold text-neutral-0 hover:bg-secondary-600 disabled:opacity-50"
            disabled={!canAdvance() || !!saving}
            onClick={() => void handleNext()}
          >
            {isLastStep ? submitLabel || t("submit_report") || "Submit" : t("next") || "Next"}
          </button>
        </div>
      )}
    </div>
  );
}
