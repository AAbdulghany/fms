import type { User, UserRole } from "./types";

const PLATFORM_ROLES: UserRole[] = ["super_user", "sw_dev", "super_admin"];

/** Software company staff — platform nav + legacy tenant super_admin nav. */
export function isPlatformStaff(user: Pick<User, "role" | "is_platform_admin">): boolean {
  return Boolean(user.is_platform_admin) || PLATFORM_ROLES.includes(user.role);
}

export function hasAnyRole(userRole: UserRole, allowed: UserRole[]): boolean {
  if (allowed.includes(userRole)) return true;
  if (userRole === "company_engineer" && allowed.includes("company_admin")) return true;
  if (userRole === "super_user" && allowed.includes("super_admin")) return true;
  if (userRole === "sw_dev" && allowed.includes("super_admin")) return true;
  return false;
}

export const TENANT_STAFF_CREATABLE: UserRole[] = [
  "technician",
  "client_admin",
  "site_manager",
  "company_engineer",
  "manager",
];

/** Platform peers a Platform Super User may invite from Users. */
export const PLATFORM_STAFF_CREATABLE: UserRole[] = ["sw_dev", "super_user"];

export const COMPANY_ENGINEER_CREATABLE: UserRole[] = [
  "technician",
  "client_admin",
  "site_manager",
  "manager",
];

export function creatableRolesFor(actorRole: UserRole): UserRole[] {
  // Platform Super User (and legacy platform super_admin) can invite SW Developers.
  if (actorRole === "super_user") {
    return [...PLATFORM_STAFF_CREATABLE, ...TENANT_STAFF_CREATABLE];
  }
  if (actorRole === "super_admin" || actorRole === "company_admin") {
    return TENANT_STAFF_CREATABLE;
  }
  if (actorRole === "company_engineer") {
    return COMPANY_ENGINEER_CREATABLE;
  }
  return [];
}
