import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch, apiFetchBlob } from "../lib/api";
import type { AuditLog, Comment, MaintenanceReport, ReportTemplate, WorkOrder, WorkOrderDocument, WorkOrderStatus, WorkOrderUserBrief } from "../lib/types";
import { workOrderStatusPillClass } from "../lib/workOrderDisplay";

interface UserMe {
  id: string;
  role: string;
}

interface TemplateField {
  id: string;
  type: string;
  label?: string;
  label_key?: string;
  placeholder?: string;
  options?: string[];
  required?: boolean;
  max_photos?: number;
  rows?: number;
}

interface TemplateSection {
  id?: string;
  title?: string;
  title_key?: string;
  fields?: TemplateField[];
}

/** Must match backend `REPORT_PDF_DOC_DESCRIPTION` in work_orders.py */
const REPORT_PDF_DOC = "report_pdf_export";

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
  const [history, setHistory] = useState<AuditLog[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [assignableUsers, setAssignableUsers] = useState<WorkOrderUserBrief[]>([]);
  const [selectedAssignee, setSelectedAssignee] = useState<string>("");
  const [documents, setDocuments] = useState<WorkOrderDocument[]>([]);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [assigneeSearch, setAssigneeSearch] = useState("");
  const [reportModalOpen, setReportModalOpen] = useState(false);

  const load = async () => {
    if (!id) return;
    setErr(null);
    try {
      const [w, user, hist, comm, assignable, docs] = await Promise.all([
        apiFetch<WorkOrder>(`/work-orders/${id}`),
        apiFetch<UserMe>("/users/me"),
        apiFetch<AuditLog[]>(`/work-orders/${id}/history`),
        apiFetch<Comment[]>(`/work-orders/${id}/comments`),
        apiFetch<WorkOrderUserBrief[]>(`/work-orders/${id}/assignable-users`),
        apiFetch<WorkOrderDocument[]>(`/work-orders/${id}/documents`),
      ]);
      setWo(w);
      setMe(user);
      setHistory(hist);
      setComments(comm);
      setAssignableUsers(assignable);
      setDocuments(docs);
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

  useEffect(() => {
    setNextStatus("");
  }, [id, wo?.status, wo?.assignee_user_id]);

  const filteredAssignable = useMemo(() => {
    const q = assigneeSearch.trim().toLowerCase();
    if (!q) return assignableUsers.slice(0, 12);
    return assignableUsers.filter(
      (u) =>
        (u.full_name || "").toLowerCase().includes(q) ||
        (u.email || "").toLowerCase().includes(q)
    ).slice(0, 20);
  }, [assignableUsers, assigneeSearch]);

  const reportPdfDocuments = useMemo(
    () => documents.filter((d) => d.description === REPORT_PDF_DOC),
    [documents]
  );

  async function saveReport(e?: FormEvent) {
    e?.preventDefault();
    if (!id) return;
    const hadReportBefore = !!report;
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
      await load();
      if (hadReportBefore) {
        setReportModalOpen(false);
      }
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
      await load();
      setReportModalOpen(false);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function downloadWorkOrderDocument(doc: WorkOrderDocument) {
    if (!id) return;
    setErr(null);
    try {
      if (doc.description === REPORT_PDF_DOC) {
        const blob = await apiFetchBlob(`/work-orders/${id}/documents/${doc.id}/file`);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = doc.file_name || "report.pdf";
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
      window.open(`/api/v1/uploads/${doc.file_url}`, "_blank", "noopener,noreferrer");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Download failed");
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
      await apiFetch<WorkOrder>(`/work-orders/${id}`, {
        method: "PATCH",
        json: { status: nextStatus },
      });
      window.location.reload();
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
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function submitComment(e: FormEvent) {
    e.preventDefault();
    if (!id || !newComment.trim()) return;
    setErr(null);
    try {
      await apiFetch(`/work-orders/${id}/comments`, {
        method: "POST",
        json: { content: newComment.trim() },
      });
      setNewComment("");
      const comm = await apiFetch<Comment[]>(`/work-orders/${id}/comments`);
      setComments(comm);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function assignUser() {
    if (!id || !selectedAssignee) return;
    setMsg(null);
    setErr(null);
    try {
      await apiFetch(`/work-orders/${id}/assign`, {
        method: "POST",
        json: { assignee_user_id: selectedAssignee },
      });
      setSelectedAssignee("");
      setAssigneeSearch("");
      window.location.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    }
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    if (!id) return;
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingFile(true);
    setErr(null);

    try {
      // 1. Get presigned URL
      const { url, fileId } = await apiFetch<{ url: string; fileId: string }>(
        `/uploads/presign`,
        {
          method: "POST",
          json: { filename: file.name, content_type: file.type },
        }
      );

      // 2. Upload to storage
      const uploadRes = await fetch(url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });

      if (!uploadRes.ok) throw new Error("Upload failed");

      // 3. Complete upload
      await apiFetch(`/uploads/complete`, {
        method: "POST",
        json: { fileId },
      });

      // 4. Register document with work order
      await apiFetch(`/work-orders/${id}/documents`, {
        method: "POST",
        json: {
          file_name: file.name,
          file_size: file.size,
          file_type: file.type,
          file_url: fileId,
        },
      });

      // 5. Refresh documents list
      const docs = await apiFetch<WorkOrderDocument[]>(`/work-orders/${id}/documents`);
      setDocuments(docs);
      setMsg("Document uploaded successfully");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploadingFile(false);
      // Reset file input
      event.target.value = "";
    }
  }


  if (!wo) {
    return err ? <p className="text-error-main">{err}</p> : <p className="text-neutral-500">…</p>;
  }

  const canEditReport = true; // All users can fill reports
  const canApprove =
    me?.role === "company_admin" ||
    me?.role === "client_admin" ||
    me?.role === "manager" ||
    me?.role === "super_admin";
  const canAdminWO =
    me?.role === "company_admin" || 
    me?.role === "super_admin" || 
    me?.role === "site_manager" ||
    me?.role === "technician"; // Technicians can change status too

  const schemaForForm =
    report?.template_snapshot_json &&
    typeof report.template_snapshot_json === "object" &&
    Array.isArray((report.template_snapshot_json as { sections?: unknown }).sections)
      ? (report.template_snapshot_json as { sections: TemplateSection[] })
      : template?.schema_json;
  const sections = (schemaForForm?.sections as TemplateSection[]) || [];

  const fieldLabel = (field: TemplateField) =>
    field.label ?? (field.label_key ? t(field.label_key) : field.id);

  const reportPhaseUnlocked = wo.status === "completed";

  const statusSelectValue = (nextStatus || wo.status) as WorkOrderStatus;

  const reportPrimaryActionLabel = !report
    ? t("fill_report") || "Fill report"
    : reportPdfDocuments.length > 0
      ? t("edit_report") || "Edit report"
      : t("continue_report") || "Continue report";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900">{wo.title || "Work order"}</h1>
        <p className="flex flex-wrap items-center gap-2 text-sm text-neutral-500">
          <span>{t("status")}:</span>
          <span className={workOrderStatusPillClass(wo.status)}>{wo.status}</span>
          <span className="font-mono text-xs text-neutral-400">· {wo.id}</span>
        </p>
      </div>

      <div className="grid gap-6 rounded-lg border border-neutral-200 bg-neutral-0 p-4 md:grid-cols-2">
        <div className="min-w-0 space-y-4">
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

          <div className="border-t border-neutral-100 pt-4">
            {canAdminWO ? (
              <>
                <label className="mb-1 block text-xs font-medium text-neutral-600" htmlFor="wo-status-transition">
                  {t("transition_status") || "Transition status"}
                </label>
                <div className="flex max-w-sm flex-wrap items-center gap-2">
                  <select
                    id="wo-status-transition"
                    className="w-36 shrink-0 rounded-md border border-neutral-300 bg-neutral-0 px-2 py-1.5 text-xs shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 sm:w-40"
                    value={statusSelectValue}
                    onChange={(e) =>
                      setNextStatus(
                        e.target.value === wo.status ? "" : (e.target.value as WorkOrderStatus)
                      )
                    }
                  >
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
                  <button
                    type="button"
                    className="shrink-0 rounded-md bg-neutral-800 px-3 py-1.5 text-xs font-medium text-neutral-0 shadow-sm transition hover:bg-neutral-900 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={!nextStatus || nextStatus === wo.status}
                    onClick={() => void patchStatus()}
                  >
                    {t("apply") || "Apply"}
                  </button>
                </div>
                <p className="mt-1 max-w-sm text-[11px] leading-snug text-neutral-500">
                  {t("status_dropdown_hint") ||
                    "Shows the current work order status. Pick a new status, then Apply."}
                </p>
                {wo.status === "verified" && (
                  <div className="mt-3 flex max-w-sm flex-wrap items-end gap-2 border-t border-neutral-100 pt-3">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-neutral-600">
                        {t("invoice_currency")}
                      </label>
                      <select
                        className="w-28 rounded-md border border-neutral-300 px-2 py-1.5 text-xs shadow-sm"
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
                      className="rounded-md bg-primary-600 px-3 py-1.5 text-xs font-medium text-neutral-0 shadow-sm hover:bg-primary-700"
                      onClick={() => void generateInvoice()}
                    >
                      {t("generate_invoice")}
                    </button>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="text-xs font-medium text-neutral-500">{t("transition_status")}</div>
                <p className="mt-1.5">
                  <span className={workOrderStatusPillClass(wo.status)}>{wo.status}</span>
                </p>
                <p className="mt-1 max-w-sm text-[11px] text-neutral-500">
                  {t("status_readonly_hint") || "Status changes are limited to authorized roles."}
                </p>
              </>
            )}
          </div>
        </div>

        <div className="min-w-0 border-neutral-100 md:border-l md:pl-6">
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
          {canAdminWO && (
            <div className="relative mt-4">
              <label className="mb-1.5 block text-xs font-medium text-neutral-600" htmlFor="wo-assignee-search">
                {t("assign_or_reassign") || "Assign or reassign"}
              </label>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  id="wo-assignee-search"
                  type="search"
                  className="min-w-0 flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder={t("search_assignee") || "Search users…"}
                  value={assigneeSearch}
                  onChange={(e) => {
                    setAssigneeSearch(e.target.value);
                    setSelectedAssignee("");
                  }}
                  autoComplete="off"
                />
                <button
                  type="button"
                  className="shrink-0 rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-neutral-0 shadow-sm transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:bg-neutral-300"
                  onClick={() => void assignUser()}
                  disabled={!selectedAssignee}
                >
                  {t("assign")}
                </button>
              </div>
              {assigneeSearch.trim().length > 0 && filteredAssignable.length > 0 && (
                <ul
                  className="absolute z-20 mt-1 max-h-40 w-full min-w-[12rem] overflow-auto rounded-md border border-neutral-200 bg-neutral-0 text-sm shadow-lg"
                  role="listbox"
                >
                  {filteredAssignable.map((u) => (
                    <li key={u.id}>
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-left hover:bg-neutral-100"
                        onClick={() => {
                          setSelectedAssignee(u.id);
                          setAssigneeSearch(`${u.full_name || u.email} (${u.role})`);
                        }}
                      >
                        <span className="font-medium text-neutral-900">{u.full_name || u.email}</span>
                        <span className="ml-1 text-xs text-neutral-500">{u.role}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {assigneeSearch.trim().length > 0 && filteredAssignable.length === 0 && (
                <p className="mt-1.5 text-xs text-neutral-500">{t("no_assignee_matches") || "No matching users"}</p>
              )}
              {selectedAssignee && (
                <p className="mt-1.5 text-xs text-neutral-600">
                  {t("assignee_selected") || "Selected"}:{" "}
                  <strong>
                    {assignableUsers.find((u) => u.id === selectedAssignee)?.full_name ||
                      assignableUsers.find((u) => u.id === selectedAssignee)?.email}
                  </strong>
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {msg && <p className="rounded-md bg-success-light px-3 py-2 text-success-dark">{msg}</p>}
      {err && <p className="rounded-md bg-error-light px-3 py-2 text-error-dark">{err}</p>}

      {!reportPhaseUnlocked && template && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          <h2 className="text-base font-semibold text-neutral-800">{t("report") || "Report"}</h2>
          <p className="mt-2 text-sm text-neutral-600">
            {t("report_locked_until_completed") ||
              "The maintenance report is available when this work order status is completed."}
          </p>
        </div>
      )}

      {reportPhaseUnlocked && !template && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          <h2 className="text-base font-semibold text-neutral-800">{t("report") || "Report"}</h2>
          <p className="mt-2 text-sm text-neutral-500">{t("no_report")}</p>
        </div>
      )}

      {reportPhaseUnlocked && template && (
        <>
          <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
            <h2 className="text-base font-semibold text-neutral-800">{t("report") || "Report"}</h2>
            <p className="mt-1 text-sm text-neutral-600">
              {t("report_card_hint") ||
                "Open the window to start or edit the report. Each save refreshes the PDF in your documents list."}
            </p>
            {reportPdfDocuments.length > 0 && (
              <div className="mt-3 rounded-md bg-neutral-50 p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-600">
                  {t("saved_report_pdfs") || "Saved report PDFs"}
                </p>
                <ul className="mt-2 space-y-1">
                  {reportPdfDocuments.map((d) => (
                    <li key={d.id}>
                      <button
                        type="button"
                        className="text-sm font-medium text-primary-700 hover:underline"
                        onClick={() => void downloadWorkOrderDocument(d)}
                      >
                        {d.file_name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                className="rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-neutral-0"
                onClick={() => setReportModalOpen(true)}
              >
                {reportPrimaryActionLabel}
              </button>
              {canApprove && report?.status === "submitted" && (
                <button
                  type="button"
                  className="rounded-md bg-success-dark px-3 py-1.5 text-sm text-neutral-0"
                  onClick={() => void approveReport()}
                >
                  {t("approve")}
                </button>
              )}
            </div>
          </div>

          {reportModalOpen && (
            <div
              className="fixed inset-0 z-40 bg-black/40"
              onMouseDown={() => setReportModalOpen(false)}
            />
          )}

          <div
            className={
              reportModalOpen
                ? "fixed left-1/2 top-14 z-50 max-h-[85vh] w-full max-w-2xl -translate-x-1/2 overflow-y-auto rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-xl"
                : "hidden"
            }
          >
            <div className="mb-4 flex items-center justify-between border-b border-neutral-100 pb-3">
              <h2 className="text-lg font-medium text-neutral-800">{t("report") || "Maintenance report"}</h2>
              <button
                type="button"
                className="rounded-md px-2 py-1 text-sm text-neutral-600 hover:bg-neutral-100"
                onClick={() => setReportModalOpen(false)}
              >
                {t("close") || "Close"}
              </button>
            </div>

            {!report && (
              <div className="py-4 text-center">
                <p className="mb-3 text-sm text-neutral-600">
                  {t("start_report_hint") || "No report started yet. Start to capture inspection details."}
                </p>
                <button
                  type="button"
                  onClick={() => void saveReport()}
                  className="rounded-md bg-primary-600 px-5 py-2 text-sm font-medium text-neutral-0 hover:bg-primary-700"
                >
                  {t("start_report") || "Start report"}
                </button>
              </div>
            )}

            {report && (
              <form className="space-y-4" onSubmit={(e) => void saveReport(e)}>
            {sections.map((sec, si) => (
              <div key={sec.id ?? si} className="space-y-3">
                {(sec.title || sec.title_key) && (
                  <h3 className="border-b border-neutral-200 pb-2 text-base font-semibold text-neutral-900">
                    {sec.title ?? (sec.title_key ? t(sec.title_key) : "")}
                  </h3>
                )}
                {(sec.fields || []).map((field) => {
                  if (field.type === "text") {
                    return (
                      <div key={field.id}>
                        <label className="mb-1 block text-sm text-neutral-700">
                          {fieldLabel(field)}
                          {field.required ? " *" : ""}
                        </label>
                        <input
                          type="text"
                          className="w-full max-w-xl rounded-md border border-neutral-300 px-3 py-2"
                          value={String(answers[field.id] ?? "")}
                          placeholder={field.placeholder}
                          disabled={!canEditReport || report?.status !== "draft"}
                          onChange={(e) =>
                            setAnswers((a) => ({ ...a, [field.id]: e.target.value }))
                          }
                        />
                      </div>
                    );
                  }
                  if (field.type === "textarea") {
                    return (
                      <div key={field.id}>
                        <label className="mb-1 block text-sm text-neutral-700">
                          {fieldLabel(field)}
                          {field.required ? " *" : ""}
                        </label>
                        <textarea
                          className="w-full max-w-3xl rounded-md border border-neutral-300 px-3 py-2"
                          rows={field.rows ?? 4}
                          value={String(answers[field.id] ?? "")}
                          placeholder={field.placeholder}
                          disabled={!canEditReport || report?.status !== "draft"}
                          onChange={(e) =>
                            setAnswers((a) => ({ ...a, [field.id]: e.target.value }))
                          }
                        />
                      </div>
                    );
                  }
                  if (field.type === "checklist" && field.options) {
                    return (
                      <div key={field.id}>
                        <label className="mb-1 block text-sm text-neutral-700">
                          {fieldLabel(field)}
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
                          {fieldLabel(field)}
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
            {report?.status === "draft" && (
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
            
            {report && report.status !== "draft" && (
              <div className="mt-4 rounded-md bg-neutral-100 p-3">
                <p className="text-sm text-neutral-600">
                  Report status: <strong className="text-neutral-900">{report.status}</strong>
                  {report.status === "submitted" && " - Waiting for approval"}
                  {report.status === "approved" && " - Report has been approved"}
                </p>
              </div>
            )}
          </form>
            )}
          </div>
        </>
      )}

      <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-medium text-neutral-800">{t("comments") || "Comments & Documents"}</h2>
        
        <div className="mb-4 space-y-3">
          {comments.length === 0 && documents.length === 0 ? (
            <p className="text-sm text-neutral-500">No comments or documents yet</p>
          ) : (
            <>
              {comments.map((comment) => (
                <div key={comment.id} className="flex gap-3 border-b border-neutral-100 pb-3">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-success-light text-sm font-semibold text-success-dark">
                    {comment.user_name ? comment.user_name.slice(0, 1).toUpperCase() : "?"}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-neutral-900">
                        {comment.user_name || "Unknown"}
                      </span>
                      <span className="text-xs text-neutral-500">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-neutral-700 whitespace-pre-wrap">{comment.content}</p>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        <form onSubmit={(e) => void submitComment(e)} className="space-y-3">
          <textarea
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
            rows={3}
            placeholder={t("add_comment") || "Add a comment..."}
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="submit"
              disabled={!newComment.trim()}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm text-neutral-0 disabled:bg-neutral-300 disabled:cursor-not-allowed"
            >
              {t("post_comment") || "Post Comment"}
            </button>
            <label
              className="inline-flex cursor-pointer items-center justify-center rounded-md border-2 border-neutral-300 px-3 py-2 text-sm transition-colors hover:border-primary-600 hover:bg-primary-50"
              title={t("attach_document") || "Attach document"}
            >
              <span className="text-xl leading-none" aria-hidden>
                🔗
              </span>
              <input
                type="file"
                className="hidden"
                aria-label={t("attach_document") || "Attach document"}
                onChange={(e) => void handleFileUpload(e)}
                disabled={uploadingFile}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt"
              />
            </label>
          </div>
        </form>
      </div>

      {(history.length > 0 || comments.length > 0 || documents.length > 0) && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-medium text-neutral-800">{t("history") || "Activity History"}</h2>
          <div className="space-y-3">
            {[...history, ...comments.map(c => ({
              id: c.id,
              actor_name: c.user_name,
              created_at: c.created_at,
              action: 'comment',
              content: c.content
            })), ...documents.map((d) => ({
              id: d.id,
              actor_name: d.uploaded_by_name,
              created_at: d.created_at,
              action: "document" as const,
              file_name: d.file_name,
              file_url: d.file_url,
              description: d.description,
            }))]
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .map((item: any) => (
              <div key={item.id} className="flex gap-3 border-b border-neutral-100 pb-3 last:border-0">
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-800">
                  {item.actor_name ? item.actor_name.slice(0, 1).toUpperCase() : "?"}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-neutral-900">
                      {item.actor_name || "System"}
                    </span>
                    <span className="text-xs text-neutral-500">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-neutral-700">
                    {item.action === "create" ? "Created work order" : null}
                    {item.action === "update" && item.after_json?.status 
                      ? `Changed status to ${String(item.after_json.status)}` 
                      : null}
                    {item.action === "update" && !item.after_json?.status ? "Updated work order" : null}
                    {item.action === "assign" ? (
                      <span>
                        {(() => {
                          const afterName =
                            typeof item.after_json?.assignee_name === "string"
                              ? item.after_json.assignee_name
                              : null;
                          const afterId =
                            typeof item.after_json?.assignee_user_id === "string"
                              ? item.after_json.assignee_user_id
                              : null;
                          const resolved =
                            afterName ||
                            (afterId
                              ? assignableUsers.find((u) => u.id === afterId)?.full_name ||
                                assignableUsers.find((u) => u.id === afterId)?.email
                              : null);
                          return resolved
                            ? t("assigned_work_order_to", { name: resolved })
                            : t("assigned_work_order");
                        })()}
                        {item.before_json?.status &&
                        item.after_json?.status &&
                        String(item.before_json.status) !== String(item.after_json.status)
                          ? ` · ${t("status")}: ${String(item.before_json.status)} → ${String(item.after_json.status)}`
                          : ""}
                      </span>
                    ) : null}
                    {item.action === "comment" ? (
                      <span className="whitespace-pre-wrap">
                        {`Commented: ${JSON.stringify(String(item.content ?? ""))}`}
                      </span>
                    ) : null}
                    {item.action === "document" ? (
                      <span className="flex flex-wrap items-center gap-2">
                        🔗{" "}
                        {item.description === REPORT_PDF_DOC ? (
                          <>
                            {t("report_pdf_saved") || "Report PDF"}:{" "}
                            <button
                              type="button"
                              className="text-primary-600 hover:underline"
                              onClick={() => {
                                const doc = documents.find((x) => x.id === item.id);
                                if (doc) void downloadWorkOrderDocument(doc);
                              }}
                            >
                              {item.file_name}
                            </button>
                          </>
                        ) : (
                          <>
                            {t("uploaded_document") || "Uploaded document"}:{" "}
                            <a
                              href={`/api/v1/uploads/${item.file_url}`}
                              className="text-primary-600 hover:underline"
                              target="_blank"
                              rel="noreferrer"
                            >
                              {item.file_name}
                            </a>
                          </>
                        )}
                      </span>
                    ) : null}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
