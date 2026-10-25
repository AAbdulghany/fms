import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";
import { hasAnyRole, isPlatformStaff } from "@/lib/roles";
import { hasFeature } from "@/lib/features";
import { NAV_ITEMS } from "@/shared/navigation/navItems";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  /** Phone More drawer — logout lives here so the top bar stays slim. */
  onLogout?: () => void;
}

export function Sidebar({ isOpen, onClose, onLogout }: SidebarProps) {
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
    if (item.hiddenInNav) return false;
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

  // Phone drawer sits between the header and the tab bar.
  // English slides in from the right; Arabic slides in from the left.
  return (
    <>
      <aside
        className={`w-64 shrink-0 border-e border-neutral-200 bg-neutral-0 shadow-lg transition-transform duration-300 ease-out max-lg:absolute max-lg:inset-y-0 max-lg:z-30 lg:sticky lg:top-0 lg:z-auto lg:flex lg:h-full lg:min-h-0 lg:flex-col lg:translate-x-0 lg:self-stretch lg:overflow-hidden ${
          isRTL ? "max-lg:left-0" : "max-lg:right-0"
        } ${
          isOpen
            ? "max-lg:translate-x-0"
            : isRTL
              ? "max-lg:-translate-x-full"
              : "max-lg:translate-x-full"
        }`}
      >
        <div className="flex h-full min-h-0 w-full flex-col">
          <div className="flex h-8 shrink-0 items-center justify-end lg:hidden">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-neutral-800 hover:bg-neutral-100"
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
            <nav className="flex-1 overflow-y-auto px-2 py-1 lg:py-4">
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
            <div className="shrink-0 border-t border-neutral-200 px-4 py-3">
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
              {onLogout && (
                <button
                  type="button"
                  className="mt-3 flex min-h-11 w-full items-center justify-center rounded-lg bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700"
                  onClick={() => {
                    onClose();
                    onLogout();
                  }}
                >
                  {t("logout")}
                </button>
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
