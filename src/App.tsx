import { ReactNode, useState, useEffect } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { clearTokens } from "./lib/api";
import { DashboardPage } from "./pages/DashboardPage";
import { InvoicesPage } from "./pages/InvoicesPage";
import { LoginPage } from "./pages/LoginPage";
import { WorkOrderDetailPage } from "./pages/WorkOrderDetailPage";
import { WorkOrdersPage } from "./pages/WorkOrdersPage";

function Layout({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [userRole, setUserRole] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRole() {
      try {
        const response = await fetch("/api/v1/users/me");
        if (response.ok) {
          const data = await response.json();
          setUserRole(data.role);
        }
      } catch (e) {
        console.error("Failed to fetch user role", e);
      }
    }
    fetchRole();
  }, []);

  const toggleLang = () => {
    const next = i18n.language === "ar" ? "en" : "ar";
    void i18n.changeLanguage(next);
    localStorage.setItem("app_lang", next);
    document.documentElement.lang = next;
    document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
    document.body.className =
      next === "ar" ? "fms-page font-body-ar" : "fms-page font-body-en";
  };

  const canViewInvoices = ["super_admin", "company_admin", "client_admin"].includes(userRole || "");

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-neutral-0 shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="text-lg font-semibold text-primary-600 font-display-ar">
            {t("app_title")}
          </Link>
          <nav className="flex flex-wrap items-center gap-4 text-sm font-medium text-neutral-700">
            <Link className="hover:text-primary-600" to="/">
              {t("dashboard")}
            </Link>
            <Link className="hover:text-primary-600" to="/work-orders">
              {t("work_orders")}
            </Link>
            {canViewInvoices && (
              <Link className="hover:text-primary-600" to="/invoices">
                {t("invoices")}
              </Link>
            )}
            <button
              type="button"
              className="rounded-md border border-neutral-300 px-2 py-1 text-xs hover:bg-neutral-100"
              onClick={toggleLang}
            >
              {t("language")}: {i18n.language.toUpperCase()}
            </button>
            <button
              type="button"
              className="text-error-main hover:underline"
              onClick={() => {
                clearTokens();
                navigate("/login");
              }}
            >
              {t("logout")}
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}

function PrivateRoute({ children }: { children: ReactNode }) {
  if (!localStorage.getItem("access_token")) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <DashboardPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/work-orders"
          element={
            <PrivateRoute>
              <WorkOrdersPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/work-orders/:id"
          element={
            <PrivateRoute>
              <WorkOrderDetailPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/invoices"
          element={
            <PrivateRoute>
              <InvoicesPage />
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
