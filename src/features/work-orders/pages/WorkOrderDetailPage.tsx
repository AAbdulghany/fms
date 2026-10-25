import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiFetch, apiFetchBlob, downloadAuthenticatedFile, resolveApiError } from "@/lib/api";
import { displayWorkOrderTitle } from "@/lib/workOrderDisplay";
import type { AuditLog, Comment, MaintenanceReport, ReportTemplate, WorkOrder, WorkOrderDocument, WorkOrderStatus, WorkOrderUserBrief } from "@/lib/types";
import { WorkOrderRequestReviewModal } from "@/features/work-orders/components/WorkOrderRequestReviewModal";
import {
  WorkOrderJobDashboard,
  type MasterCtaKind,
} from "@/features/work-orders/components/WorkOrderJobDashboard";
import { WorkOrderSteppedReport } from "@/features/work-orders/components/WorkOrderSteppedReport";
import { SlideNotices } from "@/shared/components/SlideNotice";

interface UserMe {
  id: string;
  role: string;
}

/** Must match backend `REPORT_PDF_DOC_DESCRIPTION` in work_orders.py */
const REPORT_PDF_DOC = "report_pdf_export";

const REPORT_UNLOCKED_STATUSES = new Set<WorkOrderStatus>([
  "in_progress",
  "on_hold",
  "completed",
  "verified",
  "closed",
]);

const ALLOWED_TRANSITIONS: Record<WorkOrderStatus, WorkOrderStatus[]> = {
  requested: ["created", "declined"],
  declined: [],
  created: ["assigned", "cancelled"],
  assigned: ["in_progress", "on_hold", "cancelled"],
  in_progress: ["completed", "on_hold", "cancelled"],
  on_hold: ["in_progress", "cancelled"],
  completed: ["verified", "cancelled"],
  verified: ["closed", "cancelled"],
  closed: [],
  cancelled: [],
};

function statusAllowsReport(status: WorkOrderStatus): boolean {
  return REPORT_UNLOCKED_STATUSES.has(status);
}

type TemplateRow = ReportTemplate & { code?: string };

export function WorkOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t, i18n } = useTranslation();
  const [wo, setWo] = useState<WorkOrder | null>(null);
  const [report, setReport] = useState<MaintenanceReport | null>(null);
  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
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
  const [requestReviewOpen, setRequestReviewOpen] = useState(false);
  const [holdModalOpen, setHoldModalOpen] = useState(false);
  const [holdReason, setHoldReason] = useState("");
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [pdfLang, setPdfLang] = useState<"ar" | "en">(i18n.language === "ar" ? "ar" : "en");
  const [detailTab, setDetailTab] = useState<"job" | "report" | "history">("job");
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [phoneReportOpen, setPhoneReportOpen] = useState(false);
  const [savingReport, setSavingReport] = useState(false);

  function isDesktopViewport(): boolean {
    return typeof window !== "undefined" && window.matchMedia("(min-width: 1024px)").matches;
  }

  // Phone has no Report tab — keep Work selected if state was left on report.
  useEffect(() => {
    if (detailTab !== "report") return;
    if (!isDesktopViewport()) setDetailTab("job");
  }, [detailTab]);

  function focusReportBox() {
    setDetailTab("job");
    if (!isDesktopViewport()) return;
    window.setTimeout(() => {
      document.getElementById("wo-report-box")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }

  async function openReportEditor() {
    if (report && report.status !== "draft") {
      setReportModalOpen(false);
      setPhoneReportOpen(false);
      return;
    }
    // Report submit only allowed in in_progress / on_hold — promote from assigned first.
    if (wo && (wo.status === "assigned" || wo.status === "created")) {
      try {
        await patchStatus(undefined, "in_progress", { focusReport: false });
      } catch {
        return;
      }
    }
    if (!report) {
      try {
        await saveReport();
      } catch {
        return;
      }
    }
    setDetailTab("job");
    if (isDesktopViewport()) {
      setReportModalOpen(true);
    } else {
      setPhoneReportOpen(true);
    }
  }
  const [inspectorNote, setInspectorNote] = useState("");
  const [savingNote, setSavingNote] = useState(false);

  const loadReportData = async (w: WorkOrder, woId: string) => {
    let resolvedTemplate: ReportTemplate | null = null;
    if (w.template_id) {
      try {
        const catQ = w.asset_category
          ? `?asset_category=${encodeURIComponent(w.asset_category)}`
          : "";
        resolvedTemplate = await apiFetch<ReportTemplate>(`/report-templates/${w.template_id}${catQ}`);
      } catch {
        resolvedTemplate = null;
      }
    }
    if (!resolvedTemplate) {
      try {
        const templates = await apiFetch<TemplateRow[]>("/report-templates");
        resolvedTemplate =
          templates.find((tmpl) => tmpl.code === "STD-INSP") ?? templates[0] ?? null;
      } catch {
        resolvedTemplate = null;
      }
    }
    setTemplate(resolvedTemplate);

    try {
      const r = await apiFetch<MaintenanceReport>(`/work-orders/${woId}/report`);
      setReport(r);
      const aj = (r.answers_json as Record<string, unknown>) || {};
      setAnswers(aj);
    } catch {
      setReport(null);
      setAnswers({});
    }
  };

  const load = async () => {
    if (!id) return;
    setErr(null);
    setWo(null);
    try {
      const w = await apiFetch<WorkOrder>(`/work-orders/${id}`);
      setWo(w);

      // Load /users/me on its own — a failure in history/comments/etc. must not
      // leave `me` null (Assign to me depends on me.id).
      void apiFetch<UserMe>("/users/me")
        .then((user) => setMe(user))
        .catch(() => {
          /* keep prior me if any */
        });

      void Promise.all([
        apiFetch<AuditLog[]>(`/work-orders/${id}/history`),
        apiFetch<Comment[]>(`/work-orders/${id}/comments`),
        apiFetch<WorkOrderUserBrief[]>(`/work-orders/${id}/assignable-users`),
        apiFetch<WorkOrderDocument[]>(`/work-orders/${id}/documents`),
      ])
        .then(([hist, comm, assignable, docs]) => {
          setHistory(hist);
          setComments(comm);
          setAssignableUsers(assignable);
          setDocuments(docs);
        })
        .catch(() => {
          /* secondary data — page remains usable */
        });

      void loadReportData(w, id);
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

  useEffect(() => {
    if (!msg) return;
    const timer = window.setTimeout(() => setMsg(null), 5000);
    return () => window.clearTimeout(timer);
  }, [msg]);

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

  const referenceDocuments = useMemo(
    () => documents.filter((d) => d.description !== REPORT_PDF_DOC),
    [documents]
  );

  const siteAddressLine = wo
    ? [wo.site_address, wo.site_city, wo.site_country].filter(Boolean).join(", ")
    : "";

  if (!wo) {
    return (
      <div className="flex min-h-[240px] flex-col items-center justify-center gap-3">
        {err ? (
          <p className="rounded-md bg-error-light px-4 py-3 text-sm text-error-dark">{err}</p>
        ) : (
          <>
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            <p className="text-sm text-neutral-500">{t("loading")}</p>
          </>
        )}
      </div>
    );
  }

  async function saveReport(e?: FormEvent, opts?: { close?: boolean }) {
    e?.preventDefault();
    if (!id) throw new Error(t("error_generic") || "Missing work order");
    setMsg(null);
    setErr(null);
    setSavingReport(true);
    let payload = { ...answers };

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
      setSavingReport(false);
      const msg = t("error_photo_upload") || "Photo upload failed";
      setErr(msg);
      throw e instanceof Error ? e : new Error(msg);
    }

    if (Object.keys(photoRefs).length > 0) {
      payload = { ...payload, photos: photoRefs };
    }
    try {
      const r = await apiFetch<MaintenanceReport>(`/work-orders/${id}/report`, {
        method: "PUT",
        json: { answers: payload, pdf_lang: pdfLang },
      });
      setReport(r);
      setMsg(t("saved") || "Saved");
      if (opts?.close) {
        setReportModalOpen(false);
        setPhoneReportOpen(false);
      }
      await load();
      return r;
    } catch (e) {
      const msg = resolveApiError(e, t, i18n.language, t("error_generic"));
      setErr(msg);
      throw e instanceof Error ? e : new Error(msg);
    } finally {
      setSavingReport(false);
    }
  }

  async function submitReport(opts?: { approve?: boolean }) {
    if (!id) return;
    setMsg(null);
    setErr(null);
    setSavingReport(true);
    let submitted = false;
    try {
      // Backend rejects submit unless WO is in_progress / on_hold.
      if (wo && (wo.status === "assigned" || wo.status === "created")) {
        await patchStatus(undefined, "in_progress", { focusReport: false });
      }
      await saveReport();
      setSavingReport(true);
      const r = await apiFetch<MaintenanceReport>(
        `/work-orders/${id}/report/submit?pdf_lang=${encodeURIComponent(pdfLang)}`,
        { method: "POST" }
      );
      submitted = true;
      setReport(r);
      setReportModalOpen(false);
      setPhoneReportOpen(false);
      setDetailTab("job");
      if (opts?.approve) {
        await apiFetch(`/reports/${r.id}/approve`, { method: "POST" });
        setMsg(t("report_has_been_approved") || "Report approved");
      } else {
        setMsg(t("report_submitted") || "Report submitted.");
      }
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
      if (submitted) {
        setReportModalOpen(false);
        setPhoneReportOpen(false);
      }
    } finally {
      setSavingReport(false);
    }
  }

  async function reopenReportForEdit() {
    if (!id) return;
    setErr(null);
    setSavingReport(true);
    try {
      const r = await apiFetch<MaintenanceReport>(`/work-orders/${id}/report/reopen`, {
        method: "POST",
      });
      setReport(r);
      setDetailTab("job");
      if (isDesktopViewport()) setReportModalOpen(true);
      else setPhoneReportOpen(true);
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setSavingReport(false);
    }
  }

  async function exportReportPdf(lang: "ar" | "en") {
    if (!report?.id) return;
    setErr(null);
    try {
      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
      await downloadAuthenticatedFile(
        `/reports/${report.id}/pdf?lang=${lang}`,
        `maintenance-report-${lang}-${stamp}.pdf`
      );
      // Refresh WO so "Saved report PDFs" shows the newly generated file.
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Export failed");
    }
  }

  async function downloadWorkOrderDocument(doc: WorkOrderDocument) {
    if (!id) return;
    setErr(null);
    try {
      if (doc.description === REPORT_PDF_DOC) {
        // Always regenerate (verified/closed WOs included) — never serve a stale saved file.
        const name = (doc.file_name || "").toLowerCase();
        const lang: "ar" | "en" = name.includes("-ar-") || name.includes("_ar_") ? "ar" : "en";
        await exportReportPdf(lang);
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

  async function patchStatus(
    extraPayload?: Record<string, string>,
    statusOverride?: WorkOrderStatus,
    options?: { focusReport?: boolean }
  ) {
    const targetStatus = statusOverride ?? nextStatus;
    if (!id || !targetStatus || !wo) return;
    setMsg(null);
    setErr(null);
    try {
      const updated = await apiFetch<WorkOrder>(`/work-orders/${id}`, {
        method: "PATCH",
        json: { status: targetStatus, ...extraPayload },
      });
      setWo(updated);
      setNextStatus("");
      await load();
      if (
        options?.focusReport !== false &&
        (statusAllowsReport(targetStatus) || statusAllowsReport(updated.status))
      ) {
        focusReportBox();
      }
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  function handleRailTransition(status: WorkOrderStatus) {
    setNextStatus(status);
    if (status === "on_hold") {
      setHoldReason("");
      setHoldModalOpen(true);
      return;
    }
    if (status === "cancelled") {
      setCancelReason("");
      setCancelModalOpen(true);
      return;
    }
    if (status === "completed" && (!report || (report.status !== "submitted" && report.status !== "approved"))) {
      setErr(t("error_report_required") || "The maintenance report must be submitted before marking as completed.");
      setDetailTab("job");
      focusReportBox();
      return;
    }
    void patchStatus(undefined, status);
  }

  async function handleMasterCta(kind: MasterCtaKind) {
    if (!id || !wo) return;
    setErr(null);
    setMsg(null);
    try {
      if (kind === "assign_me") {
        if (!me?.id) {
          setErr(t("error_session") || "Session missing — refresh and try again.");
          return;
        }
        const updated = await apiFetch<WorkOrder>(`/work-orders/${id}/assign`, {
          method: "POST",
          json: { assignee_user_id: String(me.id) },
        });
        setWo(updated);
        setSelectedAssignee("");
        setAssigneeSearch("");
        setMsg(t("assigned_ok") || "Assigned successfully.");
        await load();
        return;
      }
      if (kind === "assign_selected") {
        if (!selectedAssignee) return;
        await assignUser(selectedAssignee);
        return;
      }
      if (kind === "fill_report") {
        if (wo.status === "assigned" || wo.status === "created") {
          await patchStatus(undefined, "in_progress");
        }
        await openReportEditor();
        return;
      }
      if (kind === "complete") {
        void handleRailTransition("completed");
        return;
      }
      if (kind === "verify") {
        void handleRailTransition("verified");
        return;
      }
      if (kind === "close") {
        void handleRailTransition("closed");
      }
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function assignUser(userId: string) {
    if (!id || !userId) return;
    setErr(null);
    setMsg(null);
    try {
      if (!canAssignOthers && userId !== me?.id) {
        setErr(t("error_forbidden") || "You cannot assign this work order to someone else.");
        return;
      }
      const updated = await apiFetch<WorkOrder>(`/work-orders/${id}/assign`, {
        method: "POST",
        json: { assignee_user_id: userId },
      });
      setWo(updated);
      setSelectedAssignee("");
      setAssigneeSearch("");
      setMsg(t("assigned_ok") || "Assigned successfully.");
      setReportModalOpen(false);
      setPhoneReportOpen(false);
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function closeWorkOrder() {
    if (!id || !wo) return;
    if (wo.status !== "completed" && wo.status !== "verified") return;
    setErr(null);
    setMsg(null);
    try {
      if (wo.status === "completed") {
        await apiFetch<WorkOrder>(`/work-orders/${id}`, {
          method: "PATCH",
          json: { status: "verified" },
        });
      }
      const updated = await apiFetch<WorkOrder>(`/work-orders/${id}`, {
        method: "PATCH",
        json: { status: "closed" },
      });
      setWo(updated);
      setReportModalOpen(false);
      setPhoneReportOpen(false);
      setMsg(t("closed") || "Closed");
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    }
  }

  async function saveInspectorNote() {
    if (!id || !inspectorNote.trim() || !wo) return;
    setSavingNote(true);
    setErr(null);
    try {
      const note = inspectorNote.trim();
      await apiFetch(`/work-orders/${id}/comments`, {
        method: "POST",
        json: { content: `[Inspector] ${note}` },
      });
      const nextAnswers = {
        ...answers,
        inspector_notes: [answers.inspector_notes, note].filter(Boolean).join("\n\n"),
      };
      setAnswers(nextAnswers);
      if (statusAllowsReport(wo.status) || report) {
        try {
          await apiFetch(`/work-orders/${id}/report`, {
            method: "PUT",
            json: { answers: nextAnswers, pdf_lang: pdfLang },
          });
        } catch {
          /* comment still saved */
        }
      }
      setInspectorNote("");
      const comm = await apiFetch<Comment[]>(`/work-orders/${id}/comments`);
      setComments(comm);
      setDetailTab("history");
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
    } finally {
      setSavingNote(false);
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

  async function sendApprovalTo(userId: string) {
    if (!id || !userId) return;
    setErr(null);
    setMsg(null);
    try {
      const updated = await apiFetch<WorkOrder>(`/work-orders/${id}/report/send-approval`, {
        method: "POST",
        json: { assignee_user_id: userId },
      });
      setWo(updated);
      setSelectedAssignee("");
      setAssigneeSearch("");
      setMsg(t("wo_waiting_manager"));
      await load();
    } catch (e) {
      setErr(resolveApiError(e, t, i18n.language, t("error_generic")));
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


  const canEditReport = true; // All users can fill reports
  const canApprove =
    me?.role === "company_admin" ||
    me?.role === "client_admin" ||
    me?.role === "manager" ||
    me?.role === "super_admin";
  const canAdminWO =
    me?.role === "company_admin" ||
    me?.role === "company_engineer" ||
    me?.role === "super_admin" ||
    me?.role === "site_manager" ||
    me?.role === "technician";
  // Reassign is admin/engineer only — not technicians or site managers.
  const canAssignOthers =
    me?.role === "company_admin" ||
    me?.role === "company_engineer" ||
    me?.role === "super_admin";
  const canEditDiagnostics = !!canAdminWO;
  const canReviewRequest =
    wo.status === "requested" &&
    (me?.role === "company_admin" || me?.role === "super_admin");

  const reportPhaseUnlocked = statusAllowsReport(wo.status);
  const allowedNext = ALLOWED_TRANSITIONS[wo.status] ?? [];

  const reportPanelContent = (
            <div className="space-y-3">
              {!reportPhaseUnlocked && template ? (
                <p className="text-sm text-neutral-600">
                  {t("report_unlocked_at_in_progress") ||
                    "The maintenance report is available once this work order is in progress."}
                </p>
              ) : null}
              {reportPhaseUnlocked && !template ? (
                <p className="text-sm text-neutral-500">{t("no_report")}</p>
              ) : null}
              {reportPhaseUnlocked && template ? (
                <>
                  {(!report || report.status === "draft") && (
                    <p className="hidden text-xs text-neutral-500 lg:block">
                      {t("report_card_hint") ||
                        "Open the window to start or edit the report. Export regenerates a fresh PDF every time."}
                    </p>
                  )}
                  {reportPdfDocuments.length > 0 && (
                    <div className="rounded-md bg-neutral-50 p-3">
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
                  {report && (
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className="min-h-10 rounded-md border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-50"
                        onClick={() => void exportReportPdf("ar")}
                      >
                        {t("export_report_ar") || "Export PDF (Arabic)"}
                      </button>
                      <button
                        type="button"
                        className="min-h-10 rounded-md border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-50"
                        onClick={() => void exportReportPdf("en")}
                      >
                        {t("export_report_en") || "Export PDF (English)"}
                      </button>
                    </div>
                  )}
                  {(!report || report.status === "draft") && (
                    <button
                      type="button"
                      className="min-h-11 w-full rounded-md bg-primary-600 px-4 py-2.5 text-sm font-medium text-neutral-0 hover:bg-primary-700"
                      onClick={() => void openReportEditor()}
                    >
                      {!report
                        ? t("start_report") || "Start report"
                        : t("wo_view_edit_report")}
                    </button>
                  )}
                </>
              ) : null}
            </div>
  );

  return (
    <div className="space-y-4 lg:space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-neutral-900 lg:text-2xl">
          <span className="lg:hidden">
            {displayWorkOrderTitle(wo, i18n.language)}
          </span>
          <span className="hidden lg:inline">
            {displayWorkOrderTitle(wo, i18n.language)}
          </span>
        </h1>
        <p className="hidden flex-wrap items-center gap-2 text-sm text-neutral-500 lg:flex">
          <span className="font-mono text-xs text-neutral-400">{wo.id}</span>
          {wo.asset_name && <span>· {wo.asset_name}</span>}
        </p>
      </div>

      {/* Phone: Work | History only. Desktop: Job | Report | History. */}
      <div
        className="grid grid-cols-2 gap-1 rounded-xl bg-primary-50 p-1 lg:hidden"
        role="tablist"
        aria-label={t("wo_tab_work")}
      >
        {(
          [
            ["job", "wo_tab_work"],
            ["history", "wo_tab_history"],
          ] as const
        ).map(([tabId, key]) => (
          <button
            key={tabId}
            type="button"
            role="tab"
            aria-selected={detailTab === tabId}
            className={`min-h-10 rounded-lg px-2 py-2 text-sm font-semibold ${
              detailTab === tabId
                ? "bg-primary-700 text-white shadow-sm"
                : "text-neutral-500"
            }`}
            onClick={() => setDetailTab(tabId)}
          >
            {t(key)}
          </button>
        ))}
      </div>
      <div
        className="hidden border-b border-neutral-200 lg:flex"
        role="tablist"
      >
        {(
          [
            ["job", "wo_tab_job"],
            ["report", "wo_tab_report"],
            ["history", "wo_tab_history"],
          ] as const
        ).map(([tabId, key]) => (
          <button
            key={tabId}
            type="button"
            role="tab"
            aria-selected={detailTab === tabId}
            className={`min-h-11 border-b-2 px-4 py-2.5 text-sm font-medium ${
              detailTab === tabId
                ? "border-primary-600 text-primary-700"
                : "border-transparent text-neutral-500 hover:text-neutral-800"
            }`}
            onClick={() => setDetailTab(tabId)}
          >
            {t(key)}
          </button>
        ))}
      </div>

      <SlideNotices success={msg} error={wo ? err : null} />

      {detailTab === "job" && (
        <WorkOrderJobDashboard
          wo={wo}
          report={report}
          allowedNext={allowedNext}
          canAdminWO={!!canAdminWO}
          canAssignOthers={!!canAssignOthers}
          canEditDiagnostics={canEditDiagnostics}
          meId={me?.id ?? null}
          assignableUsers={assignableUsers}
          filteredAssignable={filteredAssignable}
          assigneeSearch={assigneeSearch}
          selectedAssignee={selectedAssignee}
          onAssigneeSearchChange={(v) => {
            setAssigneeSearch(v);
            setSelectedAssignee("");
          }}
          onSelectAssignee={(uid, label) => {
            setSelectedAssignee(uid);
            setAssigneeSearch(label);
          }}
          inspectorNote={inspectorNote}
          savingNote={savingNote}
          onInspectorNoteChange={setInspectorNote}
          onSaveInspectorNote={() => void saveInspectorNote()}
          onMasterCta={(kind) => void handleMasterCta(kind)}
          onSecondaryTransition={handleRailTransition}
          onWoSaved={setWo}
          siteAddressLine={siteAddressLine}
          canEditReport={canEditReport && reportPhaseUnlocked}
          savingReport={savingReport}
          onSaveReport={() => void saveReport()}
          onSubmitReport={() => void submitReport()}
          onStartReport={() => void openReportEditor()}
          phoneReportOpen={phoneReportOpen}
          onPhoneReportOpenChange={setPhoneReportOpen}
          onExportReport={(lang) => void exportReportPdf(lang)}
          onPreviewReport={async (lang) => {
            if (!report?.id) return null;
            setErr(null);
            try {
              const blob = await apiFetchBlob(`/reports/${report.id}/pdf?lang=${lang}`);
              return URL.createObjectURL(blob);
            } catch (e) {
              setErr(e instanceof Error ? e.message : "Export failed");
              return null;
            }
          }}
          onConfirmReport={() => {
            if (allowedNext.includes("completed")) void handleMasterCta("complete");
            else if (allowedNext.includes("verified")) void handleMasterCta("verify");
          }}
          onEditReport={() => void reopenReportForEdit()}
          canApprove={!!canApprove}
          canHandOffApproval={
            me?.role === "technician" ||
            me?.role === "company_engineer" ||
            me?.role === "site_manager"
          }
          onSendApproval={(userId) => void sendApprovalTo(userId)}
          onAssignUser={(userId) => void assignUser(userId)}
          onFinishReport={() => void submitReport()}
          onSendToApprove={() => void submitReport({ approve: !!canApprove })}
          onApproveReport={() => void approveReport()}
          onCloseWorkOrder={() => void closeWorkOrder()}
          canCloseWorkOrder={
            !!canApprove ||
            me?.role === "company_engineer" ||
            me?.role === "site_manager"
          }
          phoneReport={
            report && report.status === "draft" ? (
              <WorkOrderSteppedReport
                woSource={wo.source || "corrective"}
                workOrderId={wo.id}
                answers={answers}
                setAnswers={setAnswers}
                photos={photos}
                setPhotos={setPhotos}
                canEdit={canEditReport}
                isDraft
                jobStartedAt={wo.job_started_at}
                jobHours={wo.job_hours}
                pdfLang={pdfLang}
                setPdfLang={setPdfLang}
                onSave={async () => {
                  await saveReport(undefined, { close: true });
                }}
                submitLabel={t("wo_finish_report")}
                onSubmit={() => submitReport()}
                saving={savingReport}
              />
            ) : null
          }
          reportPanel={<div className="hidden lg:block">{reportPanelContent}</div>}
        />
      )}

      {detailTab === "report" && (
        <div
          id="wo-report-box"
          className="hidden scroll-mt-20 space-y-4 rounded-xl border border-neutral-200 bg-neutral-0 p-4 shadow-sm lg:block lg:p-6"
        >
          {reportPanelContent}
        </div>
      )}

      {reportModalOpen && (!report || report.status === "draft") && (
      <>
      <div
        className="fixed inset-0 z-40 bg-black/40"
        onMouseDown={() => setReportModalOpen(false)}
      />
      <div
        className="fixed left-1/2 top-14 z-50 max-h-[85vh] w-full max-w-2xl -translate-x-1/2 overflow-y-auto rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-xl"
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
              <div className="space-y-4">
                {referenceDocuments.length > 0 && (
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
                    <p className="text-xs font-medium uppercase tracking-wide text-neutral-600">
                      {t("reference_documents") || "Reference documents"}
                    </p>
                    <ul className="mt-2 space-y-1">
                      {referenceDocuments.map((doc) => (
                        <li key={doc.id}>
                          <button
                            type="button"
                            className="text-sm text-primary-700 hover:underline"
                            onClick={() => void downloadWorkOrderDocument(doc)}
                          >
                            {doc.file_name}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {report.status === "draft" && (
                  <WorkOrderSteppedReport
                    woSource={wo.source || "corrective"}
                    workOrderId={wo.id}
                    answers={answers}
                    setAnswers={setAnswers}
                    photos={photos}
                    setPhotos={setPhotos}
                    canEdit={canEditReport}
                    isDraft
                    jobStartedAt={wo.job_started_at}
                    jobHours={wo.job_hours}
                    pdfLang={pdfLang}
                    setPdfLang={setPdfLang}
                    onSave={async () => {
                      await saveReport(undefined, { close: true });
                    }}
                    submitLabel={t("wo_finish_report")}
                    onSubmit={() => submitReport()}
                  />
                )}
              </div>
            )}
      </div>
      </>
      )}


      {detailTab === "job" &&
        (wo.status === "verified" || wo.status === "closed") &&
        canAdminWO && (
        <div className="flex flex-wrap items-end gap-3 rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-600" htmlFor="wo-invoice-currency">
              {t("invoice_currency")}
            </label>
            <select
              id="wo-invoice-currency"
              className="rounded-md border border-neutral-300 px-2 py-1.5 text-sm"
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
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            onClick={() => void generateInvoice()}
          >
            {t("generate_invoice")}
          </button>
        </div>
      )}

      {canReviewRequest && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3">
          <p className="text-sm text-orange-900">{t("pending_request_banner")}</p>
          <button
            type="button"
            className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            onClick={() => setRequestReviewOpen(true)}
          >
            {t("review_request")}
          </button>
        </div>
      )}

      {requestReviewOpen && (
        <WorkOrderRequestReviewModal
          workOrder={wo}
          open
          onClose={() => setRequestReviewOpen(false)}
          onResolved={() => void load()}
        />
      )}

      {/* History tab — comments + activity only */}
      <div className={detailTab === "history" ? "space-y-4 lg:space-y-6" : "hidden"}>
      <div className="rounded-xl border border-neutral-200 bg-neutral-0 p-4 shadow-sm lg:p-6">
        <h2 className="mb-4 text-base font-medium text-neutral-800 lg:text-lg">{t("comments") || "Comments & Documents"}</h2>
        
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
              <svg className="h-5 w-5 text-neutral-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                />
              </svg>
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
        <div className="rounded-xl border border-neutral-200 bg-neutral-0 p-4 shadow-sm lg:p-6">
          <h2 className="mb-4 text-base font-medium text-neutral-800 lg:text-lg">{t("history") || "Activity History"}</h2>
          <div className="space-y-3 border-s-2 border-primary-200 ps-3 lg:border-s-0 lg:ps-0">
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
                    {item.action === "create" ? t("history_created_wo") : null}
                    {item.action === "request" ? t("history_submitted_request") : null}
                    {item.action === "update" && item.before_json?.status && item.after_json?.status
                      ? `${t("history_status_changed")}: ${String(item.before_json.status)} → ${String(item.after_json.status)}${
                          item.after_json.decline_reason
                            ? ` — ${t("decline_reason")}: ${String(item.after_json.decline_reason)}`
                            : ""
                        }`
                      : null}
                    {item.action === "update" && item.after_json?.status && !item.before_json?.status
                      ? `${t("history_status_changed")}: ${String(item.after_json.status)}`
                      : null}
                    {item.action === "update" && !item.after_json?.status ? t("history_updated_wo") : null}
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
                        {" "}
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

      {holdModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl bg-neutral-0 p-6 shadow-xl">
            <h3 className="mb-2 text-lg font-semibold text-neutral-900">
              {t("hold_reason_title") || "Reason for Hold"}
            </h3>
            <p className="mb-4 text-sm text-neutral-600">
              {t("hold_reason_hint") || "Provide a reason for placing this work order on hold."}
            </p>
            <textarea
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              rows={4}
              value={holdReason}
              onChange={(e) => setHoldReason(e.target.value)}
              placeholder={t("hold_reason_placeholder") || "Enter hold reason…"}
              autoFocus
            />
            <div className="mt-4 flex justify-end gap-3">
              <button
                className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100"
                onClick={() => setHoldModalOpen(false)}
              >
                {t("cancel")}
              </button>
              <button
                className="rounded-md bg-neutral-800 px-4 py-2 text-sm font-medium text-neutral-0 hover:bg-neutral-900 disabled:opacity-50"
                disabled={!holdReason.trim()}
                onClick={() => {
                  setHoldModalOpen(false);
                  void patchStatus({ hold_reason: holdReason.trim() }, "on_hold");
                }}
              >
                {t("apply") || "Apply"}
              </button>
            </div>
          </div>
        </div>
      )}

      {cancelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl bg-neutral-0 p-6 shadow-xl">
            <h3 className="mb-2 text-lg font-semibold text-neutral-900">
              {t("cancel_reason_title") || "Reason for Cancellation"}
            </h3>
            <p className="mb-4 text-sm text-neutral-600">
              {t("cancel_reason_hint") || "Provide a reason for cancelling this work order."}
            </p>
            <textarea
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              rows={4}
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder={t("cancel_reason_placeholder") || "Enter cancellation reason…"}
              autoFocus
            />
            <div className="mt-4 flex justify-end gap-3">
              <button
                className="rounded-md px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-100"
                onClick={() => setCancelModalOpen(false)}
              >
                {t("cancel")}
              </button>
              <button
                className="rounded-md bg-error-dark px-4 py-2 text-sm font-medium text-neutral-0 hover:bg-error-main disabled:opacity-50"
                disabled={!cancelReason.trim()}
                onClick={() => {
                  setCancelModalOpen(false);
                  void patchStatus({ cancellation_reason: cancelReason.trim() }, "cancelled");
                }}
              >
                {t("confirm") || "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}