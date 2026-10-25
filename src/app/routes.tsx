import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/shared/components/Layout";
import { ProtectedRoute } from "@/shared/components/ProtectedRoute";
import { FeatureRoute } from "@/shared/components/FeatureRoute";
import { FieldHomeRedirect } from "@/shared/components/FieldHomeRedirect";

const LoginPage = lazy(() =>
  import("@/features/auth/pages/LoginPage").then((m) => ({ default: m.LoginPage }))
);
const DashboardPage = lazy(() =>
  import("@/features/dashboard/pages/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const InvoiceDetailPage = lazy(() =>
  import("@/features/invoices/pages/InvoiceDetailPage").then((m) => ({ default: m.InvoiceDetailPage }))
);
const InvoicesPage = lazy(() =>
  import("@/features/invoices/pages/InvoicesPage").then((m) => ({ default: m.InvoicesPage }))
);
const WorkOrderDetailPage = lazy(() =>
  import("@/features/work-orders/pages/WorkOrderDetailPage").then((m) => ({
    default: m.WorkOrderDetailPage,
  }))
);
const WorkOrdersPage = lazy(() =>
  import("@/features/work-orders/pages/WorkOrdersPage").then((m) => ({ default: m.WorkOrdersPage }))
);
const CompaniesPage = lazy(() => import("@/features/companies/pages/CompaniesPage"));
const CompanyDetailPage = lazy(() => import("@/features/companies/pages/CompanyDetailPage"));
const SiteDetailPage = lazy(() => import("@/features/companies/pages/SiteDetailPage"));
const AssetsPage = lazy(() => import("@/features/assets/pages/AssetsPage"));
const AssetDetailPage = lazy(() => import("@/features/assets/pages/AssetDetailPage"));
const ScanAssetPage = lazy(() => import("@/features/assets/pages/ScanAssetPage"));
const MaintenanceCalendarPage = lazy(() => import("@/features/assets/pages/MaintenanceCalendarPage"));
const UsersPage = lazy(() => import("@/features/users/pages/UsersPage"));
const LaborPage = lazy(() => import("@/features/labor/pages/LaborPage"));
const LocationsPage = lazy(() => import("@/features/locations/pages/LocationsPage"));
const SubscriptionPage = lazy(() =>
  import("@/features/platform/pages/SubscriptionPage").then((m) => ({ default: m.SubscriptionPage }))
);
const PlatformPackagesPage = lazy(() =>
  import("@/features/platform/pages/PlatformPackagesPage").then((m) => ({
    default: m.PlatformPackagesPage,
  }))
);
const MaintenanceCompaniesPage = lazy(() =>
  import("@/features/platform/pages/MaintenanceCompaniesPage").then((m) => ({
    default: m.MaintenanceCompaniesPage,
  }))
);
const ProfilePage = lazy(() =>
  import("@/features/users/pages/ProfilePage").then((m) => ({ default: m.ProfilePage }))
);
const ReportTemplatesPage = lazy(() => import("@/features/reports/pages/ReportTemplatesPage"));
const AssetTypesPage = lazy(() => import("@/features/assets/pages/AssetTypesPage"));
const AssetTagLandingPage = lazy(() => import("@/features/assets/pages/AssetTagLandingPage"));
const CommercialTermsPage = lazy(() => import("@/features/billing/pages/CommercialTermsPage"));
const InventoryPage = lazy(() => import("@/features/billing/pages/InventoryPage"));

function PageFallback() {
  return (
    <div className="flex min-h-[240px] items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
    </div>
  );
}

function LazyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageFallback />}>{children}</Suspense>;
}

/** Application route table — pages live under src/features/…/pages/. */
export function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <LazyPage>
            <LoginPage />
          </LazyPage>
        }
      />
      <Route
        path="/a/:token"
        element={
          <LazyPage>
            <AssetTagLandingPage />
          </LazyPage>
        }
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <FieldHomeRedirect />
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <LazyPage>
                <DashboardPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/companies"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
            <Layout>
              <LazyPage>
                <CompaniesPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/companies/:id"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
            <Layout>
              <LazyPage>
                <CompanyDetailPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/sites/:id"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager"]}>
            <Layout>
              <LazyPage>
                <SiteDetailPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/scan"
        element={
          <ProtectedRoute
            allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager", "technician"]}
          >
            <Layout>
              <FeatureRoute feature="assets">
                <LazyPage>
                  <ScanAssetPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/assets"
        element={
          <ProtectedRoute
            allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager", "technician"]}
          >
            <Layout>
              <FeatureRoute feature="assets">
                <LazyPage>
                  <AssetsPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/assets/maintenance-calendar"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager"]}>
            <Layout>
              <FeatureRoute feature="assets">
                <LazyPage>
                  <MaintenanceCalendarPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/assets/:id"
        element={
          <ProtectedRoute
            allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager", "technician"]}
          >
            <Layout>
              <FeatureRoute feature="assets">
                <LazyPage>
                  <AssetDetailPage />
                </LazyPage>
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
              <LazyPage>
                <WorkOrdersPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/work-orders/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <LazyPage>
                <WorkOrderDetailPage />
              </LazyPage>
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
                <LazyPage>
                  <InvoicesPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/billing/commercial-terms"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
            <Layout>
              <FeatureRoute feature="invoices">
                <LazyPage>
                  <CommercialTermsPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/billing/inventory"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
            <Layout>
              <FeatureRoute feature="invoices">
                <LazyPage>
                  <InventoryPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />
      {/* Legacy billing URLs → merged pages */}
      <Route path="/billing/parts" element={<Navigate to="/billing/inventory" replace />} />
      <Route path="/billing/tax" element={<Navigate to="/billing/commercial-terms" replace />} />
      <Route path="/billing/pricing" element={<Navigate to="/billing/commercial-terms" replace />} />
      <Route path="/billing/contracts" element={<Navigate to="/billing/commercial-terms" replace />} />

      <Route
        path="/invoices/:id"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin"]}>
            <Layout>
              <FeatureRoute feature="invoices">
                <LazyPage>
                  <InvoiceDetailPage />
                </LazyPage>
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
              <LazyPage>
                <UsersPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/labor"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin", "manager", "technician"]}>
            <Layout>
              <LazyPage>
                <LaborPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/locations"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin"]}>
            <Layout>
              <LazyPage>
                <LocationsPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/platform/maintenance-companies"
        element={
          <ProtectedRoute allowedRoles={["super_user", "sw_dev", "super_admin"]}>
            <Layout>
              <LazyPage>
                <MaintenanceCompaniesPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/platform/packages"
        element={
          <ProtectedRoute allowedRoles={["super_user", "sw_dev", "super_admin"]}>
            <Layout>
              <LazyPage>
                <PlatformPackagesPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/subscription"
        element={
          <ProtectedRoute allowedRoles={["super_user", "sw_dev", "super_admin"]}>
            <Layout>
              <LazyPage>
                <SubscriptionPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Layout>
              <LazyPage>
                <ProfilePage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/report-templates"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
            <Layout>
              <LazyPage>
                <ReportTemplatesPage />
              </LazyPage>
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* A1: Asset Types Library — company_admin / super_admin only */}
      <Route
        path="/asset-types"
        element={
          <ProtectedRoute allowedRoles={["super_admin", "company_admin"]}>
            <Layout>
              <FeatureRoute feature="assets">
                <LazyPage>
                  <AssetTypesPage />
                </LazyPage>
              </FeatureRoute>
            </Layout>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
