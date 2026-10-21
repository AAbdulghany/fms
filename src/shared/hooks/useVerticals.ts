/**
 * A1 — Load the platform vertical catalog (GET /verticals).
 */
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Vertical } from "@/lib/types";

export function verticalName(v: { name_en: string; name_ar: string }, lang: string): string {
  return lang.startsWith("ar") ? v.name_ar : v.name_en;
}

export function useVerticals(enabled = true) {
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    setLoading(true);
    setError(false);
    void apiFetch<Vertical[]>("/verticals")
      .then((data) => {
        if (!cancelled) setVerticals(data);
      })
      .catch(() => {
        if (!cancelled) {
          setVerticals([]);
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return { verticals, loading, error };
}
