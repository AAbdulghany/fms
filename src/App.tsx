import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { ReactNode, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { NotificationProvider } from "./contexts/NotificationContext";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { InvoiceDetailPage } from "./pages/InvoiceDetailPage";
import { InvoicesPage } from "./pages/InvoicesPage";
import { LoginPage } from "./pages/LoginPage";
import { WorkOrderDetailPage } from "./pages/WorkOrderDetailPage";
import { WorkOrdersPage } from "./pages/WorkOrdersPage";
import CompaniesPage from "./pages/CompaniesPage";
import CompanyDetailPage from "./pages/CompanyDetailPage";
import SiteDetailPage from "./pages/SiteDetailPage";
import AssetsPage from "./pages/AssetsPage";
import AssetDetailPage from "./pages/AssetDetailPage";
import UsersPage from "./pages/UsersPage";
import LaborPage from "./pages/LaborPage";
import LocationsPage from "./pages/LocationsPage";
import { SubscriptionPage } from "./pages/SubscriptionPage";
import { PlatformPackagesPage } from "./pages/PlatformPackagesPage";
import { MaintenanceCompaniesPage } from "./pages/MaintenanceCompaniesPage";
import { ProfilePage } from "./pages/ProfilePage";
import ReportTemplatesPage from "./pages/ReportTemplatesPage";
import { apiFetch } from "./lib/api";
import type { User } from "./lib/types";
import { hasFeature } from "./lib/features";

interface FeatureRouteProps {
  feature: string;
  children: ReactNode;
}

function FeatureRoute({ feature, children }: FeatureRouteProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const data = await apiFetch<User>("/users/me");
        setUser(data);
      } catch {
        // ignore — ProtectedRoute already guards auth
      } finally {
        setChecked(true);
      }
    })();
  }, []);

  if (!checked) return null;

  if (user && !hasFeature(user, feature)) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="max-w-sm rounded-lg border border-neutral-200 bg-neutral-0 p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-100">
            <svg className="h-7 w-7 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="mb-2 text-lg font-semibold text-neutral-900">{t("feature_not_available")}</h2>
          <p className="text-sm text-neutral-500">
            {t("feature_not_available_hint") || "This feature is not included in your current plan. Contact your administrator to enable it."}
          </p>
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="mt-5 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            {t("dashboard")}
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <NotificationProvider>
        <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout>
                <Navigate to="/dashboard" replace />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/companies"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
              <Layout>
                <CompaniesPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/companies/:id"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
              <Layout>
                <CompanyDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/sites/:id"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager"]}>
              <Layout>
                <SiteDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/assets"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager"]}>
              <Layout>
                <FeatureRoute feature="assets">
                  <AssetsPage />
                </FeatureRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/assets/:id"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager"]}>
              <Layout>
                <FeatureRoute feature="assets">
                  <AssetDetailPage />
                </FeatureRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/work-orders"
          element={
            <ProtectedRoute>
              <Layout>
                <WorkOrdersPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/work-orders/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <WorkOrderDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/invoices"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin"]}>
              <Layout>
                <FeatureRoute feature="invoices">
                  <InvoicesPage />
                </FeatureRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/invoices/:id"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin"]}>
              <Layout>
                <FeatureRoute feature="invoices">
                  <InvoiceDetailPage />
                </FeatureRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/users"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
              <Layout>
                <UsersPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/labor"
          element={
            <ProtectedRoute
              allowedRoles={["super_admin", "company_admin", "manager", "technician"]}
            >
              <Layout>
                <LaborPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/locations"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin"]}>
              <Layout>
                <LocationsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/platform/maintenance-companies"
          element={
            <ProtectedRoute allowedRoles={["super_user", "sw_dev", "super_admin"]}>
              <Layout>
                <MaintenanceCompaniesPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/platform/packages"
          element={
            <ProtectedRoute allowedRoles={["super_user", "sw_dev", "super_admin"]}>
              <Layout>
                <PlatformPackagesPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/subscription"
          element={
            <ProtectedRoute allowedRoles={["super_user", "sw_dev", "super_admin"]}>
              <Layout>
                <SubscriptionPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Layout>
                <ProfilePage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/report-templates"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
              <Layout>
                <ReportTemplatesPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </NotificationProvider>
    </BrowserRouter>
  );
}
