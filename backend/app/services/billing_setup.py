"""Ensure clients have pricing profiles and active contracts for invoicing."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, Contract, PricingProfile

DEFAULT_PROFILE_NAME = "Standard rates"
DEFAULT_CONTRACT_NAME = "Default service contract"


def ensure_tenant_pricing_profile(db: Session, tenant_id: UUID) -> PricingProfile:
    profile = db.scalar(
        select(PricingProfile)
        .where(PricingProfile.tenant_id == tenant_id, PricingProfile.name == DEFAULT_PROFILE_NAME)
        .limit(1)
    )
    if profile:
        return profile
    profile = PricingProfile(
        tenant_id=tenant_id,
        name=DEFAULT_PROFILE_NAME,
        hourly_rate_sar=150,
        parts_markup_percent=15,
        default_service_fee_sar=50,
        emergency_surcharge_percent=25,
    )
    db.add(profile)
    db.flush()
    return profile


def ensure_client_active_contract(db: Session, tenant_id: UUID, client_id: UUID) -> Contract:
    existing = db.scalar(
        select(Contract).where(
            Contract.tenant_id == tenant_id,
            Contract.client_id == client_id,
            Contract.status == "active",
        )
    )
    if existing:
        return existing

    profile = ensure_tenant_pricing_profile(db, tenant_id)
    contract = Contract(
        tenant_id=tenant_id,
        client_id=client_id,
        pricing_profile_id=profile.id,
        name=DEFAULT_CONTRACT_NAME,
        currency="SAR",
        status="active",
    )
    db.add(contract)
    db.flush()
    return contract


def ensure_all_clients_have_contracts(db: Session) -> int:
    """Backfill active contracts for every client missing one. Returns count created."""
    created = 0
    clients = list(db.scalars(select(Client)).all())
    for client in clients:
        has = db.scalar(
            select(Contract.id).where(
                Contract.tenant_id == client.tenant_id,
                Contract.client_id == client.id,
                Contract.status == "active",
            )
        )
        if not has:
            ensure_client_active_contract(db, client.tenant_id, client.id)
            created += 1
    return created
