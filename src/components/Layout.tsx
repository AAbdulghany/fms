import { ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { clearTokens } from "../lib/api";
import { Sidebar } from "./Sidebar";
import ClockWidget from "./ClockWidget";
import NotificationBell from "./NotificationBell";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isRTL = i18n.dir() === "rtl";

  const toggleLang = () => {
    const next = i18n.language === "ar" ? "en" : "ar";
    void i18n.changeLanguage(next);
    localStorage.setItem("app_lang", next);
    document.documentElement.lang = next;
    document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
    document.body.className =
      next === "ar" ? "fms-page font-body-ar" : "fms-page font-body-en";
  };

  const handleLogout = () => {
    clearTokens();
    navigate("/login");
  };

  return (
    <div
      className="grid min-h-screen min-h-dvh grid-rows-[auto_minmax(0,1fr)] overflow-x-hidden bg-neutral-50"
      dir={isRTL ? "rtl" : "ltr"}
    >
      <header className="relative z-40 shrink-0 border-b border-neutral-200 bg-neutral-0 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3 lg:px-6">
          <div className="flex items-center gap-4">
            <button
              type="button"
              className="rounded-md p-2 text-neutral-600 hover:bg-neutral-100 lg:hidden"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label={t("toggle_menu")}
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>

            <h1 className="text-lg font-semibold text-primary-600 font-display-ar lg:text-xl">
              {t("app_title")}
            </h1>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <ClockWidget />
            <NotificationBell />
            <button
              type="button"
              className="rounded-md border border-neutral-300 px-2 py-1 text-xs hover:bg-neutral-100 sm:px-3 sm:py-1.5 sm:text-sm"
              onClick={toggleLang}
            >
              {i18n.language.toUpperCase()}
            </button>

            <button
              type="button"
              className="rounded-md px-2 py-1 text-xs text-error-main hover:bg-error-light sm:px-3 sm:py-1.5 sm:text-sm"
              onClick={handleLogout}
            >
              {t("logout")}
            </button>
          </div>
        </div>
      </header>

      <div className="flex h-full min-h-0 min-w-0 items-stretch">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div
          className={`flex min-w-0 flex-1 flex-col transition-[margin] duration-300 ease-out ${
            sidebarOpen ? (isRTL ? "max-lg:mr-64" : "max-lg:ml-64") : ""
          }`}
        >
          <main className="flex-1 min-w-0 overflow-x-hidden px-4 py-6 lg:px-8">
            <div className="mx-auto w-full max-w-[min(100%,88rem)]">{children}</div>
          </main>
        </div>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-x-0 bottom-0 top-14 z-20 bg-neutral-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
