import { UserRole } from "../lib/types";
import { useTranslation } from "react-i18next";

interface UserRoleBadgeProps {
  role: UserRole;
}

const ROLE_COLORS: Record<UserRole, string> = {
  super_admin: "bg-purple-100 text-purple-700",
  company_admin: "bg-blue-100 text-blue-700",
  client_admin: "bg-teal-100 text-teal-700",
  site_manager: "bg-green-100 text-green-700",
  technician: "bg-orange-100 text-orange-700",
};

export function UserRoleBadge({ role }: UserRoleBadgeProps) {
  const { t } = useTranslation();
  const colorClass = ROLE_COLORS[role] || "bg-neutral-100 text-neutral-700";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}
    >
      {t(`role_${role}`)}
    </span>
  );
}
