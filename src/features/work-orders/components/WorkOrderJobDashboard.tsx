import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import type {
  MaintenanceReport,
  WorkOrder,
  WorkOrderStatus,
  WorkOrderUserBrief,
} from "@/lib/types";
import { workOrderStatusPillClass } from "@/lib/workOrderDisplay";
import { WorkOrderDiagnosticsPanel } from "@/features/work-orders/components/WorkOrderDiagnosticsPanel";

export type MasterCtaKind =
  | "assign_me"
  | "assign_selected"
  | "fill_report"
  | "complete"
  | "verify"
  | "close"
  | "none";

interface Props {
  wo: WorkOrder;
  report: MaintenanceReport | null;
  allowedNext: WorkOrderStatus[];
  canAdminWO: boolean;
  canAssignOthers: boolean;
  canEditDiagnostics: boolean;
  meId: string | null;
  assignableUsers: WorkOrderUserBrief[];
  filteredAssignable: WorkOrderUserBrief[];
  assigneeSearch: string;
  selectedAssignee: string;
  onAssigneeSearchChange: (v: string) => void;
  onSelectAssignee: (id: string, label: string) => void;
  inspectorNote: string;
  savingNote: boolean;
  onInspectorNoteChange: (v: string) => void;
  onSaveInspectorNote: () => void;
  onMasterCta: (kind: MasterCtaKind) => void;
  onSecondaryTransition: (status: WorkOrderStatus) => void;
  onWoSaved: (wo: WorkOrder) => void;
  /** Desktop companion report panel (lg+). */
  reportPanel: ReactNode;
  /** Phone inline stepped report (no Report tab). */
  phoneReport?: ReactNode;
  onSaveReport?: () => void;
  onSubmitReport?: () => void;
  onStartReport?: () => void;
  savingReport?: boolean;
  canEditReport?: boolean;
  siteAddressLine?: string;
  /** Phone report sheet. Parent owns it so status errors can open it. */
  phoneReportOpen?: boolean;
  onPhoneReportOpenChange?: (open: boolean) => void;
  onExportReport?: (lang: "ar" | "en") => void;
  /** Return a blob URL for the report PDF so it can be shown in the page. */
  onPreviewReport?: (lang: "ar" | "en") => Promise<string | null>;
  onConfirmReport?: () => void;
  onEditReport?: () => void;
  /** Manager, company admin, client admin, or super admin can approve a report. */
  canApprove?: boolean;
  /** Assign the typed or picked user. */
  onAssignUser?: (userId: string) => void;
  /** Submit the saved draft so it can be sent for approval. */
  onFinishReport?: () => void;
  /** Submit the draft. Managers approve in the same step. */
  onSendToApprove?: () => void;
  /** Engineer or technician names an approver after the report is submitted. */
  canHandOffApproval?: boolean;
  onSendApproval?: (userId: string) => void;
  /** Approve a report that is already submitted. */
  onApproveReport?: () => void;
  /** After approval: complete is a separate button; this closes the work order. */
  onCloseWorkOrder?: () => void;
  /** Roles allowed to verify and close. Technicians can complete, not close. */
  canCloseWorkOrder?: boolean;
}

/** Work / Job — phone: context + inline report + sticky bar; desktop: split panels. */
export function WorkOrderJobDashboard({
  wo,
  report,
  allowedNext,
  canAdminWO,
  canAssignOthers,
  canEditDiagnostics,
  meId: _meId,
  assignableUsers,
  filteredAssignable,
  assigneeSearch,
  selectedAssignee,
  onAssigneeSearchChange,
  onSelectAssignee,
  inspectorNote,
  savingNote,
  onInspectorNoteChange,
  onSaveInspectorNote,
  onMasterCta,
  onSecondaryTransition,
  onWoSaved,
  reportPanel,
  phoneReport,
  onSaveReport: _onSaveReport,
  onSubmitReport: _onSubmitReport,
  onStartReport,
  savingReport = false,
  canEditReport: _canEditReport = false,
  siteAddressLine = "",
  phoneReportOpen = false,
  onPhoneReportOpenChange,
  onExportReport: _onExportReport,
  onPreviewReport,
  onConfirmReport: _onConfirmReport,
  onEditReport,
  canApprove = false,
  onAssignUser,
  onFinishReport,
  onSendToApprove: _onSendToApprove,
  canHandOffApproval = false,
  onSendApproval,
  onApproveReport,
  onCloseWorkOrder,
  canCloseWorkOrder = false,
}: Props) {
  const { t } = useTranslation();
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [codesOpen, setCodesOpen] = useState(false);
  const [pdfOpened, setPdfOpened] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const secondary = allowedNext.filter((s) => s === "on_hold" || s === "cancelled");

  const codesStrip = [
    wo.failure_code,
    wo.symptom_code,
    wo.downtime_minutes != null ? `DT ${wo.downtime_minutes}m` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const reportReady =
    !!report && (report.status === "submitted" || report.status === "approved");
  const detailsSummary =
    [wo.company_name, wo.site_name, wo.asset_name || wo.asset_label_code].filter(Boolean).join(" · ") ||
    "—";

  const detailFields: { label: string; value: ReactNode; wide?: boolean }[] = [
    {
      label: t("status"),
      value: (
        <span className={workOrderStatusPillClass(wo.status)}>{t(wo.status) || wo.status}</span>
      ),
    },
    { label: t("company"), value: wo.company_name || "—" },
    { label: t("site"), value: wo.site_name || "—" },
    { label: t("address"), value: siteAddressLine || "—", wide: true },
    { label: t("location") || "Location", value: wo.location_name || "—" },
    {
      label: t("asset"),
      value: wo.asset_id ? (
        <Link to={`/assets/${wo.asset_id}`} className="text-primary-700 hover:underline">
          {wo.asset_name || wo.asset_label_code || wo.asset_id}
        </Link>
      ) : (
        "—"
      ),
    },
    { label: t("asset_category"), value: wo.asset_category || "—" },
    { label: t("asset_serial"), value: wo.asset_serial || "—" },
    { label: t("model") || "Model", value: wo.asset_model || "—" },
    { label: t("category") || "Category", value: wo.category || "—" },
    { label: t("source") || "Source", value: wo.source || "—" },
    { label: t("urgency") || "Urgency", value: wo.urgency || "—" },
    {
      label: t("assigned_to"),
      value: wo.assignee?.full_name || wo.assignee?.email || t("not_assigned"),
    },
    { label: t("description"), value: wo.description || "—", wide: true },
  ];

  const needsAssignment =
    wo.status === "created" ||
    wo.status === "requested" ||
    (!wo.assignee &&
      !wo.assignee_user_id &&
      !["cancelled", "closed", "declined", "completed", "verified"].includes(wo.status));
  const currentAssigneeId = wo.assignee?.id ?? wo.assignee_user_id ?? "";
  const typedName = assigneeSearch.trim();
  const singleMatchId =
    typedName && filteredAssignable.length === 1 ? filteredAssignable[0].id : "";
  const assignTarget = selectedAssignee || singleMatchId;
  const assignReady =
    !!assignTarget && assignTarget !== currentAssigneeId && typedName.length > 0;
  const reportDraft = report?.status === "draft";
  const reportSubmitted = report?.status === "submitted";
  const reportApproved = report?.status === "approved";
  const terminal = ["cancelled", "closed", "declined"].includes(wo.status);
  const approvalSent = !!wo.return_assignee_user_id;
  const showHandoff = canHandOffApproval && reportSubmitted && !approvalSent && !terminal;
  const approverRoles = ["company_admin", "client_admin", "manager", "super_admin"];
  const approvers = assignableUsers.filter((u) => approverRoles.includes(u.role));
  const nameQuery = typedName.replace(/\s*\([^)]*\)\s*$/, "").trim().toLowerCase();
  const matchesApprover = (u: WorkOrderUserBrief) => {
    const name = (u.full_name || "").toLowerCase();
    const email = (u.email || "").toLowerCase();
    return name.includes(nameQuery) || email.includes(nameQuery);
  };
  const typedApprovers = nameQuery ? approvers.filter(matchesApprover) : [];
  const pickerUsers = showHandoff ? typedApprovers : filteredAssignable;
  const selectedApprover = approvers.find((u) => u.id === selectedAssignee);
  const handoffTarget =
    (selectedApprover && selectedApprover.id !== currentAssigneeId ? selectedApprover.id : "") ||
    (typedApprovers.length === 1 && typedApprovers[0].id !== currentAssigneeId
      ? typedApprovers[0].id
      : "");
  const handoffReady = showHandoff && !!handoffTarget && nameQuery.length > 0;
  const canWorkReport = !terminal && !needsAssignment;
  const ctaClass =
    "flex min-h-11 w-full items-center justify-center rounded-xl bg-secondary-500 px-4 text-sm font-bold text-white hover:bg-secondary-600";
  const greenClass =
    "flex min-h-11 w-full items-center justify-center rounded-xl bg-emerald-600 px-4 text-sm font-bold text-white hover:bg-emerald-700";
  const redClass =
    "flex min-h-11 w-full items-center justify-center rounded-xl bg-red-600 px-4 text-sm font-bold text-white hover:bg-red-700";
  const quietClass =
    "flex min-h-11 w-full items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 px-4 text-sm font-semibold text-neutral-900";

  function statusBody(searchId: string) {
    return (
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className={workOrderStatusPillClass(wo.status)}>{t(wo.status) || wo.status}</span>
          {wo.assignee ? (
            <span className="text-xs text-neutral-600">
              {t("assigned_to")}: <strong>{wo.assignee.full_name || wo.assignee.email}</strong>
            </span>
          ) : (
            <span className="text-xs text-neutral-400">{t("not_assigned")}</span>
          )}
        </div>
        <p className="text-xs text-neutral-600">
          {t("report")}:{" "}
          <strong className="text-neutral-900">
            {report?.status
              ? t(report.status) !== report.status
                ? t(report.status)
                : report.status
              : t("not_started")}
          </strong>
        </p>

        {needsAssignment && canAdminWO && (
          <button type="button" className={ctaClass} onClick={() => onMasterCta("assign_me")}>
            {t("wo_cta_assign_to_me")}
          </button>
        )}

        {(showHandoff ||
          (canAssignOthers &&
            !(canHandOffApproval && approvalSent) &&
            ["created", "requested", "assigned", "in_progress", "on_hold"].includes(wo.status))) && (
            <div>
              <label className="mb-1 block text-xs font-medium text-neutral-600" htmlFor={searchId}>
                {showHandoff ? t("wo_send_approval_to") : t("wo_assign_someone")}
              </label>
              <div className="flex items-start gap-2">
                <input
                  id={searchId}
                  type="search"
                  className="min-h-11 min-w-0 flex-1 rounded-md border border-neutral-300 px-3 text-base"
                  placeholder={t("search_assignee") || "Search users…"}
                  value={assigneeSearch}
                  onChange={(e) => onAssigneeSearchChange(e.target.value)}
                  autoComplete="off"
                />
                {showHandoff && (
                  <button
                    type="button"
                    disabled={!handoffReady}
                    className="min-h-11 shrink-0 rounded-xl bg-emerald-600 px-3 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-40"
                    onClick={() => {
                      if (handoffReady) onSendApproval?.(handoffTarget);
                    }}
                  >
                    {t("wo_send_to_approve")}
                  </button>
                )}
                {!showHandoff && typedName.length > 0 && (
                  <button
                    type="button"
                    disabled={!assignReady}
                    className="min-h-11 shrink-0 rounded-xl bg-primary-700 px-3 text-sm font-bold text-white disabled:opacity-40"
                    onClick={() => {
                      if (assignReady) onAssignUser?.(assignTarget);
                    }}
                  >
                    {t("wo_cta_assign")}
                  </button>
                )}
              </div>
              {typedName && !selectedAssignee && pickerUsers.length > 0 && (
                <ul className="mt-1 max-h-40 overflow-auto rounded-md border border-neutral-200 bg-neutral-0 text-sm">
                  {pickerUsers.map((u) => (
                    <li key={u.id}>
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-start hover:bg-neutral-100"
                        onClick={() =>
                          onSelectAssignee(u.id, `${u.full_name || u.email} (${u.role})`)
                        }
                      >
                        <span className="font-medium">{u.full_name || u.email}</span>
                        <span className="ms-1 text-xs text-neutral-500">{u.role}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

        {canWorkReport && !report && (
          <button type="button" className={ctaClass} onClick={() => onStartReport?.()}>
            {t("wo_cta_fill_report") || "Fill report"}
          </button>
        )}
        {canWorkReport && reportDraft && (
          <div className="flex gap-2">
            <button
              type="button"
              className="flex min-h-11 flex-1 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 px-3 text-sm font-semibold text-neutral-900"
              onClick={() => {
                setPreviewMode(true);
                setPdfOpened(false);
                setPreviewUrl((prev) => {
                  if (prev) URL.revokeObjectURL(prev);
                  return null;
                });
                onPhoneReportOpenChange?.(true);
              }}
            >
              {t("view_report")}
            </button>
            <button
              type="button"
              className="flex min-h-11 flex-1 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 px-3 text-sm font-semibold text-neutral-900"
              onClick={() => {
                setPreviewMode(false);
                onStartReport?.();
              }}
            >
              {t("edit_report")}
            </button>
          </div>
        )}
        {canWorkReport && reportDraft && (
          <button type="button" className={greenClass} onClick={() => onFinishReport?.()}>
            {t("wo_finish_report")}
          </button>
        )}
        {reportSubmitted && (
          <div className="flex gap-2">
            <button
              type="button"
              className="flex min-h-11 flex-1 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 px-3 text-sm font-semibold text-neutral-900"
              onClick={() => {
                setPreviewMode(false);
                setPdfOpened(false);
                setPreviewUrl((prev) => {
                  if (prev) URL.revokeObjectURL(prev);
                  return null;
                });
                onPhoneReportOpenChange?.(true);
              }}
            >
              {t("view_report")}
            </button>
            <button
              type="button"
              className="flex min-h-11 flex-1 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-0 px-3 text-sm font-semibold text-neutral-900"
              onClick={() => onEditReport?.()}
            >
              {t("edit_report")}
            </button>
          </div>
        )}
        {reportSubmitted && canApprove && (
          <button type="button" className={greenClass} onClick={() => onApproveReport?.()}>
            {t("approve")}
          </button>
        )}
        {reportSubmitted && !canApprove && (!canHandOffApproval || approvalSent) && (
          <p className="rounded-lg bg-neutral-50 px-3 py-2 text-sm text-neutral-600">
            {t("wo_waiting_manager")}
          </p>
        )}
        {reportApproved && allowedNext.includes("completed") && canAdminWO && (
          <button type="button" className={greenClass} onClick={() => onMasterCta("complete")}>
            {t("wo_cta_complete")}
          </button>
        )}
        {(wo.status === "completed" || wo.status === "verified") && canCloseWorkOrder && (
          <button type="button" className={redClass} onClick={() => onCloseWorkOrder?.()}>
            {t("wo_cta_close")}
          </button>
        )}
        {reportApproved && (
          <button
            type="button"
            className={quietClass}
            onClick={() => {
              setPdfOpened(false);
              setPreviewUrl((prev) => {
                if (prev) URL.revokeObjectURL(prev);
                return null;
              });
              onPhoneReportOpenChange?.(true);
            }}
          >
            {t("view_report") || "View report"}
          </button>
        )}

        {canAdminWO && secondary.length > 0 && (
          <div className="flex gap-2">
            {secondary.includes("on_hold") && (
              <button
                type="button"
                className="min-h-11 flex-1 rounded-xl border border-neutral-300 text-sm font-semibold text-neutral-800"
                onClick={() => onSecondaryTransition("on_hold")}
              >
                {t("wo_cta_hold")}
              </button>
            )}
            {secondary.includes("cancelled") &&
              report?.status !== "approved" &&
              wo.status !== "completed" &&
              wo.status !== "verified" &&
              wo.status !== "closed" && (
              <button
                type="button"
                className="min-h-11 flex-1 rounded-xl border border-neutral-300 text-sm font-semibold text-neutral-800"
                onClick={() => onSecondaryTransition("cancelled")}
              >
                {t("wo_cta_cancel")}
              </button>
            )}
            {wo.status === "on_hold" && allowedNext.includes("in_progress") && (
              <button
                type="button"
                className="min-h-11 flex-1 rounded-xl border border-neutral-300 text-sm font-semibold text-neutral-800"
                onClick={() => onSecondaryTransition("in_progress")}
              >
                {t("wo_cta_resume")}
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  function closeReportSheet() {
    setPreviewMode(false);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    onPhoneReportOpenChange?.(false);
  }

  async function showReportPdf(lang: "ar" | "en") {
    setPdfOpened(true);
    setPreviewing(true);
    try {
      const url = (await onPreviewReport?.(lang)) ?? null;
      setPreviewUrl((prev) => {
        if (prev && prev !== url) URL.revokeObjectURL(prev);
        return url;
      });
    } finally {
      setPreviewing(false);
    }
  }

  return (
    <div className="grid gap-3 lg:gap-4">
      {/* Phone · Work — collapsed page; report opens as a sheet */}
      <div className="space-y-2 lg:hidden">
        <div className="rounded-xl border border-neutral-300 bg-neutral-0 p-3">
          <h2 className="mb-2 text-sm font-bold text-neutral-900">{t("wo_status_box")}</h2>
          {statusBody("phone-assignee-search")}
        </div>

        <div className="overflow-hidden rounded-xl border border-neutral-300 bg-neutral-0">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-start"
            onClick={() => setDetailsOpen((o) => !o)}
            aria-expanded={detailsOpen}
          >
            <span className="min-w-0">
              <span className="block text-sm font-bold text-neutral-900">{t("wo_details")}</span>
              {!detailsOpen && (
                <span className="mt-0.5 block truncate text-xs text-neutral-500">{detailsSummary}</span>
              )}
            </span>
            <span className="text-xs text-neutral-500" aria-hidden>
              {detailsOpen ? "▾" : "▸"}
            </span>
          </button>
          {detailsOpen && (
            <div className="grid grid-cols-2 gap-3 border-t border-neutral-100 px-3 py-3">
              {detailFields.map((f) => (
                <div key={f.label} className={f.wide ? "col-span-2" : ""}>
                  <p className="text-[10px] font-semibold text-neutral-500">{f.label}</p>
                  <div className="mt-0.5 break-words text-sm text-neutral-900">{f.value}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="overflow-hidden rounded-xl border border-amber-200 bg-amber-50">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-start"
            onClick={() => setCodesOpen((o) => !o)}
            aria-expanded={codesOpen}
          >
            <span className="min-w-0">
              <span className="block text-sm font-bold text-neutral-900">
                {t("error_codes") || "Error codes"}
              </span>
              {!codesOpen && (
                <span className="mt-0.5 block truncate text-xs text-amber-900">
                  {codesStrip || t("diagnostic_codes_hint") || "Failure / symptom codes and downtime"}
                </span>
              )}
            </span>
            <span className="text-xs text-amber-900" aria-hidden>
              {codesOpen ? "▾" : "▸"}
            </span>
          </button>
          {codesOpen && (
            <div className="border-t border-amber-200 bg-neutral-0 px-3 py-3">
              <WorkOrderDiagnosticsPanel
                workOrder={wo}
                canEdit={canEditDiagnostics}
                onSaved={onWoSaved}
                embedded
              />
            </div>
          )}
        </div>

      </div>

      {/* Desktop split — unchanged */}
      <div className="hidden gap-3 lg:grid lg:grid-cols-2 lg:gap-4">
        <div className="rounded-xl border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-neutral-800">{t("wo_details")}</h2>
          <dl className="mt-2 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[11px] text-neutral-500">{t("company")}</dt>
              <dd className="truncate text-neutral-900">{wo.company_name || "—"}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-neutral-500">{t("site")}</dt>
              <dd className="truncate text-neutral-900">
                {wo.site_name ? (
                  <Link to={`/sites/${wo.site_id}`} className="text-primary-700 hover:underline">
                    {wo.site_name}
                  </Link>
                ) : (
                  "—"
                )}
              </dd>
            </div>
            {siteAddressLine ? (
              <div className="sm:col-span-2">
                <dt className="text-[11px] text-neutral-500">{t("address")}</dt>
                <dd className="text-neutral-900">{siteAddressLine}</dd>
              </div>
            ) : null}
            {wo.location_name ? (
              <div>
                <dt className="text-[11px] text-neutral-500">{t("location") || "Location"}</dt>
                <dd className="truncate text-neutral-900">{wo.location_name}</dd>
              </div>
            ) : null}
            <div>
              <dt className="text-[11px] text-neutral-500">{t("asset")}</dt>
              <dd className="truncate text-neutral-900">
                {wo.asset_id ? (
                  <Link to={`/assets/${wo.asset_id}`} className="text-primary-700 hover:underline">
                    {wo.asset_name || wo.asset_label_code || wo.asset_id}
                  </Link>
                ) : (
                  "—"
                )}
              </dd>
            </div>
            {wo.asset_category ? (
              <div>
                <dt className="text-[11px] text-neutral-500">{t("asset_category")}</dt>
                <dd className="truncate text-neutral-900">{wo.asset_category}</dd>
              </div>
            ) : null}
            {wo.asset_serial ? (
              <div>
                <dt className="text-[11px] text-neutral-500">{t("asset_serial")}</dt>
                <dd className="font-mono text-neutral-900">{wo.asset_serial}</dd>
              </div>
            ) : null}
            {wo.asset_model ? (
              <div>
                <dt className="text-[11px] text-neutral-500">{t("model") || "Model"}</dt>
                <dd className="truncate text-neutral-900">{wo.asset_model}</dd>
              </div>
            ) : null}
            <div>
              <dt className="text-[11px] text-neutral-500">{t("category") || "Category"}</dt>
              <dd className="capitalize text-neutral-900">{wo.category || "—"}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-neutral-500">{t("source") || "Source"}</dt>
              <dd className="capitalize text-neutral-900">{wo.source || "—"}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-neutral-500">{t("urgency") || "Urgency"}</dt>
              <dd className="capitalize text-neutral-900">{wo.urgency}</dd>
            </div>
            {wo.description ? (
              <div className="sm:col-span-2">
                <dt className="text-[11px] text-neutral-500">{t("description")}</dt>
                <dd className="line-clamp-3 whitespace-pre-wrap text-neutral-900">{wo.description}</dd>
              </div>
            ) : null}
          </dl>
        </div>

        <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-neutral-800">{t("wo_status_box")}</h2>
          {statusBody("status-assignee-search")}
        </div>
      </div>

      <div className="hidden gap-3 lg:grid lg:grid-cols-2 lg:gap-4 lg:items-start">
        <div className="overflow-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm [&_form]:border-0 [&_form]:shadow-none">
          <WorkOrderDiagnosticsPanel
            workOrder={wo}
            canEdit={canEditDiagnostics}
            onSaved={onWoSaved}
          />
        </div>

        <div
          id="wo-report-box"
          className="scroll-mt-20 rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm"
        >
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-neutral-100 pb-3">
            <h2 className="text-sm font-semibold text-neutral-800">{t("wo_reports_box")}</h2>
            <p className="text-sm text-neutral-600">
              {t("status")}:{" "}
              <strong className="text-neutral-900">
                {report?.status
                  ? t(report.status) !== report.status
                    ? t(report.status)
                    : report.status
                  : t("not_started") || "—"}
              </strong>
            </p>
          </div>
          {reportPanel}
          <div className="mt-4 space-y-2 border-t border-neutral-100 pt-3">
            <label className="block text-xs font-medium text-neutral-600" htmlFor="job-inspector-note">
              {t("inspector_note")}
            </label>
            <textarea
              id="job-inspector-note"
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              rows={2}
              value={inspectorNote}
              onChange={(e) => onInspectorNoteChange(e.target.value)}
            />
            <button
              type="button"
              disabled={savingNote || !inspectorNote.trim()}
              className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-50 disabled:opacity-50"
              onClick={onSaveInspectorNote}
            >
              {savingNote ? t("loading") : t("add_inspector_note")}
            </button>
          </div>
        </div>
      </div>

      {phoneReportOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center lg:items-center">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label={t("close") || "Close"}
            onClick={closeReportSheet}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="wo-phone-report-title"
            className="relative flex max-h-[92vh] w-full flex-col rounded-t-2xl border border-neutral-200 bg-neutral-0 shadow-xl lg:max-w-3xl lg:rounded-2xl"
          >
            <div className="flex items-center justify-between gap-2 border-b border-neutral-100 px-4 py-3">
              <h2 id="wo-phone-report-title" className="text-base font-semibold text-neutral-900">
                {t("report") || "Report"}
              </h2>
              <button
                type="button"
                className="min-h-9 rounded-lg px-2 text-sm font-semibold text-neutral-600"
                onClick={closeReportSheet}
              >
                {t("close") || "Close"}
              </button>
            </div>
            <div className="overflow-y-auto px-4 py-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
              {reportReady || previewMode ? (
                <div className="space-y-3">
                  <p className="text-sm text-neutral-600">{t("wo_confirm_hint")}</p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={previewing}
                      className="min-h-11 flex-1 rounded-xl border border-neutral-300 text-sm font-bold text-neutral-900 disabled:opacity-50"
                      onClick={() => void showReportPdf("ar")}
                    >
                      {t("wo_open_report_ar")}
                    </button>
                    <button
                      type="button"
                      disabled={previewing}
                      className="min-h-11 flex-1 rounded-xl border border-neutral-300 text-sm font-bold text-neutral-900 disabled:opacity-50"
                      onClick={() => void showReportPdf("en")}
                    >
                      {t("wo_open_report_en")}
                    </button>
                  </div>
                  {previewing && (
                    <p className="text-center text-sm text-neutral-500">{t("loading")}</p>
                  )}
                  {previewUrl && (
                    <>
                      <iframe
                        title={t("report") || "Report"}
                        src={previewUrl}
                        className="h-[65vh] w-full rounded-lg border border-neutral-200 bg-neutral-50"
                      />
                      <a
                        href={previewUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex min-h-11 items-center justify-center rounded-xl bg-primary-700 text-sm font-bold text-white"
                      >
                        {t("wo_open_report_tab")}
                      </a>
                    </>
                  )}
                  {pdfOpened && report?.status === "submitted" && (
                    <button
                      type="button"
                      className="min-h-11 w-full rounded-xl border border-neutral-300 text-sm font-bold text-neutral-900"
                      onClick={() => onEditReport?.()}
                    >
                      {t("edit_report")}
                    </button>
                  )}
                </div>
              ) : (
                <>
                  {!report && (
                    <p className="py-6 text-center text-sm text-neutral-500">
                      {savingReport ? t("loading") : t("wo_start_report_inline") || "Starting report…"}
                    </p>
                  )}
                  {phoneReport}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

