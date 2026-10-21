import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";
import { hasAnyRole, isPlatformStaff } from "@/lib/roles";
import { hasFeature } from "@/lib/features";
import { OrbitLogo } from "@/shared/components/OrbitLogo";
import { NAV_ITEMS } from "@/shared/navigation/navItems";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

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
