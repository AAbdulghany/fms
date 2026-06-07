import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import type { WorkOrder } from "../lib/types";
import { urgencyBadgeClass, workOrderStatusPillClass } from "../lib/workOrderDisplay";

type Props = {
  workOrder: WorkOrder;
  open: boolean;
  onClose: () => void;
  onResolved: () => void;
};

export function WorkOrderRequestReviewModal({ workOrder, open, onClose, onResolved }: Props) {
  const { t } = useTranslation();
  const [title, setTitle] = useState(workOrder.title);
  const [description, setDescription] = useState(workOrder.description ?? "");
  const [urgency, setUrgency] = useState(workOrder.urgency);
  const [declineReason, setDeclineReason] = useState("");
  const [mode, setMode] = useState<"review" | "decline">("review");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setTitle(workOrder.title);
    setDescription(workOrder.description ?? "");
    setUrgency(workOrder.urgency);
    setDeclineReason("");
    setMode("review");
    setErr(null);
  }, [workOrder]);

  if (!open) return null;

  const hasEdits =
    title.trim() !== workOrder.title ||
    (description.trim() || "") !== (workOrder.description ?? "") ||
    urgency !== workOrder.urgency;

  async function saveEditsIfNeeded() {
    if (!hasEdits) return;
    await apiFetch(`/work-orders/${workOrder.id}`, {
      method: "PATCH",
      json: {
        title: title.trim(),
        description: description.trim() || null,
        urgency,
      },
    });
  }

  async function onApprove(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      if (hasEdits) await saveEditsIfNeeded();
      await apiFetch(`/work-orders/${workOrder.id}/approve-request`, { method: "POST" });
      onResolved();
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  async function onDecline(e: FormEvent) {
    e.preventDefault();
    const reason = declineReason.trim();
    if (!reason) {
      setErr(t("decline_reason_required"));
      return;
    }
    setLoading(true);
    setErr(null);
    try {
      await apiFetch(`/work-orders/${workOrder.id}/decline-request`, {
        method: "POST",
        json: { reason },
      });
      onResolved();
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl bg-neutral-0 p-6 shadow-xl" role="dialog" aria-modal>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-neutral-900">{t("review_work_order_request")}</h2>
            <p className="mt-1 text-sm text-neutral-600">
              {workOrder.company_name} · {workOrder.site_name}
            </p>
          </div>
          <span className={workOrderStatusPillClass(workOrder.status)}>{t("requested")}</span>
        </div>

        {workOrder.creator && (
          <p className="mb-4 text-sm text-neutral-600">
            {t("created_by")}: {workOrder.creator.full_name || workOrder.creator.email}
          </p>
        )}

        {err && <p className="mb-3 text-sm text-error-main">{err}</p>}

        {mode === "review" ? (
          <form onSubmit={onApprove} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("title")}</label>
              <input
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("description")}</label>
              <textarea
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">{t("urgency")}</label>
              <select
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                value={urgency}
                onChange={(e) => setUrgency(e.target.value)}
              >
                <option value="normal">{t("normal")}</option>
                <option value="urgent">{t("urgent")}</option>
                <option value="emergency">{t("emergency")}</option>
              </select>
              <span className={`mt-2 inline-flex ${urgencyBadgeClass(urgency)}`}>{t(urgency)}</span>
            </div>
            <p className="text-xs text-neutral-500">{t("approve_request_hint")}</p>
            <div className="flex flex-wrap justify-end gap-2 pt-2">
              <button
                type="button"
                className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100"
                onClick={onClose}
              >
                {t("cancel")}
              </button>
              <button
                type="button"
                className="rounded-md bg-neutral-200 px-4 py-2 text-sm font-medium text-neutral-800 hover:bg-neutral-300"
                onClick={() => {
                  setMode("decline");
                  setErr(null);
                }}
              >
                {t("decline_request")}
              </button>
              <button
                type="submit"
                disabled={loading}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {loading ? t("loading") : t("approve_request")}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={onDecline} className="space-y-4">
            <p className="text-sm text-neutral-700">{title}</p>
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                {t("decline_reason")} *
              </label>
              <textarea
                required
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                rows={4}
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                placeholder={t("decline_reason_placeholder")}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100"
                onClick={() => {
                  setMode("review");
                  setErr(null);
                }}
              >
                {t("back")}
              </button>
              <button
                type="submit"
                disabled={loading || !declineReason.trim()}
                className="rounded-md bg-error-main px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              >
                {loading ? t("loading") : t("confirm_decline")}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
