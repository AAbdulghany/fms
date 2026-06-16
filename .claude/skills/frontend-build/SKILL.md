---
name: frontend-build
description: >-
  Debug FMS frontend build failures — `tsc -b`, Vite, duplicate i18n keys,
  User type drift vs backend schemas. Use when `npm run build` fails or preview
  serves stale bundles.
disable-model-invocation: false
argument-hint: "[error snippet or command]"
effort: medium
---

# /frontend-build — FMS frontend build debugging

Use this skill **before** guessing when `npm run build`, `tsc -b`, or `vite build` fails.

**Stack:** React + TypeScript + Vite. Build command: `npm run build` → `tsc -b && vite build`.

## Quick repro

From repo root:

```powershell
npm run build
```

For local dev (no type gate): `npm run dev`.  
For production-like preview: **always build first** — `npm run preview` serves `dist/` and will not pick up source edits until rebuild.

## Decision tree

```
npm run build failed?
├─ TS1117 duplicate property in object literal
│  └─ Usually src/i18n/index.ts — search duplicate keys in ar AND en blocks
│     rg '^\s+(\w+):' src/i18n/index.ts | sort | uniq -d   (conceptually)
│     Fix: remove the newer duplicate; keep the key in one section (often // Common)
├─ TS2339 Property 'X' does not exist on type 'User'
│  └─ Frontend User in src/lib/types.ts drifted from backend UserPublic
│     Compare: backend/app/schemas.py → UserPublic fields
│     Add optional fields (locale, username, client_id, …) to src/lib/types.ts
├─ TS2307 Cannot find module
│  └─ Missing file, wrong path, or case mismatch on Windows
├─ TS2345 / role union mismatch
│  └─ New UserRole enum value added backend-side but not in src/lib/types.ts
│     Also check src/lib/roles.ts hasAnyRole aliases
└─ Vite error after tsc passes
   └─ Read vite message; often bad import or env var
```

## Common FMS pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Sidebar empty for `super_user` | Nav allowedRoles only listed `super_admin` | `hasAnyRole` in `src/lib/roles.ts` maps platform roles |
| Preview shows old UI | `npm run preview` without rebuild | `npm run build` then preview |
| i18n key shows raw string | Key missing in **both** `ar` and `en` in `src/i18n/index.ts` | Add to both translation objects |
| TS1117 on `filter` | Key added near feature keys **and** in `// Common` block | Keep one `filter` per language |
| Login locale TS error | `User` type missing `locale` | Align with `UserPublic.locale` in schemas.py |
| English strings in Arabic UI | Hardcoded `\|\| "fallback"` or missing i18n keys | Add keys to **both** `ar` and `en` in `src/i18n/index.ts`; use `t("key")` only |
| Language resets on logout | Login overwrote `app_lang` with `user.locale` | Use `applyLanguage(getStoredLanguage(), i18n)` from `src/lib/language.ts` |
| Client dashboard "Create WO" wrong | Navigated to list instead of request modal | Dashboard → `/work-orders?open=request`; WorkOrdersPage opens modal |
| Asset register missing client pick | Modal only had site dropdown | `AssetRegisterModal` — client select for tenant staff; locked for client/site mgr |
| Vercel/Netlify login 404 on `/api` | Proxy URL not set in `vercel.json` / `netlify.toml` | [DEMO_VERCEL_NETLIFY.md](../../docs/phase3-restructure/DEMO_VERCEL_NETLIFY.md) |
| Render API cold start | Free tier sleeps ~15 min | Wait 60 s on first request; or upgrade Render plan |

## UX / i18n debugging

```
Symptom?
├─ Raw i18n key shown (enable_maintenance_schedule)
│  └─ grep key in src/i18n/index.ts — must exist in ar AND en translation objects
├─ Language flips on logout/login
│  └─ Never apply user.locale over localStorage app_lang on login
│     Use src/lib/language.ts → applyLanguage + getStoredLanguage everywhere
├─ Role-specific form missing fields
│  └─ Fetch /users/me in modal; branch on role (see AssetRegisterModal pattern)
└─ Quick action goes to wrong page
   └─ Prefer ?open=request query param to reuse existing modal on target page
```

**Language persistence:** `localStorage.app_lang` is the source of truth for UI language. User profile `locale` is not applied on login unless you explicitly want profile-driven language (not current product behaviour).

## Type sync checklist (backend ↔ frontend)

When touching auth or `/users/me`:

1. Read `backend/app/schemas.py` → `UserPublic`, `UserListOut`.
2. Update `src/lib/types.ts` → `User`, `UserRole`.
3. If new role: update `src/lib/roles.ts`, `UserRoleBadge.tsx`, i18n `role_*` keys, `Sidebar.tsx` allowedRoles.
4. Run `npm run build` — dev server does not run `tsc -b`.

**UserPublic fields (keep in sync):**

- `id`, `tenant_id`, `client_id`, `email`, `username`, `full_name`, `role`, `locale`, `is_active`, `is_platform_admin`

## Agent checklist

1. Run `npm run build` and capture **full** tsc output (file + line).
2. Fix root cause — do not `@ts-ignore` unless truly unavoidable.
3. Re-run `npm run build` until clean.
4. If the pattern is new, add a row to **Common FMS pitfalls** in this skill.

## Related

- Docker/API: `.claude/skills/docker-debug/SKILL.md`
- Demo logins: `docs/phase3-restructure/DEMO_QUICKSTART.md`
- RBAC roles: `docs/phase3-restructure/RBAC_ROLES.md`
