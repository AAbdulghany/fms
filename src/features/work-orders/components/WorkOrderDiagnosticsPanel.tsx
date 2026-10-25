import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiFetch, resolveApiError } from "@/lib/api";
import { SlideNotice } from "@/shared/components/SlideNotice";
import type { DiagnosticCode, WorkOrder } from "@/lib/types";

interface Props {
  workOrder: WorkOrder;
  canEdit: boolean;
  onSaved: (wo: WorkOrder) => void;
  /** Inside the phone collapse row — skip the outer card title. */
  embedded?: boolean;
}

function toLocalInputValue(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInputValue(local: string): string | null {
  if (!local.trim()) return null;
  const d = new Date(local);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export function WorkOrderDiagnosticsPanel({ workOrder, canEdit, onSaved, embedded = false }: Props) {
  const { t, i18n } = useTranslation();
  const [failureCodes, setFailureCodes] = useState<DiagnosticCode[]>([]);
  const [symptomCodes, setSymptomCodes] = useState<DiagnosticCode[]>([]);
  const [started, setStarted] = useState(toLocalInputValue(workOrder.downtime_started_at));
  const [ended, setEnded] = useState(toLocalInputValue(workOrder.downtime_ended_at));
  const [failure, setFailure] = useState(workOrder.failure_code || "");
  const [symptom, setSymptom] = useState(workOrder.symptom_code || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setStarted(toLocalInputValue(workOrder.downtime_started_at));
    setEnded(toLocalInputValue(workOrder.downtime_ended_at));
    setFailure(workOrder.failure_code || "");
    setSymptom(workOrder.symptom_code || "");
  }, [workOrder.id, workOrder.downtime_started_at, workOrder.downtime_ended_at, workOrder.failure_code, workOrder.symptom_code]);

  useEffect(() => {
    void (async () => {
      try {
        const rows = await apiFetch<DiagnosticCode[]>("/work-orders/diagnostic-codes");
        setFailureCodes(rows.filter((r) => r.kind === "failure"));
        setSymptomCodes(rows.filter((r) => r.kind === "symptom"));
      } catch {
        /* catalog optional for display */
      }
    })();
  }, []);

  const labelFor = (row: DiagnosticCode) =>
    i18n.language?.startsWith("ar") ? row.name_ar || row.name_en || row.code : row.name_en || row.name_ar || row.code;

  async function save(e: FormEvent) {
    e.preventDefault();
    if (!canEdit) return;
    setSaving(true);
    setError(null);
    try {
      const startIso = fromLocalInputValue(started);
      const endIso = fromLocalInputValue(ended);
      const updated = await apiFetch<WorkOrder>(`/work-orders/${workOrder.id}`, {
        method: "PATCH",
        json: {
          downtime_started_at: startIso,
          downtime_ended_at: endIso,
          clear_downtime: !startIso && !endIso,
          failure_code: failure || undefined,
          clear_failure_code: !failure,
          symptom_code: symptom || undefined,
          clear_symptom_code: !symptom,
        },
      });
      onSaved(updated);
    } catch (err) {
      setError(resolveApiError(err, t, i18n.language, t("error_generic")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={(e) => void save(e)}
      className={
        embedded
          ? "bg-transparent"
          : "rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm"
      }
    >
      {!embedded && (
        <>
          <h2 className="text-base font-semibold text-neutral-800">{t("error_codes")}</h2>
          <p className="mt-1 text-xs text-neutral-500">
            {t("diagnostic_codes_hint") || "Failure / symptom codes and downtime"}
          </p>
        </>
      )}

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="text-xs font-medium text-neutral-500">{t("downtime_started_at")}</span>
          <input
            type="datetime-local"
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-50"
            value={started}
            onChange={(e) => setStarted(e.target.value)}
            disabled={!canEdit}
          />
        </label>
        <label className="block text-sm">
          <span className="text-xs font-medium text-neutral-500">{t("downtime_ended_at")}</span>
          <input
            type="datetime-local"
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-50"
            value={ended}
            onChange={(e) => setEnded(e.target.value)}
            disabled={!canEdit}
          />
        </label>
        <label className="block text-sm">
          <span className="text-xs font-medium text-neutral-500">{t("failure_code")}</span>
          <select
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-50"
            value={failure}
            onChange={(e) => setFailure(e.target.value)}
            disabled={!canEdit}
          >
            <option value="">—</option>
            {failureCodes.map((c) => (
              <option key={c.code} value={c.code}>
                {c.code} — {labelFor(c)}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="text-xs font-medium text-neutral-500">{t("symptom_code")}</span>
          <select
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-50"
            value={symptom}
            onChange={(e) => setSymptom(e.target.value)}
            disabled={!canEdit}
          >
            <option value="">—</option>
            {symptomCodes.map((c) => (
              <option key={c.code} value={c.code}>
                {c.code} — {labelFor(c)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {workOrder.downtime_minutes != null && (
        <p className="mt-2 text-sm text-neutral-600">
          {t("downtime_minutes")}: <span className="font-medium text-neutral-900">{workOrder.downtime_minutes}</span>
        </p>
      )}

      <SlideNotice text={error} tone="error" />

      {canEdit && (
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? t("loading") : t("save_diagnostics")}
          </button>
          <button
            type="button"
            disabled={saving}
            className="rounded-md border border-neutral-300 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 disabled:opacity-50"
            onClick={() => {
              setStarted("");
              setEnded("");
              setFailure("");
              setSymptom("");
            }}
          >
            {t("clear_downtime")}
          </button>
        </div>
      )}
    </form>
  );
}
