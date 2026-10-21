import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { User } from "@/lib/types";
import { hasAnyRole } from "@/lib/roles";
import { hasFeature } from "@/lib/features";

interface MobileBottomNavProps {
  user: User | null;
  onMore: () => void;
}

/** Concept D field shell — Queue / Scan / Time / More (menu contents TBD). */
const FIELD_TABS = [
  {
    path: "/work-orders",
    labelKey: "nav_queue",
    icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
    roles: ["super_admin", "company_admin", "client_admin", "site_manager", "technician", "manager"] as const,
  },
  {
    path: "/assets",
    labelKey: "nav_scan",
    icon: "M3 7V5a2 2 0 012-2h2M17 3h2a2 2 0 012 2v2M21 17v2a2 2 0 01-2 2h-2M7 21H5a2 2 0 01-2-2v-2M7 8h10v8H7V8z",
    roles: ["super_admin", "company_admin", "client_admin", "site_manager", "technician"] as const,
    requiredFeature: "assets",
  },
  {
    path: "/labor",
    labelKey: "nav_time",
    icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
    roles: ["super_admin", "company_admin", "manager", "technician"] as const,
  },
] as const;

export function MobileBottomNav({ user, onMore }: MobileBottomNavProps) {
  const { t } = useTranslation();
  const location = useLocation();

  const tabs = FIELD_TABS.filter((tab) => {
    if (!user || !hasAnyRole(user.role, [...tab.roles])) return false;
    if ("requiredFeature" in tab && tab.requiredFeature && !hasFeature(user, tab.requiredFeature)) {
      return false;
    }
    return true;
  });

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-neutral-200 bg-neutral-0/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-sm lg:hidden"
      aria-label={t("primary_navigation")}
    >
      <ul className="mx-auto flex max-w-lg items-stretch justify-around px-1 pt-1">
        {tabs.map((item) => {
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
                <span className="max-w-[4.5rem] truncate">{t(item.labelKey)}</span>
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
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" />
            </svg>
            <span>{t("nav_more")}</span>
          </button>
        </li>
      </ul>
    </nav>
  );
}
