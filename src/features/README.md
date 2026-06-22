# Frontend features

Feature-oriented UI modules. Each domain has `pages/` and optionally `components/`.

| Feature | Pages | Components |
|---------|-------|------------|
| `auth/` | LoginPage | — |
| `dashboard/` | DashboardPage | — |
| `companies/` | Companies, CompanyDetail, SiteDetail | modals (create, provision, QR, …) |
| `assets/` | Assets, AssetDetail | calendar, lifecycle, import modals |
| `work-orders/` | WorkOrders, WorkOrderDetail | request review modal |
| `invoices/` | Invoices, InvoiceDetail | preview modal |
| `users/` | Users, Profile | — |
| `platform/` | packages, subscription, maintenance companies | — |
| `reports/` | ReportTemplates | — |
| `locations/` | LocationsPage | — |
| `labor/` | LaborPage | — |
| `shared/` | FeatureUnavailablePage | — |

Shell components live in `src/shared/components/`. Import via `@/features/...` or `@/shared/...`. Legacy `src/pages/` and `src/components/` shims remain for one release cycle.
