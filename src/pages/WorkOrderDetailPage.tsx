import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch } from "../lib/api";
import type { MaintenanceReport, ReportTemplate, WorkOrder, WorkOrderStatus } from "../lib/types";

interface UserMe {
  role: string;
}

interface TemplateField {
  id: string;
  type: string;
  label_key?: string;
  options?: string[];
  required?: boolean;
  max_photos?: number;
}

export function WorkOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const [wo, setWo] = useState<WorkOrder | null>(null);
  const [report, setReport] = useState<MaintenanceReport | null>(null);
  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [parts, setParts] = useState<Array<{ sku: string; quantity: number }>>([]);
  const [photos, setPhotos] = useState<Record<string, File[]>>({});
  const [me, setMe] = useState<UserMe | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [nextStatus, setNextStatus] = useState<WorkOrderStatus | "">("");
  const [invoiceCurrency, setInvoiceCurrency] = useState("SAR");

  const load = async () => {
    if (!id) return;
    setErr(null);
    try {
      const [w, user] = await Promise.all([
        apiFetch<WorkOrder>(`/work-orders/${id}`),
        apiFetch<UserMe>("/users/me"),
      ]);
      setWo(w);
      setMe(user);
      if (w.template_id) {
        const tmpl = await apiFetch<ReportTemplate>(`/report-templates/${w.template_id}`);
        setTemplate(tmpl);
      }
      try {
        const r = await apiFetch<MaintenanceReport>(`/work-orders/${id}/report`);
        setReport(r);
        const aj = (r.answers_json as Record<string, unknown>) || {};
        setAnswers(aj);
        const partsData = aj.parts_used ?? [{ sku: "FLT-001", quantity: 2 }];
        setParts(Array.isArray(partsData) ? partsData : []);
      } catch {
        setReport(null);
        setAnswers({});
        setParts([{ sku: "FLT-001", quantity: 2 }]);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  async function saveReport(e?: FormEvent) {
    e?.preventDefault();
    if (!id) return;
    setMsg(null);
    setErr(null);
    let payload = { ...answers };
    payload = { ...payload, parts_used: parts };

    // Upload photos and get file identifiers
    const photoRefs: Record<string, string[]> = {};
    try {
      for (const [fieldId, files] of Object.entries(photos)) {
        const uploadedIds = await Promise.all(
          files.map((f) => uploadFile(f))
        );
        photoRefs[fieldId] = uploadedIds;
      }
    } catch (e) {
      setErr("Photo upload failed");
      return;
    }

    if (Object.keys(photoRefs).length > 0) {
      payload = { ...payload, photos: photoRefs };
    }
    try {
      const r = await apiFetch<MaintenanceReport>(`/work-orders/${id}/report`, {
        method: "PUT",
        json: { answers: payload },
      });
      setReport(r);
      setMsg("Saved");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function submitReport() {
    if (!id) return;
    setMsg(null);
    setErr(null);
    try {
      await saveReport();
      const r = await apiFetch<MaintenanceReport>(`/work-orders/${id}/report/submit`, {
        method: "POST",
      });
      setReport(r);
      setMsg("Submitted");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function uploadFile(file: File) {
    try {
      // 1. Get presigned URL from backend
      const { url, fileId } = await apiFetch<{ url: string; fileId: string }>(
        `/uploads/presign`,
        {
          method: "POST",
          json: { filename: file.name, content_type: file.type },
        }
      );

      // 2. Upload binary to S3/MinIO
      const uploadRes = await fetch(url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });

      if (!uploadRes.ok) throw new Error("S3 upload failed");

      // 3. Complete the upload to let backend know it's finished
      await apiFetch(`/uploads/complete`, {
        method: "POST",
        json: { fileId },
      });

      return fileId;
    } catch (e) {
      console.error("Upload failed", e);
      throw e;
    }
  }

  async function patchStatus() {
    if (!id || !nextStatus || !wo) return;
    setMsg(null);
    setErr(null);
    try {
      const w = await apiFetch<WorkOrder>(`/work-orders/${id}`, {
        method: "PATCH",
        json: { status: nextStatus },
      });
      setWo(w);
      setMsg("Status updated");
      setNextStatus("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function generateInvoice() {
    if (!id) return;
    setMsg(null);
    setErr(null);
    try {
      await apiFetch(`/work-orders/${id}/generate-invoice`, {
        method: "POST",
        json: { currency: invoiceCurrency },
      });
      setMsg("Invoice created");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function approveReport() {
    if (!id || !report) return;
    setMsg(null);
    setErr(null);
    try {
      await apiFetch(`/reports/${report.id}/approve`, { method: "POST" });
      setMsg("Report approved");
      await load(); // Reload to get updated status
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  if (!wo) {
    return err ? <p className="text-error-main">{err}</p> : <p className="text-neutral-500">…</p>;
  }

  const canEditReport =
    me?.role === "technician" ||
    me?.role === "company_admin" ||
    me?.role === "super_admin" ||
    me?.role === "site_manager";
  const canApprove =
    me?.role === "company_admin" ||
    me?.role === "client_admin" ||
    me?.role === "manager" ||
    me?.role === "super_admin";
  const canAdminWO =
    me?.role === "company_admin" || me?.role === "super_admin" || me?.role === "site_manager";

  const sections = (template?.schema_json?.sections as Array<{ fields?: TemplateField[] }>) || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">{wo.title || "Work order"}</h1>
        <p className="text-sm text-neutral-500">
          {t("status")}: <strong>{wo.status}</strong> · {wo.id}
        </p>
      </div>

      <div className="grid gap-4 rounded-lg border border-neutral-200 bg-neutral-0 p-4 md:grid-cols-2">
        <div>
          <div className="text-xs font-medium text-neutral-500">{t("created_by")}</div>
          {wo.creator ? (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-800">
                {(wo.creator.full_name || wo.creator.email || "?").slice(0, 1).toUpperCase()}
              </div>
              <div>
                <div className="text-sm font-medium text-neutral-900">
                  {wo.creator.full_name || wo.creator.email}
                </div>
                <div className="text-xs text-neutral-500">{wo.creator.role}</div>
              </div>
            </div>
          ) : (
            <p className="mt-1 text-sm text-neutral-400">—</p>
          )}
          <p className="mt-2 text-xs text-neutral-500">
            {t("created_at")}: {new Date(wo.opened_at).toLocaleString()}
          </p>
        </div>
        <div>
          <div className="text-xs font-medium text-neutral-500">{t("assigned_to")}</div>
          {wo.assignee ? (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-success-light text-sm font-semibold text-success-dark">
                {(wo.assignee.full_name || wo.assignee.email || "?").slice(0, 1).toUpperCase()}
              </div>
              <div>
                <div className="text-sm font-medium text-neutral-900">
                  {wo.assignee.full_name || wo.assignee.email}
                </div>
                <div className="text-xs text-neutral-500">{wo.assignee.role}</div>
              </div>
            </div>
          ) : (
            <p className="mt-1 text-sm text-neutral-400">{t("not_assigned")}</p>
          )}
        </div>
      </div>

      {msg && <p className="rounded-md bg-success-light px-3 py-2 text-success-dark">{msg}</p>}
      {err && <p className="rounded-md bg-error-light px-3 py-2 text-error-dark">{err}</p>}

      {canAdminWO && (
        <div className="flex flex-wrap items-end gap-2 rounded-lg border border-neutral-200 bg-neutral-0 p-4">
          <div>
            <label className="mb-1 block text-xs text-neutral-500">Transition status</label>
            <select
              className="rounded-md border border-neutral-300 px-2 py-2 text-sm"
              value={nextStatus}
              onChange={(e) => setNextStatus(e.target.value as WorkOrderStatus)}
            >
              <option value="">—</option>
              {(
                [
                  "created",
                  "assigned",
                  "in_progress",
                  "on_hold",
                  "completed",
                  "verified",
                  "closed",
                  "cancelled",
                ] as WorkOrderStatus[]
              ).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="rounded-md bg-neutral-800 px-3 py-2 text-sm text-neutral-0"
            onClick={() => void patchStatus()}
          >
            Apply
          </button>
          {wo.status === "verified" && (
            <>
              <div>
                <label className="mb-1 block text-xs text-neutral-500">{t("invoice_currency")}</label>
                <select
                  className="rounded-md border border-neutral-300 px-2 py-2 text-sm"
                  value={invoiceCurrency}
                  onChange={(e) => setInvoiceCurrency(e.target.value)}
                >
                  <option value="SAR">SAR</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="EGP">EGP</option>
                </select>
              </div>
              <button
                type="button"
                className="rounded-md bg-primary-600 px-3 py-2 text-sm text-neutral-0"
                onClick={() => void generateInvoice()}
              >
                {t("generate_invoice")}
              </button>
            </>
          )}
        </div>
      )}

      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-medium text-neutral-800">Report</h2>
        {!template && <p className="text-neutral-500">{t("no_report")}</p>}
        {template && (
          <form className="space-y-4" onSubmit={(e) => void saveReport(e)}>
            {sections.map((sec, si) => (
              <div key={si} className="space-y-3">
                {(sec.fields || []).map((field) => {
                  if (field.type === "checklist" && field.options) {
                    return (
                      <div key={field.id}>
                        <label className="mb-1 block text-sm text-neutral-700">
                          {field.label_key || field.id}
                          {field.required ? " *" : ""}
                        </label>
                        <select
                          className="w-full max-w-md rounded-md border border-neutral-300 px-3 py-2"
                          value={String(answers[field.id] ?? "")}
                          disabled={!canEditReport || report?.status !== "draft"}
                          onChange={(e) =>
                            setAnswers((a) => ({ ...a, [field.id]: e.target.value }))
                          }
                        >
                          <option value="">—</option>
                          {field.options.map((o) => (
                            <option key={o} value={o}>
                              {o}
                            </option>
                          ))}
                        </select>
                      </div>
                    );
                  }
                  if (field.type === "labor_log") {
                    const hours = Array.isArray(answers.labor_log)
                      ? Number((answers.labor_log as { hours?: number }[])[0]?.hours ?? 0)
                      : Number(answers.labor_hours ?? 0);
                    return (
                      <div key={field.id}>
                        <label className="mb-1 block text-sm text-neutral-700">Labor hours</label>
                        <input
                          type="number"
                          step="0.25"
                          className="w-full max-w-xs rounded-md border border-neutral-300 px-3 py-2"
                          disabled={!canEditReport || report?.status !== "draft"}
                          value={hours || ""}
                          onChange={(e) => {
                            const h = parseFloat(e.target.value) || 0;
                            setAnswers((a) => ({ ...a, labor_log: [{ hours: h }] }));
                          }}
                        />
                      </div>
                    );
                  }
                  if (field.type === "parts_used") {
                    return (
                      <div key={field.id} className="space-y-3">
                        <label className="mb-1 block text-sm text-neutral-700">
                          {t("parts_used") || "Parts Used"}
                        </label>
                        <div className="space-y-2">
                          {parts.map((part, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                              <input
                                type="text"
                                className="flex-1 rounded-md border border-neutral-300 px-3 py-1 text-sm"
                                value={part.sku}
                                disabled={!canEditReport || report?.status !== "draft"}
                                onChange={(e) => {
                                  const newParts = [...parts];
                                  newParts[idx].sku = e.target.value;
                                  setParts(newParts);
                                }}
                                placeholder="SKU"
                              />
                              <input
                                type="number"
                                className="w-20 rounded-md border border-neutral-300 px-3 py-1 text-sm"
                                value={part.quantity}
                                disabled={!canEditReport || report?.status !== "draft"}
                                onChange={(e) => {
                                  const newParts = [...parts];
                                  newParts[idx].quantity = parseInt(e.target.value, 10) || 0;
                                  setParts(newParts);
                                }}
                              />
                              <button
                                type="button"
                                className="text-error-main hover:text-error-dark"
                                disabled={!canEditReport || report?.status !== "draft"}
                                onClick={() => setParts(parts.filter((_, i) => i !== idx))}
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                          {canEditReport && report?.status === "draft" && (
                            <button
                              type="button"
                              className="text-xs text-primary-600 hover:underline"
                              onClick={() => setParts([...parts, { sku: "", quantity: 1 }])}
                            >
                              + {t("add_part") || "Add Part"}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  }
                  if (field.type === "photo" && field.max_photos) {
                    return (
                      <div key={field.id}>
                        <label className="mb-1 block text-sm text-neutral-700">
                          {field.label_key || field.id}
                          {field.required ? " *" : ""}
                        </label>
                        <input
                          type="file"
                          accept="image/*"
                          multiple
                          disabled={!canEditReport || report?.status !== "draft"}
                          onChange={(e) => {
                            const files = Array.from(e.target.files || []);
                            setPhotos((p) => ({ ...p, [field.id]: files }));
                          }}
                          className="w-full text-sm text-neutral-600"
                        />
                        {photos[field.id] && (
                          <p className="mt-1 text-xs text-neutral-500">
                            {photos[field.id].length} file(s) selected (max: {field.max_photos})
                          </p>
                        )}
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            ))}
            {canEditReport && report?.status === "draft" && (
              <div className="flex flex-wrap gap-2 pt-4">
                <button
                  type="submit"
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm text-neutral-0"
                >
                  {t("save_report")}
                </button>
                <button
                  type="button"
                  className="rounded-md border border-primary-600 px-4 py-2 text-sm text-primary-700"
                  onClick={() => void submitReport()}
                >
                  {t("submit_report")}
                </button>
              </div>
            )}
          </form>
        )}
        {report && (
          <p className="mt-4 text-sm text-neutral-600">
            Report status: <strong>{report.status}</strong>
          </p>
        )}
        {canApprove && report?.status === "submitted" && (
          <button
            type="button"
            className="mt-4 rounded-md bg-success-dark px-4 py-2 text-sm text-neutral-0"
            onClick={() => void approveReport()}
          >
            {t("approve")}
          </button>
        )}
      </div>
    </div>
  );
}
