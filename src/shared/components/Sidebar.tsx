import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { User, UserRole } from "@/lib/types";
import { hasAnyRole, isPlatformStaff } from "@/lib/roles";
import { hasFeature } from "@/lib/features";
import { OrbitLogo } from "@/components/OrbitLogo";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  path: string;
  labelKey: string;
  icon: string;
  allowedRoles: UserRole[];
  platformAdminOnly?: boolean;
  requiredFeature?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: "/dashboard",
    labelKey: "dashboard",
    icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
    allowedRoles: ["super_admin", "company_admin", "client_admin", "site_manager", "technician"],
  },
  {
    path: "/companies",
    labelKey: "companies",
    icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
    allowedRoles: ["super_admin", "company_admin"],
  },
  {
    path: "/assets",
    labelKey: "assets",
    icon: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
    allowedRoles: ["super_admin", "company_admin", "client_admin", "site_manager"],
    requiredFeature: "assets",
  },
  {
    path: "/work-orders",
    labelKey: "work_orders",
    icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
    allowedRoles: ["super_admin", "company_admin", "client_admin", "site_manager", "technician"],
  },
  {
    path: "/invoices",
    labelKey: "invoices",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    allowedRoles: ["super_admin", "company_admin", "client_admin"],
    requiredFeature: "invoices",
  },
  {
    path: "/users",
    labelKey: "users",
    icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
    allowedRoles: ["super_admin", "company_admin"],
  },
  {
    path: "/labor",
    labelKey: "labor",
    icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
    allowedRoles: ["super_admin", "company_admin", "manager", "technician"],
  },
  {
    path: "/platform/maintenance-companies",
    labelKey: "maintenance_companies",
    icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
    allowedRoles: ["super_user", "sw_dev", "super_admin"],
    platformAdminOnly: true,
  },
  {
    path: "/platform/packages",
    labelKey: "platform_packages",
    icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
    allowedRoles: ["super_user", "sw_dev", "super_admin"],
    platformAdminOnly: true,
  },
  {
    path: "/subscription",
    labelKey: "subscription",
    icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z",
    allowedRoles: ["super_user", "sw_dev", "super_admin"],
    platformAdminOnly: true,
  },
  {
    path: "/locations",
    labelKey: "locations",
    icon: "M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z",
    allowedRoles: ["super_admin", "company_admin", "client_admin"],
  },
  {
    path: "/report-templates",
    labelKey: "report_templates",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    allowedRoles: ["super_admin", "company_admin"],
  },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const isRTL = i18n.dir() === "rtl";

  useEffect(() => {
    async function fetchUser() {
      try {
        const data = await apiFetch<User>("/users/me");
        setUser(data);
      } catch (error) {
        console.error("Failed to fetch user", error);
      } finally {
        setLoading(false);
      }
    }
    void fetchUser();
  }, []);

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (!user || !hasAnyRole(user.role, item.allowedRoles)) return false;
    if (item.platformAdminOnly && !isPlatformStaff(user)) return false;
    if (item.requiredFeature && !hasFeature(user, item.requiredFeature)) return false;
    return true;
  }).sort((a, b) => {
    if (!user || !isPlatformStaff(user)) return 0;
    if (a.platformAdminOnly && !b.platformAdminOnly) return -1;
    if (!a.platformAdminOnly && b.platformAdminOnly) return 1;
    return 0;
  });

  const isActive = (path: string) => {
    if (path === "/dashboard") {
      return location.pathname === "/" || location.pathname === "/dashboard";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <>
      <aside
        className={`max-lg:fixed ${isRTL ? "max-lg:right-0 max-lg:left-auto" : "max-lg:left-0"} max-lg:top-14 max-lg:bottom-0 max-lg:z-30 w-64 shrink-0 transform ${isRTL ? "border-l" : "border-r"} border-neutral-200 bg-neutral-0 shadow-lg transition-transform duration-300 lg:relative lg:top-auto lg:z-auto lg:flex lg:h-full lg:min-h-0 lg:flex-col lg:translate-x-0 lg:self-stretch ${
          isOpen ? "translate-x-0" : isRTL ? "translate-x-full" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full min-h-0 w-full flex-col">
          <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-4 lg:hidden">
            <OrbitLogo iconSize={24} />
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-2 text-neutral-600 hover:bg-neutral-100"
              aria-label={t("close_menu")}
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="flex flex-1 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
          ) : (
            <nav className="flex-1 overflow-y-auto px-2 py-4">
              <ul className="space-y-1">
                {visibleItems.map((item) => (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={onClose}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                        isActive(item.path)
                          ? "bg-primary-50 text-primary-700"
                          : "text-neutral-700 hover:bg-neutral-100"
                      }`}
                    >
                      <svg
                        className="h-5 w-5 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={2}
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                      </svg>
                      <span>{t(item.labelKey)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          )}

          {user && (
            <div className="border-t border-neutral-200 px-4 py-3">
              <Link
                to="/profile"
                onClick={onClose}
                className="mb-2 block truncate text-sm font-medium text-primary-600 hover:underline"
              >
                {t("profile")}
              </Link>
              <div className="text-xs text-neutral-500">{t("logged_in_as")}</div>
              <div className="mt-1 truncate text-sm font-medium text-neutral-900">
                {user.full_name}
              </div>
              <div className="truncate text-xs text-neutral-500">{user.email}</div>
              <div className="mt-1 inline-block rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700">
                {t(`role_${user.role}`)}
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
