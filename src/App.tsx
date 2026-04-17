import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { NotificationProvider } from "./contexts/NotificationContext";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
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
                <AssetsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/assets/:id"
          element={
            <ProtectedRoute allowedRoles={["super_admin", "company_admin", "client_admin", "site_manager"]}>
              <Layout>
                <AssetDetailPage />
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
                <InvoicesPage />
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

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </NotificationProvider>
    </BrowserRouter>
  );
}
