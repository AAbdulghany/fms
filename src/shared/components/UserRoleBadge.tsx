import { UserRole } from "@/lib/types";
import { useTranslation } from "react-i18next";

interface UserRoleBadgeProps {
  role: UserRole;
}

export function UserRoleBadge({ role }: UserRoleBadgeProps) {
  const { t } = useTranslation();

  return (
    <span className={`orbit-chip orbit-role-${role}`}>
      {t(`role_${role}`)}
    </span>
  );
}
