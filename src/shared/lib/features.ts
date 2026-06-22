import type { User } from "./types";

/** Tenant subscription feature flags from GET /users/me (Wave 3 NT-120). */
export function hasFeature(user: User | null | undefined, feature: string): boolean {
  if (!user) return false;
  if (user.is_platform_admin) return true;
  const features = user.features ?? [];
  return features.includes(feature);
}
