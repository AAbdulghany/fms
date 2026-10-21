# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev          # Start Vite dev server (port 5173) with hot reload
npm run build        # TypeScript compile + Vite build
npm run preview      # Preview production build
npm run dev:css      # Tailwind CSS watch mode
npm run build:css    # Tailwind CSS one-time build (minified)
```

**Documentation:** [docs/README.md](docs/README.md) · [local dev](docs/guides/local-development.md) · [environments](docs/guides/environments.md) · [testing](docs/guides/testing.md)

## Architecture Overview

**Facility Management System (Orbit)** — React 18 + TypeScript + Vite SPA with bilingual support (English/Arabic, RTL).

### Tech Stack
- **Framework:** React 18 with TypeScript (JSX mode)
- **Build:** Vite 6 with @vitejs/plugin-react
- **Styling:** Tailwind CSS 3 with custom design tokens in `src/styles/tokens.css`
- **Routing:** React Router 6 with protected routes
- **State:** localStorage for auth tokens; component-level useState/useEffect
- **i18n:** react-i18next with locale JSON (AR default, EN fallback)

### Project Structure
```
src/
├── main.tsx                 # Entry: mounts App with I18nextProvider
├── App.tsx                  # Thin shell → app router
├── app/                     # Router, auth guard, providers
├── features/                # Domain UI (auth, work-orders, …)/{pages,components}
├── shared/
│   ├── lib/                 # apiFetch (also @/lib), types, helpers
│   ├── components/          # Layout, nav, shared UI
│   └── navigation/          # Field shell tabs, redirects
├── features/pwa/            # Manifest / install banner
├── i18n/locales/            # AR/EN JSON
└── styles/
    ├── globals.css
    ├── tokens.css
    └── tailwind.theme.js
```

Import via `@/features/...` or `@/shared/...`. Do **not** use `@/components` or `@/pages` (guard: `npm run check:imports`).

### API Integration
- Base URL: `/api/v1` (proxied to `http://127.0.0.1:8000` in dev)
- Auth: Bearer token stored in localStorage (`access_token`, `refresh_token`)
- Key endpoints:
  - `POST /auth/login` → `{ access_token, refresh_token, user }`
  - `GET /work-orders` → paginated list
  - `GET /work-orders/:id` → single WO
  - `PUT /work-orders/:id/report` → save draft report
  - `POST /work-orders/:id/report/submit` → submit for approval
  - `POST /reports/:id/approve` → approve report
  - `PATCH /work-orders/:id` → update status
  - `POST /work-orders/:id/generate-invoice` → create invoice (requires verified status)

### Authentication Flow
1. Login form submits credentials to `/auth/login`
2. Tokens stored in localStorage
3. `PrivateRoute` checks for `access_token`; redirects to `/login` if missing
4. `apiFetch()` automatically attaches `Authorization: Bearer <token>` header

### Work Order Lifecycle
Statuses: `created` → `assigned` → `in_progress` → `on_hold` → `completed` → `verified` → `closed` (or `cancelled`)

Report workflow: `draft` → `submitted` → `approved` → invoice generation available

### Role-Based UI
- **technician/site_manager/company_admin/super_admin:** can edit reports
- **company_admin/client_admin/manager/super_admin:** can approve reports
- **company_admin/super_admin/site_manager:** can change WO status, generate invoices
