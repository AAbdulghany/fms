import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/shared/components/Layout";
import { ProtectedRoute } from "@/shared/components/ProtectedRoute";
import { FeatureRoute } from "@/shared/components/FeatureRoute";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { InvoiceDetailPage } from "@/features/invoices/pages/InvoiceDetailPage";
import { InvoicesPage } from "@/features/invoices/pages/InvoicesPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { WorkOrderDetailPage } from "@/features/work-orders/pages/WorkOrderDetailPage";
import { WorkOrdersPage } from "@/features/work-orders/pages/WorkOrdersPage";
import CompaniesPage from "@/features/companies/pages/CompaniesPage";
import CompanyDetailPage from "@/features/companies/pages/CompanyDetailPage";
import SiteDetailPage from "@/features/companies/pages/SiteDetailPage";
import AssetsPage from "@/features/assets/pages/AssetsPage";
import AssetDetailPage from "@/features/assets/pages/AssetDetailPage";
import UsersPage from "@/features/users/pages/UsersPage";
import LaborPage from "@/features/labor/pages/LaborPage";
import LocationsPage from "@/features/locations/pages/LocationsPage";
import { SubscriptionPage } from "@/features/platform/pages/SubscriptionPage";
import { PlatformPackagesPage } from "@/features/platform/pages/PlatformPackagesPage";
import { MaintenanceCompaniesPage } from "@/features/platform/pages/MaintenanceCompaniesPage";
import { ProfilePage } from "@/features/users/pages/ProfilePage";
import ReportTemplatesPage from "@/features/reports/pages/ReportTemplatesPage";

/** Application route table — pages live under src/features/…/pages/. */
export function AppRoutes() {
  return (
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
          <ProtectedRoute allowedRoles={["super_admin", "company_admin", "manager", "technician"]}>
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
  );
}
