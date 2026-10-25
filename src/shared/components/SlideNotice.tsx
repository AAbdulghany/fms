import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";

import { notice, tone } from "@/shared/lib/palette";

type NoticeTone = "success" | "error";

/**
 * The work-order event chip: small, end-aligned, slides in.
 * Success hides after a few seconds. Errors stay until cleared.
 */
export function SlideNotice({
  text,
  tone: noticeTone = "success",
  offset = 0,
}: {
  text?: string | null;
  tone?: NoticeTone;
  offset?: number;
}) {
  const { i18n } = useTranslation();
  const [shown, setShown] = useState<string | null>(text ?? null);

  useEffect(() => {
    setShown(text ?? null);
    if (!text || noticeTone === "error") return;
    const id = window.setTimeout(() => setShown(null), 5000);
    return () => window.clearTimeout(id);
  }, [text, noticeTone]);

  if (!shown) return null;

  return createPortal(
    <div
      role={noticeTone === "error" ? "alert" : "status"}
      dir={i18n.dir()}
      className={`notice-slide pointer-events-none fixed z-[70] end-3 ${notice} ${
        noticeTone === "error" ? tone.error : tone.success
      }`}
      style={{ top: `calc(3.75rem + ${offset} * 1.75rem)` }}
    >
      {shown}
    </div>,
    document.body,
  );
}

export function SlideNotices({
  success,
  error,
}: {
  success?: string | null;
  error?: string | null;
}) {
  return (
    <>
      <SlideNotice text={success} />
      <SlideNotice text={error} tone="error" offset={success ? 1 : 0} />
    </>
  );
}
