import type { User } from "./types";

/** Tenant subscription feature flags from GET /users/me (Wave 3 NT-120). */
export function hasFeature(user: User | null | undefined, feature: string): boolean {
  if (!user) return false;
  if (user.is_platform_admin) return true;
  // Login payload is UserPublic without `features` — treat as unknown (allow) until /me loads.
  // Explicit empty array means the tenant truly has no modules.
  if (user.features === undefined) return true;
  return user.features.includes(feature);
}
