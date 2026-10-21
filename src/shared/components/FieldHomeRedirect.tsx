import { Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

const FIELD_ROLES = new Set(["technician", "site_manager", "manager", "company_engineer"]);

/** Concept D: field roles land on Queue (/work-orders); office roles keep dashboard. */
export function FieldHomeRedirect() {
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void apiFetch<User>("/users/me")
      .then((u) => {
        if (!cancelled) setTarget(FIELD_ROLES.has(u.role) ? "/work-orders" : "/dashboard");
      })
      .catch(() => {
        if (!cancelled) setTarget("/dashboard");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!target) {
    return <div className="p-6 text-sm text-neutral-500">…</div>;
  }
  return <Navigate to={target} replace />;
}
