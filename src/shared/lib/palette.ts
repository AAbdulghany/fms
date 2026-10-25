/**
 * Class names for the Orbit palette (src/styles/palette.css).
 * Colors themselves live in src/styles/tokens.css.
 * Apply a tone to any element: className={`${chip} ${tone.success}`}
 */

export const chip = "orbit-chip";
export const notice = "orbit-notice";

export const tone = {
  success: "orbit-tone-success",
  warning: "orbit-tone-warning",
  error: "orbit-tone-error",
  info: "orbit-tone-info",
  neutral: "orbit-tone-neutral",
  primary: "orbit-tone-primary",
  hold: "orbit-tone-hold",
  verified: "orbit-tone-verified",
} as const;

export type PaletteTone = keyof typeof tone;

const workOrderTone: Record<string, string> = {
  requested: tone.warning,
  declined: tone.error,
  created: tone.neutral,
  assigned: tone.info,
  in_progress: tone.warning,
  on_hold: tone.hold,
  completed: tone.success,
  verified: tone.verified,
  cancelled: tone.error,
  closed: tone.neutral,
};

export function statusPillClass(status: string): string {
  const strike = status === "declined" ? " orbit-chip-strike" : "";
  return `${chip} ${workOrderTone[status] ?? tone.neutral}${strike}`;
}

export function urgencyPillClass(urgency: string): string {
  const mapped = urgency === "emergency" ? tone.error : urgency === "urgent" ? tone.warning : tone.success;
  return `${chip} ${mapped}`;
}

export function invoicePillClass(status: string): string {
  switch (status) {
    case "paid":
      return `${chip} ${tone.success}`;
    case "draft":
      return `${chip} ${tone.neutral}`;
    case "approved":
      return `${chip} ${tone.warning}`;
    case "sent":
      return `${chip} ${tone.info}`;
    case "void":
      return `${chip} ${tone.error}`;
    default:
      return `${chip} ${tone.warning}`;
  }
}

export function activePillClass(active: boolean): string {
  return `${chip} ${active ? tone.success : tone.neutral}`;
}

export function kindPillClass(kind: string): string {
  if (kind === "raw_material") return `${chip} ${tone.success}`;
  if (kind === "spare_asset") return `${chip} ${tone.warning}`;
  return `${chip} ${tone.info}`;
}

export const stat = {
  plain: "orbit-stat orbit-stat-plain",
  open: `orbit-stat ${tone.info}`,
  overdue: `orbit-stat ${tone.error}`,
  inProgress: `orbit-stat ${tone.warning}`,
};

export const button = {
  base: "orbit-btn",
  primary: "orbit-btn orbit-btn-primary",
  ghost: "orbit-btn orbit-btn-ghost",
};
