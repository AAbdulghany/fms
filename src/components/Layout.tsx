import { ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { clearTokens } from "../lib/api";
import { Sidebar } from "./Sidebar";

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
    <div className="flex min-h-screen bg-neutral-50" dir={isRTL ? "rtl" : "ltr"}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-1 flex-col">
        <header className="border-b border-neutral-200 bg-neutral-0 shadow-sm">
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

        <main className="flex-1 overflow-x-hidden px-4 py-6 lg:px-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-neutral-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
