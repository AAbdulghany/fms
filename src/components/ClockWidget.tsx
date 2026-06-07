import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";

const HIJRI_KEY = "fms_clock_use_hijri";

/** Shows server-aligned time in the header (Phase 3). Optional Islamic (Hijri) calendar. */
export default function ClockWidget() {
  const { t, i18n } = useTranslation();
  const [now, setNow] = useState(() => new Date());
  const [offsetMs, setOffsetMs] = useState(0);
  const [useHijri, setUseHijri] = useState(() => localStorage.getItem(HIJRI_KEY) === "1");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const { utc } = await apiFetch<{ utc: string }>("/server-time");
        const server = new Date(utc).getTime();
        const local = Date.now();
        if (!cancelled) setOffsetMs(server - local);
      } catch {
        if (!cancelled) setOffsetMs(0);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const tick = () => setNow(new Date(Date.now() + offsetMs));
    tick();
    const id = setInterval(tick, 60_000);
    return () => clearInterval(id);
  }, [offsetMs]);

  const toggleHijri = useCallback(() => {
    setUseHijri((prev) => {
      const next = !prev;
      localStorage.setItem(HIJRI_KEY, next ? "1" : "0");
      return next;
    });
  }, []);

  const format = (d: Date) => {
    const locale = i18n.language === "ar" ? "ar-SA" : "en-US";
    const base: Intl.DateTimeFormatOptions = {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    try {
      if (useHijri) {
        return new Intl.DateTimeFormat(locale, { ...base, calendar: "islamic" }).format(d);
      }
      return new Intl.DateTimeFormat(locale, base).format(d);
    } catch {
      return new Intl.DateTimeFormat(locale, base).format(d);
    }
  };

  const label = useHijri ? t("clock_hijri_short") : t("clock_gregorian_short");

  return (
    <div className="hidden items-center gap-2 text-xs text-neutral-600 sm:flex md:text-sm">
      <button
        type="button"
        onClick={toggleHijri}
        className="rounded border border-neutral-200 bg-neutral-50 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-neutral-600 hover:bg-neutral-100 md:text-xs"
        title={t("clock_toggle_calendar")}
        aria-pressed={useHijri}
      >
        {label}
      </button>
      <div className="flex items-center gap-2" title={format(now)}>
        <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <time dateTime={now.toISOString()}>{format(now)}</time>
      </div>
    </div>
  );
}
