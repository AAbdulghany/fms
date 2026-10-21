# Shared frontend modules

Cross-feature code used by multiple domains.

| Path | Contents |
|------|----------|
| `lib/` | API client, types, roles, features, i18n helpers |
| `components/` | Layout, Sidebar, ProtectedRoute, FeatureRoute, … |

Import via `@/lib/...` or `@/shared/components/...`.  
Legacy `@/components` / `@/pages` shims were removed (CLEAN-003/004). Use `@/shared/...` or `@/features/...`.
