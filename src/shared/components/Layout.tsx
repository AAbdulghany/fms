import { ReactNode, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { apiFetch, clearTokens } from "@/lib/api";
import { applyLanguage, getStoredLanguage } from "@/lib/language";
import type { User } from "@/lib/types";
import { Sidebar } from "@/shared/components/Sidebar";
import { MobileBottomNav } from "@/shared/components/MobileBottomNav";
import ClockWidget from "@/shared/components/ClockWidget";
import NotificationBell from "@/shared/components/NotificationBell";
import { OrbitLogo } from "@/shared/components/OrbitLogo";
import { shellParentPath } from "@/shared/navigation/shellParent";
import { InstallOrbitBanner } from "@/features/pwa/InstallOrbitBanner";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const isRTL = i18n.dir() === "rtl";

  useEffect(() => {
    const shell = shellRef.current;
    const viewport = window.visualViewport;
    if (!shell || !viewport) return;

    const apply = () => {
      if (window.innerWidth >= 1024) {
        shell.style.height = "";
        shell.style.top = "";
        return;
      }
      shell.style.height = `${viewport.height}px`;
      shell.style.top = `${viewport.offsetTop}px`;
    };

    apply();
    viewport.addEventListener("resize", apply);
    viewport.addEventListener("scroll", apply);
    window.addEventListener("resize", apply);
    return () => {
      viewport.removeEventListener("resize", apply);
      viewport.removeEventListener("scroll", apply);
      window.removeEventListener("resize", apply);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadUser() {
      try {
        const data = await apiFetch<User>("/users/me");
        if (!cancelled) setUser(data);
      } catch {
        if (!cancelled) setUser(null);
      }
    }
    void loadUser();
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleLang = () => {
    const next = i18n.language === "ar" ? "en" : "ar";
    applyLanguage(next, i18n);
  };

  const handleLogout = () => {
    const lang = getStoredLanguage();
    clearTokens();
    applyLanguage(lang, i18n);
    navigate("/login");
  };

  return (
    <div
      ref={shellRef}
      className="orbit-app-shell relative grid h-dvh max-h-dvh grid-rows-[auto_minmax(0,1fr)] overflow-hidden bg-neutral-50 max-lg:fixed max-lg:inset-x-0 max-lg:top-0 max-lg:h-svh max-lg:max-h-none"
      dir={isRTL ? "rtl" : "ltr"}
    >
      <header className="z-40 h-14 shrink-0 border-b border-neutral-200 bg-neutral-0 shadow-sm">
        <div className="flex h-full items-center justify-between px-3 lg:px-6">
          <div className="flex min-w-0 items-center gap-2 lg:gap-4">
            {shellParentPath(pathname) && (
              <button
                type="button"
                aria-label={t("back")}
                className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md text-2xl leading-none text-neutral-800 hover:bg-neutral-100"
                onClick={() => {
                  const parent = shellParentPath(pathname);
                  if (parent) navigate(parent);
                }}
              >
                <span aria-hidden className="inline-block rtl:-scale-x-100">‹</span>
              </button>
            )}
            <OrbitLogo iconSize={26} tenantName={user?.tenant_name} />
          </div>

          <div className="flex shrink-0 items-center gap-1.5 sm:gap-3">
            <div className="hidden sm:block">
              <ClockWidget />
            </div>
            <NotificationBell />
            <button
              type="button"
              className="min-h-10 rounded-md border border-neutral-300 px-2.5 py-1.5 text-xs font-medium hover:bg-neutral-100 sm:px-3 sm:text-sm"
              onClick={toggleLang}
            >
              {i18n.language.toUpperCase()}
            </button>

            <button
              type="button"
              className="inline-flex min-h-10 shrink-0 items-center rounded-md bg-red-600 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-red-700 sm:px-3 sm:text-sm"
              onClick={handleLogout}
            >
              {t("logout")}
            </button>
          </div>
        </div>
      </header>

      <div className="relative flex h-full min-h-0 min-w-0 items-stretch overflow-hidden">
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onLogout={handleLogout}
        />

        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <main className="min-h-0 min-w-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-y-contain px-3 py-3 lg:px-8 lg:py-6">
            <div className="mx-auto w-full max-w-[min(100%,88rem)]">{children}</div>
          </main>
        </div>

        {sidebarOpen && (
          <div
            className="absolute inset-0 z-20 bg-neutral-900/40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}
      </div>

      <MobileBottomNav
        user={user}
        moreOpen={sidebarOpen}
        onMore={() => setSidebarOpen((open) => !open)}
      />
      <InstallOrbitBanner />
    </div>
  );
}
