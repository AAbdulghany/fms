import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../lib/api";

export type CalendarView = "monthly" | "quarterly" | "yearly";

export type MaintenanceCalendarEvent = {
  asset_id: string;
  asset_name: string;
  site_id: string;
  client_id: string;
  schedule_id: string;
  frequency: string;
  due_at: string;
  bucket: string;
  year: number;
  view: string;
};

type Props = {
  clientId?: string;
  selectedAssetId?: string | null;
  onSelectAsset?: (assetId: string) => void;
};

const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];
const MONTHS = Array.from({ length: 12 }, (_, i) => String(i + 1));

const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function MaintenanceCalendar({ clientId, selectedAssetId, onSelectAsset }: Props) {
  const { t } = useTranslation();
  const [view, setView] = useState<CalendarView>("quarterly");
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1); // 1-based
  const [events, setEvents] = useState<MaintenanceCalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ view, year: String(year) });
        if (view === "monthly") params.set("month", String(month));
        if (clientId) params.set("client_id", clientId);
        const data = await apiFetch<MaintenanceCalendarEvent[]>(
          `/assets/maintenance-calendar?${params.toString()}`
        );
        setEvents(data);
      } catch (err) {
        console.error("Failed to load maintenance calendar", err);
        setEvents([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [view, year, month, clientId]);

  const buckets = view === "quarterly" ? QUARTERS : MONTHS;

  const byBucket = useMemo(() => {
    if (view === "monthly") {
      // Monthly view: group by day-of-month (bucket = day number as string)
      const map = new Map<string, MaintenanceCalendarEvent[]>();
      for (const ev of events) {
        const day = String(new Date(ev.due_at).getDate());
        const list = map.get(day) ?? [];
        list.push(ev);
        map.set(day, list);
      }
      return map;
    }
    const map = new Map<string, MaintenanceCalendarEvent[]>();
    for (const b of buckets) map.set(b, []);
    for (const ev of events) {
      const list = map.get(ev.bucket) ?? [];
      list.push(ev);
      map.set(ev.bucket, list);
    }
    return map;
  }, [events, buckets, view]);

  const monthLabel = (m: string) => {
    const d = new Date(Number(year), Number(m) - 1, 1);
    return d.toLocaleString(undefined, { month: "short" });
  };

  // For monthly view: collect days that have events
  const monthlyDays = useMemo(() => {
    if (view !== "monthly") return [];
    const days = Array.from(byBucket.keys()).map(Number).sort((a, b) => a - b);
    return days;
  }, [byBucket, view]);

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm" data-testid="maintenance-calendar">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-neutral-900">
          {t("maintenance_calendar") || "Maintenance calendar"}
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          {/* Monthly toggle */}
          <button
            type="button"
            data-testid="calendar-view-monthly"
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              view === "monthly" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
            onClick={() => setView("monthly")}
          >
            {t("monthly_calendar") || "Monthly"}
          </button>
          <button
            type="button"
            data-testid="calendar-view-quarterly"
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              view === "quarterly" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
            onClick={() => setView("quarterly")}
          >
            {t("quarterly_calendar") || "Quarterly"}
          </button>
          <button
            type="button"
            data-testid="calendar-view-yearly"
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              view === "yearly" ? "bg-primary-600 text-white" : "border border-neutral-300"
            }`}
            onClick={() => setView("yearly")}
          >
            {t("yearly_calendar") || "Yearly"}
          </button>

          {/* Month picker — visible only in monthly view */}
          {view === "monthly" && (
            <select
              className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              aria-label={t("calendar_month_picker") || "Month"}
              data-testid="calendar-month-picker"
            >
              {MONTH_NAMES.map((name, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  {name}
                </option>
              ))}
            </select>
          )}

          {/* Year picker */}
          <select
            className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            aria-label="Year"
          >
            {[year - 1, year, year + 1].map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex min-h-[120px] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
        </div>
      ) : view === "monthly" ? (
        /* Monthly view — list events for the selected month */
        <div data-testid="calendar-grid-monthly">
          {events.length === 0 ? (
            <p className="py-6 text-center text-sm text-neutral-400">
              {t("no_events_this_month") || `No maintenance events in ${MONTH_NAMES[month - 1]} ${year}`}
            </p>
          ) : (
            <div className="space-y-2">
              {monthlyDays.map((day) => {
                const items = byBucket.get(String(day)) ?? [];
                return (
                  <div key={day} className="flex gap-3">
                    <div className="w-8 shrink-0 pt-1 text-right text-xs font-semibold text-neutral-500">
                      {day}
                    </div>
                    <div className="flex-1 space-y-1">
                      {items.map((ev) => (
                        <button
                          key={`${ev.schedule_id}-${ev.due_at}`}
                          type="button"
                          data-testid={`calendar-asset-${ev.asset_id}`}
                          className={`w-full rounded px-2 py-1.5 text-start text-xs transition-colors hover:bg-primary-50 ${
                            selectedAssetId === ev.asset_id
                              ? "bg-primary-100 font-medium text-primary-800"
                              : "border border-neutral-100 bg-neutral-50 text-neutral-800"
                          }`}
                          onClick={() => onSelectAsset?.(ev.asset_id)}
                        >
                          <span className="font-medium">{ev.asset_name}</span>
                          <span className="ms-2 text-neutral-500">{ev.frequency}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div
          className={`grid gap-3 ${view === "quarterly" ? "grid-cols-2 lg:grid-cols-4" : "grid-cols-3 lg:grid-cols-6"}`}
          data-testid={`calendar-grid-${view}`}
        >
          {buckets.map((bucket) => {
            const items = byBucket.get(bucket) ?? [];
            return (
              <div key={bucket} className="rounded-lg border border-neutral-100 bg-neutral-50 p-3">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  {view === "yearly" ? monthLabel(bucket) : bucket}
                </div>
                <ul className="space-y-1">
                  {items.length === 0 ? (
                    <li className="text-xs text-neutral-400">—</li>
                  ) : (
                    items.map((ev) => (
                      <li key={`${ev.schedule_id}-${ev.due_at}`}>
                        <button
                          type="button"
                          data-testid={`calendar-asset-${ev.asset_id}`}
                          className={`w-full rounded px-2 py-1 text-start text-xs transition-colors hover:bg-primary-50 ${
                            selectedAssetId === ev.asset_id
                              ? "bg-primary-100 font-medium text-primary-800"
                              : "text-neutral-800"
                          }`}
                          onClick={() => onSelectAsset?.(ev.asset_id)}
                        >
                          <span className="block truncate">{ev.asset_name}</span>
                          <span className="text-neutral-500">
                            {new Date(ev.due_at).toLocaleDateString()}
                          </span>
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
