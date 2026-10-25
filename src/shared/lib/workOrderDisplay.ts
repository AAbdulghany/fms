import type { WorkOrderStatus } from "./types";
import { statusPillClass, urgencyPillClass } from "@/shared/lib/palette";

/** Corrective maintenance — Asset, or صيانة وقائية — Asset. */
export function displayWorkOrderTitle(
  wo: {
    id?: string;
    title?: string | null;
    source?: string | null;
    asset_name?: string | null;
    asset_label_code?: string | null;
  },
  lang: string
): string {
  const asset = (wo.asset_name || wo.asset_label_code || "").trim();
  const source = wo.source || "";
  const ar = lang.toLowerCase().startsWith("ar");
  let phrase = "";
  if (ar) {
    const kind = source === "preventive" ? "وقائية" : source === "corrective" ? "تصحيحية" : "";
    phrase = kind ? `صيانة ${kind}` : "صيانة";
  } else if (source === "preventive") {
    phrase = "Preventive maintenance";
  } else if (source === "corrective") {
    phrase = "Corrective maintenance";
  } else if (source) {
    phrase = source;
  }
  if (asset && phrase) return `${phrase} — ${asset}`;
  const raw = (wo.title || "").trim();
  return raw || asset || (wo.id || "").slice(0, 8);
}

/** Shared layout for work order status pills — colors come from the Orbit palette. */
export const workOrderStatusPillBase = "orbit-chip";

export function workOrderStatusPillClass(status: string): string {
  return statusPillClass(status as WorkOrderStatus);
}

export const urgencyBadgeBase = "orbit-chip";

export function urgencyBadgeClass(urgency: string): string {
  return urgencyPillClass(urgency);
}
