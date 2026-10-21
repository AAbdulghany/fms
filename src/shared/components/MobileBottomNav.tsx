import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { User } from "@/lib/types";
import { hasAnyRole, isPlatformStaff } from "@/lib/roles";
import { hasFeature } from "@/lib/features";
import { NAV_ITEMS } from "@/shared/navigation/navItems";

interface MobileBottomNavProps {
  user: User | null;
  onMore: () => void;
}

const MORE_ICON =
  "M4 6h16M4 12h16M4 18h7";

export function MobileBottomNav({ user, onMore }: MobileBottomNavProps) {
  const { t } = useTranslation();
  const location = useLocation();

  const primary = NAV_ITEMS.filter((item) => {
    if (!item.mobilePrimary) return false;
    if (!user || !hasAnyRole(user.role, item.allowedRoles)) return false;
    if (item.platformAdminOnly && !isPlatformStaff(user)) return false;
    if (item.requiredFeature && !hasFeature(user, item.requiredFeature)) return false;
    return true;
  }).slice(0, 3);

  const isActive = (path: string) => {
    if (path === "/dashboard") {
      return location.pathname === "/" || location.pathname === "/dashboard";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-neutral-200 bg-neutral-0 pb-[env(safe-area-inset-bottom)] lg:hidden"
      aria-label={t("primary_navigation")}
    >
      <ul className="mx-auto flex max-w-lg items-stretch justify-around px-1 pt-1">
        {primary.map((item) => {
          const active = isActive(item.path);
          return (
            <li key={item.path} className="flex-1">
              <Link
                to={item.path}
                className={`flex min-h-12 flex-col items-center justify-center gap-0.5 px-1 py-1 text-[11px] font-medium ${
                  active ? "text-primary-700" : "text-neutral-600"
                }`}
                aria-current={active ? "page" : undefined}
              >
                <svg
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                </svg>
                <span className="truncate max-w-[4.5rem]">{t(item.labelKey)}</span>
              </Link>
            </li>
          );
        })}
        <li className="flex-1">
          <button
            type="button"
            onClick={onMore}
            className="flex min-h-12 w-full flex-col items-center justify-center gap-0.5 px-1 py-1 text-[11px] font-medium text-neutral-600"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d={MORE_ICON} />
            </svg>
            <span>{t("nav_more")}</span>
          </button>
        </li>
      </ul>
    </nav>
  );
}
