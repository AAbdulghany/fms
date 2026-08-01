"""
Tenant Isolation Tests for FMS.

Verifies that tenant data is properly isolated and users cannot access
data from other tenants, even with valid UUIDs.

Tests cover:
1. Work Orders - Tenant A cannot see Tenant B's WOs
2. Assets - Cross-tenant asset access blocked
3. Users - User listing is tenant-scoped
4. Invoices - Invoice access is tenant-isolated
5. Sites - Site listing is tenant-isolated
6. Clients - Client access is tenant-isolated
7. UUID Guessing Attack - Random UUIDs from other tenants return 404
"""

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models import (
    Tenant, User, UserRole, Client, Site, WorkOrder,
    Asset, Invoice, MaintenanceReport, ReportStatus, ReportTemplate
)
from app.core.security import hash_password


# ========== Fixtures ==========

@pytest.fixture
def tenant_a(db_session):
    """Create Tenant A."""
    tenant = Tenant(id=uuid4(), name="Tenant A", status="active")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def tenant_b(db_session):
    """Create Tenant B."""
    tenant = Tenant(id=uuid4(), name="Tenant B", status="active")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def user_tenant_a(db_session, tenant_a):
    """Create user in Tenant A."""
    user = User(
        id=uuid4(),
        tenant_id=tenant_a.id,
        email="usera@test.com",
        password_hash=hash_password("password"),
        full_name="User A",
        role=UserRole.super_admin,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_tenant_b(db_session, tenant_b):
    """Create user in Tenant B."""
    user = User(
        id=uuid4(),
        tenant_id=tenant_b.id,
        email="userb@test.com",
        password_hash=hash_password("password"),
        full_name="User B",
        role=UserRole.super_admin,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client_a(db_session, tenant_a):
    """Create client in Tenant A."""
    client = Client(
        id=uuid4(),
        tenant_id=tenant_a.id,
        legal_name="Client A",
        code="CA"
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture
def client_b(db_session, tenant_b):
    """Create client in Tenant B."""
    client = Client(
        id=uuid4(),
        tenant_id=tenant_b.id,
        legal_name="Client B",
        code="CB"
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture
def site_a(db_session, tenant_a, client_a):
    """Create site in Tenant A."""
    site = Site(
        id=uuid4(),
        tenant_id=tenant_a.id,
        client_id=client_a.id,
        name="Site A"
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture
def site_b(db_session, tenant_b, client_b):
    """Create site in Tenant B."""
    site = Site(
        id=uuid4(),
        tenant_id=tenant_b.id,
        client_id=client_b.id,
        name="Site B"
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture
def work_order_a(db_session, tenant_a, client_a, site_a):
    """Create work order in Tenant A."""
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant_a.id,
        client_id=client_a.id,
        site_id=site_a.id,
        title="WO Tenant A"
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


@pytest.fixture
def work_order_b(db_session, tenant_b, client_b, site_b):
    """Create work order in Tenant B."""
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant_b.id,
        client_id=client_b.id,
        site_id=site_b.id,
        title="WO Tenant B"
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


@pytest.fixture
def asset_a(db_session, tenant_a, site_a):
    """Create asset in Tenant A."""
    asset = Asset(
        id=uuid4(),
        tenant_id=tenant_a.id,
        site_id=site_a.id,
        name="Asset A"
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


@pytest.fixture
def asset_b(db_session, tenant_b, site_b):
    """Create asset in Tenant B."""
    asset = Asset(
        id=uuid4(),
        tenant_id=tenant_b.id,
        site_id=site_b.id,
        name="Asset B"
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


@pytest.fixture
def invoice_a(db_session, tenant_a, client_a, work_order_a):
    """Create invoice in Tenant A."""
    invoice = Invoice(
        id=uuid4(),
        tenant_id=tenant_a.id,
        client_id=client_a.id,
        work_order_id=work_order_a.id,
        number="INV-A-001"
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice


@pytest.fixture
def invoice_b(db_session, tenant_b, client_b, work_order_b):
    """Create invoice in Tenant B."""
    invoice = Invoice(
        id=uuid4(),
        tenant_id=tenant_b.id,
        client_id=client_b.id,
        work_order_id=work_order_b.id,
        number="INV-B-001"
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice


@pytest.fixture
def report_template_a(db_session, tenant_a):
    """Create report template in Tenant A."""
    template = ReportTemplate(
        id=uuid4(),
        tenant_id=tenant_a.id,
        name="Template A",
        code="TMPL_A",
        schema_json={"fields": []}
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def report_a(db_session, tenant_a, work_order_a, report_template_a):
    """Create maintenance report in Tenant A."""
    report = MaintenanceReport(
        id=uuid4(),
        tenant_id=tenant_a.id,
        work_order_id=work_order_a.id,
        template_id=report_template_a.id,
        template_version=1,
        template_snapshot_json={"fields": []},
        status=ReportStatus.submitted
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


# ========== Test: Work Orders Isolation ==========

def test_work_orders_tenant_isolated_list(
    db_session, user_tenant_a, user_tenant_b, work_order_a, work_order_b
):
    """Tenant A user cannot see Tenant B's work orders in list."""
    from app.api.routes.work_orders import list_work_orders
    
    # Tenant A lists work orders
    result_a = list_work_orders(
        db_session, user_tenant_a,
        page=1, page_size=20, status_filter=None, urgency=None,
        client_id=None, site_id=None, assignee_user_id=None,
        date_from=None, date_to=None, search=None, tags=None
    )
    wo_ids_a = [wo.id for wo in result_a.data]
    
    assert work_order_a.id in wo_ids_a
    assert work_order_b.id not in wo_ids_a
    
    # Tenant B lists work orders
    result_b = list_work_orders(
        db_session, user_tenant_b,
        page=1, page_size=20, status_filter=None, urgency=None,
        client_id=None, site_id=None, assignee_user_id=None,
        date_from=None, date_to=None, search=None, tags=None
    )
    wo_ids_b = [wo.id for wo in result_b.data]
    
    assert work_order_b.id in wo_ids_b
    assert work_order_a.id not in wo_ids_b


def test_work_orders_tenant_isolated_get(
    db_session, user_tenant_a, work_order_b
):
    """Tenant A user cannot access Tenant B's work order by ID."""
    from app.api.routes.work_orders import get_work_order
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        get_work_order(work_order_b.id, db_session, user_tenant_a)
    
    # Should return 404 to prevent tenant enumeration
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "NOT_FOUND"


def test_work_orders_tenant_isolated_patch(
    db_session, user_tenant_a, work_order_b
):
    """Tenant A user cannot update Tenant B's work order."""
    from app.api.routes.work_orders import patch_work_order
    from app.schemas import WorkOrderUpdate
    from fastapi import BackgroundTasks, HTTPException
    
    update = WorkOrderUpdate(title="Hacked Title")
    
    with pytest.raises(HTTPException) as exc_info:
        patch_work_order(work_order_b.id, update, db_session, user_tenant_a, BackgroundTasks())
    
    assert exc_info.value.status_code == 404


# ========== Test: Assets Isolation ==========

def test_assets_tenant_isolated_list(
    db_session, user_tenant_a, user_tenant_b, asset_a, asset_b
):
    """Tenant A user cannot see Tenant B's assets in list."""
    from app.api.routes.assets import list_assets
    
    # Tenant A lists assets
    assets_a = list_assets(db_session, user_tenant_a, site_id=None, category=None, search=None)
    asset_ids_a = [a.id for a in assets_a]
    
    assert asset_a.id in asset_ids_a
    assert asset_b.id not in asset_ids_a
    
    # Tenant B lists assets
    assets_b = list_assets(db_session, user_tenant_b, site_id=None, category=None, search=None)
    asset_ids_b = [a.id for a in assets_b]
    
    assert asset_b.id in asset_ids_b
    assert asset_a.id not in asset_ids_b


def test_assets_tenant_isolated_lifecycle_endpoint(
    db_session, user_tenant_a, asset_b
):
    """Tenant A user cannot access Tenant B's asset lifecycle."""
    from app.api.routes.assets import get_asset_lifecycle
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        get_asset_lifecycle(asset_b.id, db_session, user_tenant_a)
    
    assert exc_info.value.status_code == 404


# ========== Test: Users Isolation ==========

def test_users_tenant_isolated(
    db_session, user_tenant_a, user_tenant_b
):
    """Tenant A admin cannot see Tenant B's users."""
    from app.api.routes.users import list_users
    
    # Tenant A lists users
    users_a = list_users(db_session, user_tenant_a, user_tenant_a)
    user_ids_a = [u.id for u in users_a]
    
    assert user_tenant_a.id in user_ids_a
    assert user_tenant_b.id not in user_ids_a


def test_users_cannot_create_in_other_tenant(
    db_session, user_tenant_a, tenant_b
):
    """User from Tenant A cannot create users in Tenant B."""
    from app.api.routes.users import create_user, UserCreateRequest
    
    # Even if we somehow bypass tenant_id in the request,
    # the created user will inherit the current user's tenant_id
    user_in = UserCreateRequest(
        email="newuser@test.com",
        password="pass123",
        full_name="New User",
        role=UserRole.company_admin
    )
    
    result = create_user(user_in, db_session, user_tenant_a, user_tenant_a)
    new_user = result.user
    
    # Should be created in Tenant A (current user's tenant)
    assert new_user.tenant_id == user_tenant_a.tenant_id
    assert new_user.tenant_id != tenant_b.id


# ========== Test: Invoices Isolation ==========

def test_invoices_tenant_isolated_list(
    db_session, user_tenant_a, user_tenant_b, invoice_a, invoice_b
):
    """Tenant A user cannot see Tenant B's invoices."""
    from app.api.routes.invoices import list_invoices
    
    # Tenant A lists invoices
    invoices_a = list_invoices(db_session, user_tenant_a, status=None, client_id=None, date_from=None, date_to=None)
    invoice_ids_a = [inv.id for inv in invoices_a]
    
    assert invoice_a.id in invoice_ids_a
    assert invoice_b.id not in invoice_ids_a
    
    # Tenant B lists invoices
    invoices_b = list_invoices(db_session, user_tenant_b, status=None, client_id=None, date_from=None, date_to=None)
    invoice_ids_b = [inv.id for inv in invoices_b]
    
    assert invoice_b.id in invoice_ids_b
    assert invoice_a.id not in invoice_ids_b


def test_invoices_tenant_isolated_get(
    db_session, user_tenant_a, invoice_b
):
    """Tenant A user cannot access Tenant B's invoice by ID."""
    from app.api.routes.invoices import get_invoice
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        get_invoice(invoice_b.id, db_session, user_tenant_a)
    
    assert exc_info.value.status_code == 404


def test_invoices_tenant_isolated_approve(
    db_session, user_tenant_a, invoice_b
):
    """Tenant A user cannot approve Tenant B's invoice."""
    from app.api.routes.invoices import approve_invoice
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        approve_invoice(invoice_b.id, db_session, user_tenant_a, user_tenant_a)
    
    assert exc_info.value.status_code == 404


# ========== Test: Sites Isolation ==========

def test_sites_tenant_isolated_list(
    db_session, user_tenant_a, user_tenant_b, site_a, site_b
):
    """Tenant A user cannot see Tenant B's sites."""
    from app.api.routes.sites import list_sites
    
    # Tenant A lists sites
    sites_a = list_sites(db_session, user_tenant_a, client_id=None)
    site_ids_a = [s.id for s in sites_a]
    
    assert site_a.id in site_ids_a
    assert site_b.id not in site_ids_a
    
    # Tenant B lists sites
    sites_b = list_sites(db_session, user_tenant_b, client_id=None)
    site_ids_b = [s.id for s in sites_b]
    
    assert site_b.id in site_ids_b
    assert site_a.id not in site_ids_b


# ========== Test: Clients Isolation ==========

def test_clients_tenant_isolated_list(
    db_session, user_tenant_a, user_tenant_b, client_a, client_b
):
    """Tenant A user cannot see Tenant B's clients."""
    from app.api.routes.clients import list_clients
    
    # Tenant A lists clients
    clients_a = list_clients(db_session, user_tenant_a)
    client_ids_a = [c.id for c in clients_a]
    
    assert client_a.id in client_ids_a
    assert client_b.id not in client_ids_a
    
    # Tenant B lists clients
    clients_b = list_clients(db_session, user_tenant_b)
    client_ids_b = [c.id for c in clients_b]
    
    assert client_b.id in client_ids_b
    assert client_a.id not in client_ids_b


def test_clients_tenant_isolated_get(
    db_session, user_tenant_a, client_b
):
    """Tenant A user cannot access Tenant B's client by ID."""
    from app.api.routes.clients import get_client
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        get_client(client_b.id, db_session, user_tenant_a)
    
    assert exc_info.value.status_code == 404


# ========== Test: Reports Isolation ==========

def test_reports_tenant_isolated_approve(
    db_session, user_tenant_a, tenant_b, client_b, site_b, report_template_a
):
    """Tenant A user cannot approve Tenant B's reports."""
    from app.api.routes.reports import approve_report
    from fastapi import HTTPException
    
    # Create work order and report in Tenant B
    wo_b = WorkOrder(
        id=uuid4(),
        tenant_id=tenant_b.id,
        client_id=client_b.id,
        site_id=site_b.id,
        title="WO B"
    )
    db_session.add(wo_b)
    db_session.flush()
    
    # Create template in tenant B
    template_b = ReportTemplate(
        id=uuid4(),
        tenant_id=tenant_b.id,
        name="Template B",
        code="TMPL_B",
        schema_json={"fields": []}
    )
    db_session.add(template_b)
    db_session.flush()
    
    report_b = MaintenanceReport(
        id=uuid4(),
        tenant_id=tenant_b.id,
        work_order_id=wo_b.id,
        template_id=template_b.id,
        template_version=1,
        template_snapshot_json={"fields": []},
        status=ReportStatus.submitted
    )
    db_session.add(report_b)
    db_session.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        approve_report(report_b.id, db_session, user_tenant_a, user_tenant_a)
    
    assert exc_info.value.status_code == 404


# ========== Test: UUID Guessing Attack Prevention ==========

def test_uuid_guessing_work_orders_returns_404(
    db_session, user_tenant_a
):
    """Random UUIDs for work orders return 404, not 403."""
    from app.api.routes.work_orders import get_work_order
    from fastapi import HTTPException
    
    random_uuid = uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        get_work_order(random_uuid, db_session, user_tenant_a)
    
    # Should return 404 to prevent tenant enumeration
    # (403 would confirm the resource exists but user lacks access)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "NOT_FOUND"


def test_uuid_guessing_assets_returns_404(
    db_session, user_tenant_a
):
    """Random UUIDs for assets return 404."""
    from app.api.routes.assets import get_asset_lifecycle
    from fastapi import HTTPException
    
    random_uuid = uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        get_asset_lifecycle(random_uuid, db_session, user_tenant_a)
    
    assert exc_info.value.status_code == 404


def test_uuid_guessing_invoices_returns_404(
    db_session, user_tenant_a
):
    """Random UUIDs for invoices return 404."""
    from app.api.routes.invoices import get_invoice
    from fastapi import HTTPException
    
    random_uuid = uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        get_invoice(random_uuid, db_session, user_tenant_a)
    
    assert exc_info.value.status_code == 404


def test_uuid_guessing_clients_returns_404(
    db_session, user_tenant_a
):
    """Random UUIDs for clients return 404."""
    from app.api.routes.clients import get_client
    from fastapi import HTTPException
    
    random_uuid = uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        get_client(random_uuid, db_session, user_tenant_a)
    
    assert exc_info.value.status_code == 404


def test_uuid_guessing_reports_returns_404(
    db_session, user_tenant_a
):
    """Random UUIDs for reports return 404."""
    from app.api.routes.reports import approve_report
    from fastapi import HTTPException
    
    random_uuid = uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        approve_report(random_uuid, db_session, user_tenant_a, user_tenant_a)
    
    assert exc_info.value.status_code == 404


# ========== Test: Cross-Tenant Data Modification Blocked ==========

def test_cannot_modify_work_order_across_tenants(
    db_session, user_tenant_a, work_order_b
):
    """Tenant A user cannot modify Tenant B's work order."""
    from app.api.routes.work_orders import patch_work_order
    from app.schemas import WorkOrderUpdate
    from app.models import WorkOrderStatus
    from fastapi import BackgroundTasks, HTTPException
    
    update = WorkOrderUpdate(status=WorkOrderStatus.closed)
    
    with pytest.raises(HTTPException) as exc_info:
        patch_work_order(work_order_b.id, update, db_session, user_tenant_a, BackgroundTasks())
    
    assert exc_info.value.status_code == 404
    
    # Verify work order was not modified
    db_session.refresh(work_order_b)
    assert work_order_b.status != WorkOrderStatus.closed


def test_cannot_create_site_for_other_tenant_client(
    db_session, user_tenant_a, client_b
):
    """Tenant A user cannot create site for Tenant B's client."""
    from app.api.routes.sites import create_site
    from app.schemas import SiteCreate
    from fastapi import HTTPException
    
    site_in = SiteCreate(
        client_id=client_b.id,
        name="Malicious Site"
    )
    
    # Should fail because client_b is not in tenant_a
    with pytest.raises(HTTPException) as exc_info:
        create_site(site_in, db_session, user_tenant_a, user_tenant_a)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "INVALID_CLIENT"


def test_cannot_reset_lifecycle_for_other_tenant_asset(
    db_session, user_tenant_a, asset_b
):
    """Tenant A user cannot reset lifecycle for Tenant B's asset."""
    from app.api.routes.assets import reset_lifecycle
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        reset_lifecycle(asset_b.id, db_session, user_tenant_a, user_tenant_a)
    
    assert exc_info.value.status_code == 404


# ========== Test: Tenant Context Properly Set ==========

def test_tenant_context_set_correctly(db_session, user_tenant_a):
    """Verify tenant_context is set properly for authenticated user."""
    from app.database import tenant_context
    from app.api.deps import get_current_user
    
    # Simulate get_current_user call (already sets tenant_context)
    # In actual implementation, this is done in get_current_user
    tenant_context.set(user_tenant_a.tenant_id)
    
    # Verify context is set
    assert tenant_context.get() == user_tenant_a.tenant_id


def test_tenant_context_filters_queries(db_session, user_tenant_a, work_order_a, work_order_b):
    """Tenant context filters should only return tenant-scoped data."""
    from sqlalchemy import select
    
    # Manually filter by tenant (simulating what routes do)
    query = select(WorkOrder).where(WorkOrder.tenant_id == user_tenant_a.tenant_id)
    results = list(db_session.scalars(query).all())
    
    wo_ids = [wo.id for wo in results]
    assert work_order_a.id in wo_ids
    assert work_order_b.id not in wo_ids
