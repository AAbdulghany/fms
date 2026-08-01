import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

interface LaborEntryRow {
  id: string;
  work_order_id: string;
  user_id: string;
  work_date: string;
  hours_regular: string;
  hours_overtime: string;
  notes: string;
}

interface ProfileRow {
  id: string;
  user_id: string;
  hourly_rate_sar: string;
  overtime_multiplier: string;
  is_active: boolean;
}

interface ScheduleRow {
  id: string;
  user_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function LaborPage() {
  const { t } = useTranslation();
  const [me, setMe] = useState<User | null>(null);
  const [entries, setEntries] = useState<LaborEntryRow[]>([]);
  const [profiles, setProfiles] = useState<ProfileRow[]>([]);
  const [schedules, setSchedules] = useState<ScheduleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const isAdmin =
    me?.role === "super_admin" || me?.role === "company_admin" || me?.role === "manager";

  useEffect(() => {
    void (async () => {
      try {
        const u = await apiFetch<User>("/users/me");
        setMe(u);
        const [e, p, s] = await Promise.all([
          apiFetch<LaborEntryRow[]>("/labor/entries"),
          apiFetch<ProfileRow[]>("/labor/profiles").catch(() => []),
          apiFetch<ScheduleRow[]>("/labor/schedules").catch(() => []),
        ]);
        setEntries(e);
        setProfiles(p);
        setSchedules(s);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[240px] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-neutral-900">{t("labor")}</h1>
      {err && <p className="text-sm text-error-main">{err}</p>}

      {isAdmin && profiles.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-neutral-900">{t("technician_profiles")}</h2>
          <div className="overflow-x-auto rounded-lg border border-neutral-200">
            <table className="min-w-full text-start text-sm">
              <thead className="bg-neutral-100">
                <tr>
                  <th className="px-4 py-2">{t("user")}</th>
                  <th className="px-4 py-2">{t("hourly_rate")}</th>
                  <th className="px-4 py-2">{t("overtime_multiplier")}</th>
                </tr>
              </thead>
              <tbody>
                {profiles.map((p) => (
                  <tr key={p.id} className="border-t border-neutral-200">
                    <td className="px-4 py-2 font-mono text-xs">{p.user_id.slice(0, 8)}…</td>
                    <td className="px-4 py-2">{p.hourly_rate_sar}</td>
                    <td className="px-4 py-2">{p.overtime_multiplier}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold text-neutral-900">{t("labor_entries")}</h2>
        {entries.length === 0 ? (
          <p className="text-sm text-neutral-600">{t("no_labor_entries")}</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-neutral-200">
            <table className="min-w-full text-start text-sm">
              <thead className="bg-neutral-100">
                <tr>
                  <th className="px-4 py-2">{t("work_order")}</th>
                  <th className="px-4 py-2">{t("date")}</th>
                  <th className="px-4 py-2">{t("hours")}</th>
                  <th className="px-4 py-2">{t("overtime")}</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((r) => (
                  <tr key={r.id} className="border-t border-neutral-200">
                    <td className="px-4 py-2 font-mono text-xs">{r.work_order_id.slice(0, 8)}…</td>
                    <td className="px-4 py-2">{r.work_date}</td>
                    <td className="px-4 py-2">{r.hours_regular}</td>
                    <td className="px-4 py-2">{r.hours_overtime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {schedules.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-neutral-900">{t("schedule")}</h2>
          <div className="overflow-x-auto rounded-lg border border-neutral-200">
            <table className="min-w-full text-start text-sm">
              <thead className="bg-neutral-100">
                <tr>
                  <th className="px-4 py-2">{t("day")}</th>
                  <th className="px-4 py-2">{t("start")}</th>
                  <th className="px-4 py-2">{t("end")}</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((r) => (
                  <tr key={r.id} className="border-t border-neutral-200">
                    <td className="px-4 py-2">{DAYS[r.day_of_week] ?? r.day_of_week}</td>
                    <td className="px-4 py-2">{r.start_time}</td>
                    <td className="px-4 py-2">{r.end_time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
