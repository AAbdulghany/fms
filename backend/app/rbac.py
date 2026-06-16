"""Role hierarchy and permission helpers (Phase 3 multi-tenant)."""

from __future__ import annotations

from app.models import User, UserRole

# Software company staff (platform) — require is_platform_admin=True
PLATFORM_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.super_user, UserRole.sw_dev, UserRole.super_admin}
)

# Maintenance company leadership — full tenant ops except platform routes
TENANT_ADMIN_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.company_admin, UserRole.company_engineer, UserRole.super_admin}
)

# Same UI/API access as company_admin (billing, users list, clients, assets, …)
TENANT_OPERATIONS_ROLES: frozenset[UserRole] = TENANT_ADMIN_ROLES | frozenset({UserRole.manager})

# Roles company_admin may create
COMPANY_ADMIN_CREATABLE: frozenset[UserRole] = frozenset(
    {
        UserRole.technician,
        UserRole.client_admin,
        UserRole.site_manager,
        UserRole.company_engineer,
        UserRole.manager,
    }
)

# Roles company_engineer may create (no peer engineers or company admins)
COMPANY_ENGINEER_CREATABLE: frozenset[UserRole] = frozenset(
    {
        UserRole.technician,
        UserRole.client_admin,
        UserRole.site_manager,
        UserRole.manager,
    }
)

# Platform staff may create when provisioning a tenant
PLATFORM_TENANT_USER_CREATABLE: frozenset[UserRole] = frozenset(
    {
        UserRole.company_admin,
        UserRole.company_engineer,
        UserRole.technician,
        UserRole.client_admin,
        UserRole.site_manager,
        UserRole.manager,
    }
)


def is_platform_staff(user: User) -> bool:
    return bool(user.is_platform_admin) or user.role in PLATFORM_ROLES


def can_remove_members(user: User) -> bool:
    """Deactivate/delete users. sw_dev is support-only — cannot remove members."""
    if user.role == UserRole.sw_dev:
        return False
    return is_platform_staff(user) or user.role in TENANT_ADMIN_ROLES


def can_create_role(actor: User, target: UserRole) -> bool:
    if is_platform_staff(actor):
        if target in {UserRole.super_user, UserRole.sw_dev, UserRole.super_admin}:
            return actor.role == UserRole.super_user or actor.role == UserRole.super_admin
        return target in PLATFORM_TENANT_USER_CREATABLE or target in COMPANY_ADMIN_CREATABLE

    if actor.role == UserRole.company_admin:
        return target in COMPANY_ADMIN_CREATABLE
    if actor.role == UserRole.company_engineer:
        return target in COMPANY_ENGINEER_CREATABLE
    if actor.role == UserRole.super_admin and not actor.is_platform_admin:
        return target not in {UserRole.super_admin, UserRole.super_user, UserRole.sw_dev}
    return False


def can_manage_tenant_users(actor: User) -> bool:
    return actor.role in TENANT_ADMIN_ROLES or is_platform_staff(actor)


def tenant_admin_roles_for_require() -> tuple[UserRole, ...]:
    """Roles accepted by require_roles for tenant-admin endpoints."""
    return tuple(TENANT_ADMIN_ROLES)


def operations_roles_for_require() -> tuple[UserRole, ...]:
    return tuple(TENANT_OPERATIONS_ROLES)
