"""Billing setup backfill tests."""

from uuid import uuid4

import pytest

from app.models import Client, Tenant
from app.services.billing_setup import ensure_all_clients_have_contracts, ensure_client_active_contract


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="Billing Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    return t


def test_ensure_client_active_contract_creates_profile_and_contract(db_session, tenant):
    client = Client(id=uuid4(), tenant_id=tenant.id, legal_name="Acme", code="ACME")
    db_session.add(client)
    db_session.commit()

    contract = ensure_client_active_contract(db_session, tenant.id, client.id)
    assert contract.status == "active"
    assert contract.client_id == client.id

    again = ensure_client_active_contract(db_session, tenant.id, client.id)
    assert again.id == contract.id


def test_ensure_all_clients_have_contracts_backfills(db_session, tenant):
    c1 = Client(id=uuid4(), tenant_id=tenant.id, legal_name="A", code="A1")
    c2 = Client(id=uuid4(), tenant_id=tenant.id, legal_name="B", code="B1")
    db_session.add_all([c1, c2])
    db_session.commit()

    created = ensure_all_clients_have_contracts(db_session)
    assert created == 2

    created_again = ensure_all_clients_have_contracts(db_session)
    assert created_again == 0
