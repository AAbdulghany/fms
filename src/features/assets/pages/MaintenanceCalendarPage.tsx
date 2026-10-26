/**
 * Maintenance calendar — Google/Apple style:
 * Year (12 months) → Month (day grid) → Week / Day (task list).
 * Route: /assets/maintenance-calendar
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { hasAnyRole } from "@/lib/roles";
import { AssetWorkOrderPanel } from "@/features/assets/components/AssetWorkOrderPanel";
import type { MaintenanceCalendarEvent } from "@/features/assets/components/MaintenanceCalendar";

type Level = "year" | "month" | "week" | "day";

type CalendarWo = {
  id: string;
  title: string;
  asset_id?: string | null;
  asset_name?: string | null;
  status: string;
  source?: string;
  due_at?: string | null;
  opened_at?: string;
};

type CalendarChip = {
  key: string;
  label: string;
  workOrderId?: string;
  finished?: boolean;
};

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const FINISHED_WO = new Set(["completed", "verified", "closed"]);
const HIDDEN_WO = new Set(["cancelled", "declined"]);

function startOfWeek(d: Date): Date {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  x.setDate(x.getDate() - x.getDay());
  return x;
}

function daysInMonth(year: number, month1: number): number {
  return new Date(year, month1, 0).getDate();
}

function eventDate(ev: MaintenanceCalendarEvent): Date {
  return new Date(ev.due_at);
}

function woDate(w: CalendarWo): Date | null {
  const raw = w.due_at || w.opened_at;
  if (!raw) return null;
  return new Date(raw);
}

function isFinishedWo(status: string): boolean {
  return FINISHED_WO.has(status);
}

function chipClass(finished?: boolean): string {
  return finished
    ? "truncate rounded bg-success-light px-1.5 py-0.5 text-[11px] font-medium text-success-dark hover:underline"
    : "truncate rounded bg-primary-100 px-1.5 py-0.5 text-[11px] font-medium text-primary-900 hover:underline";
}

function chipClassDense(finished?: boolean): string {
  return finished
    ? "truncate rounded bg-success-light px-1 text-[10px] font-medium text-success-dark hover:underline"
    : "truncate rounded bg-primary-100 px-1 text-[10px] font-medium text-primary-900 hover:underline";
}

export default function MaintenanceCalendarPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const now = new Date();
  const [level, setLevel] = useState<Level>("year");
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [focusDay, setFocusDay] = useState(now.getDate());
  const [events, setEvents] = useState<MaintenanceCalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [clients, setClients] = useState<{ id: string; legal_name: string }[]>([]);
  const [clientFilter, setClientFilter] = useState("");
  /** Preventive WOs for the year — open + finished (linked/green); exclude cancelled/declined. */
  const [calendarWos, setCalendarWos] = useState<CalendarWo[]>([]);

  useEffect(() => {
    if (!user || !hasAnyRole(user.role, ["super_admin", "company_admin"])) {
      setClients([]);
      return;
    }
    void (async () => {
      try {
        setClients(await apiFetch<{ id: string; legal_name: string }[]>("/clients"));
      } catch (err) {
        console.error("Failed to load clients", err);
      }
    })();
  }, [user]);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ view: "yearly", year: String(year) });
        if (clientFilter) params.set("client_id", clientFilter);
        const [data, woPage] = await Promise.all([
          apiFetch<MaintenanceCalendarEvent[]>(`/assets/maintenance-calendar?${params.toString()}`),
          apiFetch<{ data: CalendarWo[] }>("/work-orders?page_size=100").catch(() => ({
            data: [] as CalendarWo[],
          })),
        ]);
        // One projected event per asset per month (calendar display dedupe)
        const seen = new Set<string>();
        const deduped: MaintenanceCalendarEvent[] = [];
        for (const ev of data) {
          const key = `${ev.asset_id}-${eventDate(ev).getFullYear()}-${eventDate(ev).getMonth()}`;
          if (seen.has(key)) continue;
          seen.add(key);
          deduped.push(ev);
        }
        setEvents(deduped);
        // Keep open + finished preventive WOs whose due/opened date falls in this year.
        setCalendarWos(
          (woPage.data || []).filter((w) => {
            if (w.source !== "preventive" || HIDDEN_WO.has(w.status)) return false;
            const d = woDate(w);
            return d != null && d.getFullYear() === year;
          })
        );
      } catch (err) {
        console.error("Failed to load maintenance calendar", err);
        setEvents([]);
        setCalendarWos([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [year, clientFilter]);

  function shiftMonth(delta: number) {
    let m = month + delta;
    let y = year;
    while (m < 1) {
      m += 12;
      y -= 1;
    }
    while (m > 12) {
      m -= 12;
      y += 1;
    }
    setYear(y);
    setMonth(m);
    const dim = daysInMonth(y, m);
    setFocusDay((d) => Math.min(d, dim));
  }

  const showClientFilter = user && hasAnyRole(user.role, ["super_admin", "company_admin"]);

  const countsByMonth = useMemo(() => {
    const map = new Array(12).fill(0);
    for (const ev of events) {
      const m = eventDate(ev).getMonth();
      map[m] += 1;
    }
    return map;
  }, [events]);

  /** monthIdx 0–11 → events (built once; YearGrid/MonthGrid look up instead of scanning). */
  const eventsByMonth = useMemo(() => {
    const map = new Map<number, MaintenanceCalendarEvent[]>();
    for (const ev of events) {
      const m = eventDate(ev).getMonth();
      const bucket = map.get(m);
      if (bucket) bucket.push(ev);
      else map.set(m, [ev]);
    }
    return map;
  }, [events]);

  /** `${y}-${m0}-${d}` → events for day cells. */
  const eventsByDayKey = useMemo(() => {
    const map = new Map<string, MaintenanceCalendarEvent[]>();
    for (const ev of events) {
      const d = eventDate(ev);
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      const bucket = map.get(key);
      if (bucket) bucket.push(ev);
      else map.set(key, [ev]);
    }
    return map;
  }, [events]);

  const wosByMonth = useMemo(() => {
    const map = new Map<number, CalendarWo[]>();
    for (const w of calendarWos) {
      const d = woDate(w);
      if (!d || d.getFullYear() !== year) continue;
      const m = d.getMonth();
      const bucket = map.get(m);
      if (bucket) bucket.push(w);
      else map.set(m, [w]);
    }
    return map;
  }, [calendarWos, year]);

  const wosByDayKey = useMemo(() => {
    const map = new Map<string, CalendarWo[]>();
    for (const w of calendarWos) {
      const d = woDate(w);
      if (!d) continue;
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      const bucket = map.get(key);
      if (bucket) bucket.push(w);
      else map.set(key, [w]);
    }
    return map;
  }, [calendarWos]);

  const focusDate = useMemo(
    () => new Date(year, month - 1, focusDay),
    [year, month, focusDay]
  );

  const weekStart = useMemo(() => startOfWeek(focusDate), [focusDate]);

  const weekEvents = useMemo(() => {
    const end = new Date(weekStart);
    end.setDate(end.getDate() + 7);
    const out: MaintenanceCalendarEvent[] = [];
    for (const ev of events) {
      const d = eventDate(ev);
      if (d >= weekStart && d < end) out.push(ev);
    }
    return out;
  }, [events, weekStart]);

  const weekWos = useMemo(() => {
    const end = new Date(weekStart);
    end.setDate(end.getDate() + 7);
    const out: CalendarWo[] = [];
    for (const w of calendarWos) {
      const d = woDate(w);
      if (d && d >= weekStart && d < end) out.push(w);
    }
    return out;
  }, [calendarWos, weekStart]);

  const dayEvents = useMemo(
    () => eventsByDayKey.get(`${year}-${month - 1}-${focusDay}`) ?? [],
    [eventsByDayKey, year, month, focusDay]
  );

  const dayWos = useMemo(
    () => wosByDayKey.get(`${year}-${month - 1}-${focusDay}`) ?? [],
    [wosByDayKey, year, month, focusDay]
  );

  function openMonth(m: number) {
    setMonth(m);
    setLevel("month");
    setSelectedAssetId(null);
  }

  function openDay(y: number, m: number, d: number) {
    setYear(y);
    setMonth(m);
    setFocusDay(d);
    setLevel("day");
  }

  function openWeek(y: number, m: number, d: number) {
    setYear(y);
    setMonth(m);
    setFocusDay(d);
    setLevel("week");
  }

  const breadcrumb = (
    <nav className="flex flex-wrap items-center gap-1 text-sm text-neutral-600" aria-label="Calendar breadcrumb">
      <button
        type="button"
        className={`rounded px-2 py-1 hover:bg-neutral-100 ${level === "year" ? "font-semibold text-primary-700" : ""}`}
        onClick={() => setLevel("year")}
      >
        {year}
      </button>
      {level !== "year" && (
        <>
          <span>/</span>
          <button
            type="button"
            className={`rounded px-2 py-1 hover:bg-neutral-100 ${level === "month" ? "font-semibold text-primary-700" : ""}`}
            onClick={() => setLevel("month")}
          >
            {MONTH_NAMES[month - 1]}
          </button>
        </>
      )}
      {(level === "week" || level === "day") && (
        <>
          <span>/</span>
          <span className="px-2 py-1 font-semibold text-primary-700">
            {level === "week"
              ? `${t("calendar_week") || "Week"} of ${weekStart.toLocaleDateString()}`
              : focusDate.toLocaleDateString()}
          </span>
        </>
      )}
    </nav>
  );

  return (
    <div className="space-y-4" data-testid="maintenance-calendar-page">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("maintenance_calendar") || "Maintenance calendar"}
          </h1>
          <p className="mt-1 text-sm text-neutral-600">
            {t("maintenance_calendar_help") ||
              "Year → month → week/day. Click a month or day to drill into scheduled maintenance."}
          </p>
        </div>
        <Link
          to="/assets"
          className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-50"
        >
          ← {t("assets")}
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {breadcrumb}
        <div className="ms-auto flex flex-wrap items-center gap-2">
          {showClientFilter && clients.length > 0 && (
            <select
              data-testid="calendar-client-filter"
              className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm"
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
            >
              <option value="">{t("all_clients") || "All clients"}</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.legal_name}
                </option>
              ))}
            </select>
          )}
          {level === "year" ? (
            <>
              <button
                type="button"
                className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
                onClick={() => setYear((y) => y - 1)}
                aria-label="Previous year"
              >
                ‹
              </button>
              <select
                className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
              >
                {[year - 1, year, year + 1].map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
                onClick={() => setYear((y) => y + 1)}
                aria-label="Next year"
              >
                ›
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                data-testid="calendar-prev-month"
                className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
                onClick={() => shiftMonth(-1)}
                aria-label="Previous month"
              >
                ‹
              </button>
              <span className="min-w-[8rem] text-center text-sm font-medium text-neutral-800">
                {MONTH_NAMES[month - 1]} {year}
              </span>
              <button
                type="button"
                data-testid="calendar-next-month"
                className="rounded-lg border border-neutral-300 px-2 py-1.5 text-sm"
                onClick={() => shiftMonth(1)}
                aria-label="Next month"
              >
                ›
              </button>
              <div className="flex gap-1 rounded-lg border border-neutral-200 p-0.5">
                {(["month", "week", "day"] as Level[]).map((lv) => (
                  <button
                    key={lv}
                    type="button"
                    data-testid={`calendar-level-${lv}`}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium ${
                      level === lv ? "bg-primary-600 text-white" : "text-neutral-700 hover:bg-neutral-50"
                    }`}
                    onClick={() => setLevel(lv)}
                  >
                    {lv === "month"
                      ? t("monthly_calendar") || "Month"
                      : lv === "week"
                        ? t("calendar_week") || "Week"
                        : t("calendar_day") || "Day"}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className={`grid gap-4 ${level === "year" ? "" : "lg:grid-cols-[1fr_280px]"}`}>
        <section className="rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm">
          {loading ? (
            <div className="flex min-h-[240px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : level === "year" ? (
            <YearGrid
              year={year}
              counts={countsByMonth}
              wosByMonth={wosByMonth}
              eventsByMonth={eventsByMonth}
              currentMonth={now.getFullYear() === year ? now.getMonth() + 1 : null}
              onOpenMonth={openMonth}
            />
          ) : level === "month" ? (
            <MonthGrid
              year={year}
              month={month}
              eventsByDayKey={eventsByDayKey}
              wosByDayKey={wosByDayKey}
              today={now}
              onDayClick={(d) => openDay(year, month, d)}
              onWeekClick={(d) => openWeek(year, month, d)}
            />
          ) : (
            <TaskList
              title={
                level === "week"
                  ? `${t("calendar_week") || "Week"} · ${weekStart.toLocaleDateString()} – ${new Date(weekStart.getTime() + 6 * 86400000).toLocaleDateString()}`
                  : focusDate.toLocaleDateString(undefined, {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })
              }
              events={level === "week" ? weekEvents : dayEvents}
              workOrders={level === "week" ? weekWos : dayWos}
              selectedAssetId={selectedAssetId}
              onSelect={setSelectedAssetId}
              emptyLabel={t("no_events_this_month") || "No scheduled maintenance"}
            />
          )}
        </section>

        {level !== "year" && <AssetWorkOrderPanel assetId={selectedAssetId} />}
      </div>
    </div>
  );
}

function YearGrid({
  counts,
  wosByMonth,
  eventsByMonth,
  currentMonth,
  onOpenMonth,
}: {
  year: number;
  counts: number[];
  wosByMonth: Map<number, CalendarWo[]>;
  eventsByMonth: Map<number, MaintenanceCalendarEvent[]>;
  currentMonth: number | null;
  onOpenMonth: (m: number) => void;
}) {
  function previewsForMonth(monthIdx: number): CalendarChip[] {
    const fromWo = wosByMonth.get(monthIdx) ?? [];
    const seen = new Set<string>();
    const out: CalendarChip[] = [];
    for (const w of fromWo) {
      const key = w.asset_id || w.id;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({
        key: w.id,
        label: w.asset_name || w.title,
        workOrderId: w.id,
        finished: isFinishedWo(w.status),
      });
    }
    // Schedule announcements only when no WO covers that asset this month
    for (const ev of eventsByMonth.get(monthIdx) ?? []) {
      if (seen.has(ev.asset_id)) continue;
      seen.add(ev.asset_id);
      out.push({ key: ev.asset_id, label: ev.asset_name });
    }
    return out;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" data-testid="calendar-year-grid">
      {MONTH_SHORT.map((label, idx) => {
        const m = idx + 1;
        const isCurrent = currentMonth === m;
        const previews = previewsForMonth(idx);
        return (
          <button
            key={m}
            type="button"
            data-testid={`calendar-month-tile-${m}`}
            onClick={() => onOpenMonth(m)}
            className={`min-h-[140px] rounded-xl border p-3 text-start transition-colors hover:border-primary-400 hover:bg-primary-50/40 ${
              isCurrent
                ? "border-primary-500 bg-primary-50 ring-2 ring-primary-200"
                : "border-neutral-200 bg-neutral-0"
            }`}
          >
            <div className="mb-2 flex items-baseline justify-between">
              <span className={`text-sm font-semibold ${isCurrent ? "text-primary-800" : "text-neutral-900"}`}>
                {label}
              </span>
              <span className="text-xs text-neutral-500">
                {previews.length || counts[idx]} WO
              </span>
            </div>
            {previews.length === 0 ? (
              <p className="text-xs text-neutral-400">—</p>
            ) : (
              <ul className="space-y-1">
                {previews.slice(0, 4).map((p) => (
                  <li key={p.key}>
                    {p.workOrderId ? (
                      <Link
                        to={`/work-orders/${p.workOrderId}`}
                        onClick={(e) => e.stopPropagation()}
                        className={`block ${chipClass(p.finished)}`}
                        title={p.finished ? "Finished work order" : "Open work order"}
                      >
                        {p.label}
                      </Link>
                    ) : (
                      <span className="block truncate rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] text-neutral-600">
                        {p.label}
                      </span>
                    )}
                  </li>
                ))}
                {previews.length > 4 && (
                  <li className="text-[10px] text-neutral-500">+{previews.length - 4}</li>
                )}
              </ul>
            )}
          </button>
        );
      })}
    </div>
  );
}

function MonthGrid({
  year,
  month,
  eventsByDayKey,
  wosByDayKey,
  today,
  onDayClick,
  onWeekClick,
}: {
  year: number;
  month: number;
  eventsByDayKey: Map<string, MaintenanceCalendarEvent[]>;
  wosByDayKey: Map<string, CalendarWo[]>;
  today: Date;
  onDayClick: (day: number) => void;
  onWeekClick: (day: number) => void;
}) {
  const dim = daysInMonth(year, month);
  const firstDow = new Date(year, month - 1, 1).getDay();
  const cells: (number | null)[] = [
    ...Array.from({ length: firstDow }, () => null),
    ...Array.from({ length: dim }, (_, i) => i + 1),
  ];
  while (cells.length % 7 !== 0) cells.push(null);
  const weeks: (number | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  const monthIdx = month - 1;

  function chipsForDay(day: number): CalendarChip[] {
    const key = `${year}-${monthIdx}-${day}`;
    const dayWos = wosByDayKey.get(key) ?? [];
    const dayEvs = eventsByDayKey.get(key) ?? [];
    const seen = new Set<string>();
    const out: CalendarChip[] = [];
    for (const w of dayWos) {
      const assetKey = w.asset_id || w.id;
      if (seen.has(assetKey)) continue;
      seen.add(assetKey);
      out.push({
        key: w.id,
        label: w.asset_name || w.title,
        workOrderId: w.id,
        finished: isFinishedWo(w.status),
      });
    }
    for (const ev of dayEvs) {
      if (seen.has(ev.asset_id)) continue;
      seen.add(ev.asset_id);
      out.push({ key: `${ev.schedule_id}-${ev.due_at}`, label: ev.asset_name });
    }
    return out;
  }

  return (
    <div data-testid="calendar-month-grid">
      <div className="mb-2 grid grid-cols-[40px_repeat(7,1fr)] gap-1 text-center text-xs font-medium text-neutral-500">
        <div />
        {DOW.map((d) => (
          <div key={d}>{d}</div>
        ))}
      </div>
      <div className="space-y-1">
        {weeks.map((week, wi) => {
          const firstDay = week.find((d) => d != null) ?? 1;
          return (
            <div key={wi} className="grid grid-cols-[40px_repeat(7,1fr)] gap-1">
              <button
                type="button"
                className="rounded text-[10px] text-neutral-400 hover:bg-neutral-100 hover:text-primary-700"
                title="Open week"
                onClick={() => onWeekClick(firstDay)}
              >
                W{wi + 1}
              </button>
              {week.map((day, di) => {
                if (day == null) return <div key={di} className="min-h-[72px] rounded-lg bg-neutral-50/50" />;
                const chips = chipsForDay(day);
                const isToday =
                  today.getFullYear() === year &&
                  today.getMonth() + 1 === month &&
                  today.getDate() === day;
                return (
                  <button
                    key={di}
                    type="button"
                    data-testid={`calendar-day-cell-${day}`}
                    onClick={() => onDayClick(day)}
                    className={`min-h-[72px] rounded-lg border p-1.5 text-start transition-colors hover:border-primary-400 ${
                      isToday ? "border-primary-500 bg-primary-50" : "border-neutral-100 bg-neutral-0"
                    }`}
                  >
                    <div
                      className={`mb-1 text-xs font-semibold ${
                        isToday ? "text-primary-800" : "text-neutral-700"
                      }`}
                    >
                      {day}
                    </div>
                    <ul className="space-y-0.5">
                      {chips.slice(0, 3).map((chip) => (
                        <li key={chip.key}>
                          {chip.workOrderId ? (
                            <Link
                              to={`/work-orders/${chip.workOrderId}`}
                              onClick={(e) => e.stopPropagation()}
                              className={`block ${chipClassDense(chip.finished)}`}
                              title={chip.finished ? "Finished work order" : "Open work order"}
                            >
                              {chip.label}
                            </Link>
                          ) : (
                            <span className="block truncate rounded bg-neutral-100 px-1 text-[10px] text-neutral-600">
                              {chip.label}
                            </span>
                          )}
                        </li>
                      ))}
                      {chips.length > 3 && (
                        <li className="text-[10px] text-neutral-500">+{chips.length - 3}</li>
                      )}
                    </ul>
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TaskList({
  title,
  events,
  workOrders,
  selectedAssetId,
  onSelect,
  emptyLabel,
}: {
  title: string;
  events: MaintenanceCalendarEvent[];
  workOrders: CalendarWo[];
  selectedAssetId: string | null;
  onSelect: (id: string) => void;
  emptyLabel: string;
}) {
  type Row = {
    key: string;
    assetId: string;
    label: string;
    subtitle: string;
    when: Date;
    workOrderId?: string;
    finished?: boolean;
  };

  const rows: Row[] = [];
  const coveredAssets = new Set<string>();
  for (const w of workOrders) {
    const d = woDate(w);
    if (!d) continue;
    const assetId = w.asset_id || w.id;
    coveredAssets.add(assetId);
    rows.push({
      key: w.id,
      assetId,
      label: w.asset_name || w.title,
      subtitle: isFinishedWo(w.status) ? w.status.replace(/_/g, " ") : "preventive",
      when: d,
      workOrderId: w.id,
      finished: isFinishedWo(w.status),
    });
  }
  for (const ev of events) {
    if (coveredAssets.has(ev.asset_id)) continue;
    rows.push({
      key: `${ev.schedule_id}-${ev.due_at}`,
      assetId: ev.asset_id,
      label: ev.asset_name,
      subtitle: ev.frequency,
      when: eventDate(ev),
    });
  }
  rows.sort((a, b) => a.when.getTime() - b.when.getTime());

  return (
    <div data-testid="calendar-task-list">
      <h2 className="mb-3 text-lg font-semibold text-neutral-900">{title}</h2>
      {rows.length === 0 ? (
        <p className="py-10 text-center text-sm text-neutral-400">{emptyLabel}</p>
      ) : (
        <ul className="divide-y divide-neutral-100">
          {rows.map((row) => (
            <li key={row.key}>
              <div
                className={`flex w-full items-center justify-between gap-3 px-2 py-3 text-sm ${
                  selectedAssetId === row.assetId ? "bg-primary-50" : ""
                }`}
              >
                <button
                  type="button"
                  data-testid={`calendar-asset-${row.assetId}`}
                  className="min-w-0 flex-1 text-start hover:opacity-80"
                  onClick={() => onSelect(row.assetId)}
                >
                  <div className="font-medium text-neutral-900">{row.label}</div>
                  <div className="text-xs text-neutral-500">{row.subtitle}</div>
                </button>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <div className="text-xs text-neutral-600">
                    {row.when.toLocaleString(undefined, {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                  {row.workOrderId ? (
                    <Link
                      to={`/work-orders/${row.workOrderId}`}
                      className={chipClass(row.finished)}
                    >
                      {row.finished ? "Finished WO" : "Open WO"}
                    </Link>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
