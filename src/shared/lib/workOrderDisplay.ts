import type { WorkOrderStatus } from "./types";

/** Shared layout for work order status pills (design palette). */
export const workOrderStatusPillBase =
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap";

/** Work order lifecycle status — same pill shape as before (`rounded-full`); palette = bg/text only. */
export function workOrderStatusPillClass(status: string): string {
  const s = status as WorkOrderStatus;
  switch (s) {
    case "requested":
      return `${workOrderStatusPillBase} bg-orange-100 text-orange-900`;
    case "declined":
      return `${workOrderStatusPillBase} bg-red-50 text-red-700 line-through`;
    case "created":
      return `${workOrderStatusPillBase} bg-slate-200 text-slate-800`;
    case "assigned":
      return `${workOrderStatusPillBase} bg-blue-100 text-blue-800`;
    case "in_progress":
      return `${workOrderStatusPillBase} bg-amber-100 text-amber-900`;
    case "on_hold":
      return `${workOrderStatusPillBase} bg-violet-100 text-violet-800`;
    case "completed":
      return `${workOrderStatusPillBase} bg-emerald-100 text-emerald-900`;
    case "verified":
      return `${workOrderStatusPillBase} bg-emerald-800 text-emerald-50`;
    case "cancelled":
      return `${workOrderStatusPillBase} bg-red-100 text-red-800`;
    case "closed":
      return `${workOrderStatusPillBase} bg-neutral-200 text-neutral-800`;
    default:
      return `${workOrderStatusPillBase} bg-neutral-100 text-neutral-700`;
  }
}

/** Urgency — same pill shape as tables used before (`rounded-full`, no border); semantic light/dark fills. */
export const urgencyBadgeBase =
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap";

export function urgencyBadgeClass(urgency: string): string {
  switch (urgency) {
    case "emergency":
      return `${urgencyBadgeBase} bg-error-light text-error-dark`;
    case "urgent":
      return `${urgencyBadgeBase} bg-warning-light text-warning-dark`;
    case "normal":
    default:
      return `${urgencyBadgeBase} bg-success-light text-success-dark`;
  }
}
