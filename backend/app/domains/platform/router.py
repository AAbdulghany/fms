"""Platform administration routes (Wave 1) — SW staff only."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.config import get_settings
from app.core.security import hash_password
from app.database import get_db
from app.models import Client, SubscriptionPackage, Tenant, User, UserRole
from app.rbac import PLATFORM_TENANT_USER_CREATABLE, can_create_role
from app.schemas import (
    MaintenanceCompanyOut,
    PlatformClientBrief,
    PlatformClientCreate,
    PlatformUserCreate,
    PlatformUserCreateOut,
    SubscriptionPackageCreate,
    SubscriptionPackageOut,
    SubscriptionPackageUpdate,
    SubscriptionOut,
    TenantBriefOut,
    TenantLicenseAssign,
    TenantProvisionBody,
    TenantProvisionOut,
)
from app.services.audit import write_audit
from app.services.provisioning import generate_initial_password, next_client_code
from app.services.subscription import assign_tenant_subscription, get_subscription

router = APIRouter(prefix="/platform", tags=["platform"])

_platform = Depends(require_platform_admin())


@router.get("/tenants", response_model=list[TenantBriefOut])
def list_tenants(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, _platform],
) -> list[Tenant]:
    return list(db.scalars(select(Tenant).order_by(Tenant.name)).all())


@router.get("/maintenance-companies", response_model=list[MaintenanceCompanyOut])
def list_maintenance_companies(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, _platform],
    search: str | None = None,
    status: str | None = None,
) -> list[MaintenanceCompanyOut]:
    """Platform view: maintenance companies (tenants) with nested end clients."""
    q = select(Tenant).order_by(Tenant.name)
    if status:
        q = q.where(Tenant.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(Tenant.name.ilike(like))
    tenants = list(db.scalars(q).all())
    out: list[MaintenanceCompanyOut] = []
    for tenant in tenants:
        clients = list(
            db.scalars(
                select(Client)
                .where(Client.tenant_id == tenant.id)
                .order_by(Client.legal_name)
            ).all()
        )
        sub = get_subscription(db, tenant)
        out.append(
            MaintenanceCompanyOut(
                id=tenant.id,
                name=tenant.name,
                status=tenant.status,
                client_count=len(clients),
                clients=[PlatformClientBrief.model_validate(c) for c in clients],
                subscription=SubscriptionOut.model_validate(sub),
            )
        )
    return out


@router.post("/tenants", response_model=TenantProvisionOut, status_code=status.HTTP_201_CREATED)
def provision_tenant(
    body: TenantProvisionBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> TenantProvisionOut:
    """Create maintenance company + company_admin + subscription (SW staff only)."""
    pkg = db.get(SubscriptionPackage, body.package_id)
    if not pkg or not pkg.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PACKAGE")

    tenant = Tenant(name=body.tenant_name.strip(), status="active")
    db.add(tenant)
    db.flush()

    auto_password: str | None = None
    if body.admin_password:
        pwd_hash = hash_password(body.admin_password)
    else:
        auto_password = generate_initial_password()
        pwd_hash = hash_password(auto_password)

    admin = User(
        tenant_id=tenant.id,
        email=body.admin_email.strip().lower(),
        password_hash=pwd_hash,
        full_name=body.admin_full_name.strip(),
        role=UserRole.company_admin,
        is_platform_admin=False,
        is_active=True,
        metadata_json={"must_change_password": auto_password is not None},
    )
    db.add(admin)
    db.flush()

    assign_tenant_subscription(
        db,
        tenant,
        package_id=body.package_id,
        status=body.license_status,
        valid_until=body.valid_until,
    )
    write_audit(
        db,
        tenant_id=tenant.id,
        actor=current,
        action="provision_tenant",
        entity_type="tenant",
        entity_id=str(tenant.id),
    )
    db.commit()
    db.refresh(tenant)
    db.refresh(admin)
    return TenantProvisionOut(
        tenant_id=tenant.id,
        admin_user_id=admin.id,
        initial_password=auto_password,
        subscription=SubscriptionOut.model_validate(get_subscription(db, tenant)),
    )


@router.post(
    "/tenants/{tenant_id}/clients",
    response_model=PlatformClientBrief,
    status_code=status.HTTP_201_CREATED,
)
def platform_create_client(
    tenant_id: UUID,
    body: PlatformClientCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> Client:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    code = body.code or next_client_code(db, tenant_id)
    client = Client(
        tenant_id=tenant_id,
        legal_name=body.legal_name.strip(),
        code=code,
        billing_email=body.billing_email,
        status="active",
        activity_type=body.activity_type,
    )
    db.add(client)
    write_audit(
        db,
        tenant_id=tenant_id,
        actor=current,
        action="platform_create_client",
        entity_type="client",
        entity_id=code,
    )
    db.commit()
    db.refresh(client)
    return client


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=PlatformUserCreateOut,
    status_code=status.HTTP_201_CREATED,
)
def platform_create_user(
    tenant_id: UUID,
    body: PlatformUserCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> PlatformUserCreateOut:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if body.role not in PLATFORM_TENANT_USER_CREATABLE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ROLE_NOT_ALLOWED")
    if not can_create_role(current, body.role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    existing = db.scalar(
        select(User).where(User.tenant_id == tenant_id, User.email == body.email.strip().lower())
    )
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="EMAIL_ALREADY_IN_USE")

    auto_password: str | None = None
    if body.password:
        pwd_hash = hash_password(body.password)
    else:
        auto_password = generate_initial_password()
        pwd_hash = hash_password(auto_password)

    user = User(
        tenant_id=tenant_id,
        email=body.email.strip().lower(),
        password_hash=pwd_hash,
        full_name=body.full_name.strip(),
        role=body.role,
        client_id=body.client_id,
        is_platform_admin=False,
        is_active=True,
        metadata_json={"must_change_password": auto_password is not None},
    )
    db.add(user)
    write_audit(
        db,
        tenant_id=tenant_id,
        actor=current,
        action="platform_create_user",
        entity_type="user",
        entity_id=body.email,
    )
    db.commit()
    db.refresh(user)
    return PlatformUserCreateOut(user_id=user.id, initial_password=auto_password)


@router.get("/packages", response_model=list[SubscriptionPackageOut])
def list_packages(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, _platform],
    active_only: bool = False,
) -> list[SubscriptionPackage]:
    q = select(SubscriptionPackage).order_by(SubscriptionPackage.code)
    if active_only:
        q = q.where(SubscriptionPackage.is_active.is_(True))
    return list(db.scalars(q).all())


@router.post("/packages", response_model=SubscriptionPackageOut, status_code=status.HTTP_201_CREATED)
def create_package(
    body: SubscriptionPackageCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> SubscriptionPackage:
    existing = db.scalar(select(SubscriptionPackage).where(SubscriptionPackage.code == body.code))
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="CODE_EXISTS")
    row = SubscriptionPackage(
        code=body.code.strip().lower(),
        name=body.name,
        features_json=list(body.features_json),
        limits_json=dict(body.limits_json),
        is_active=body.is_active,
    )
    db.add(row)
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="subscription_package",
        entity_id=body.code,
    )
    db.commit()
    db.refresh(row)
    return row


@router.get("/packages/{package_id}", response_model=SubscriptionPackageOut)
def get_package(
    package_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, _platform],
) -> SubscriptionPackage:
    row = db.get(SubscriptionPackage, package_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return row


@router.patch("/packages/{package_id}", response_model=SubscriptionPackageOut)
def update_package(
    package_id: UUID,
    body: SubscriptionPackageUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> SubscriptionPackage:
    row = db.get(SubscriptionPackage, package_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="subscription_package",
        entity_id=str(package_id),
    )
    db.commit()
    db.refresh(row)
    return row


@router.delete("/packages/{package_id}", response_model=SubscriptionPackageOut)
def deactivate_package(
    package_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> SubscriptionPackage:
    row = db.get(SubscriptionPackage, package_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


@router.get("/tenants/{tenant_id}/license", response_model=SubscriptionOut)
def read_tenant_license(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, _platform],
) -> SubscriptionOut:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return SubscriptionOut.model_validate(get_subscription(db, tenant))


@router.put("/tenants/{tenant_id}/license", response_model=SubscriptionOut)
def assign_tenant_license(
    tenant_id: UUID,
    body: TenantLicenseAssign,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> SubscriptionOut:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    try:
        assign_tenant_subscription(
            db,
            tenant,
            package_id=body.package_id,
            status=body.status,
            valid_until=body.valid_until,
            overrides_json=body.overrides_json or {},
        )
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PACKAGE")
    write_audit(
        db,
        tenant_id=tenant.id,
        actor=current,
        action="assign_license",
        entity_type="tenant_subscription",
        entity_id=str(tenant.id),
    )
    db.commit()
    return SubscriptionOut.model_validate(get_subscription(db, tenant))


@router.post("/demo/reset")
def demo_reset(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, _platform],
) -> dict[str, str]:
    if get_settings().app_env.lower() != "demo":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="DEMO_ENV_ONLY")
    from app.pitch_seed import seed_pitch_demo

    info = seed_pitch_demo(db)
    actor = db.scalar(select(User).where(User.email == "super@demo.com"))
    if actor:
        write_audit(
            db,
            tenant_id=actor.tenant_id,
            actor=actor,
            action="demo_reset",
            entity_type="platform",
            entity_id="demo",
        )
    db.commit()
    return {"status": "ok", "message": "Demo database reset complete", **info}
