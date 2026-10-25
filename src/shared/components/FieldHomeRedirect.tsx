import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const FIELD_ROLES = new Set(["technician", "site_manager", "manager", "company_engineer"]);

/** Concept D: field roles land on Queue (/work-orders); office roles keep dashboard. */
export function FieldHomeRedirect() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="p-6 text-sm text-neutral-500">…</div>;
  }

  const target = user && FIELD_ROLES.has(user.role) ? "/work-orders" : "/dashboard";
  return <Navigate to={target} replace />;
}
