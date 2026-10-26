"""A2 — Mint / resolve opaque asset QR tags."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Client, Site
from app.models.asset_tags import AssetTag

# Crockford base32 alphabet (no I, L, O, U)
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
TOKEN_LEN = 12


def _new_token() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(TOKEN_LEN))


def public_tag_url(token: str) -> str:
    import os

    base = os.environ.get("PUBLIC_APP_URL", "").rstrip("/")
    if base:
        return f"{base}/a/{token}"
    return f"/a/{token}"


def absolute_qr_payload(payload: str | None, *, app_base: str | None = None) -> str:
    """Return an absolute URL suitable for QR encoding / print stickers.

    Relative ``/a/<token>`` payloads are prefixed with ``app_base`` (or PUBLIC_APP_URL).
    Already-absolute http(s) payloads are returned unchanged.
    """
    import os

    raw = (payload or "").strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    base = (app_base or os.environ.get("PUBLIC_APP_URL") or "").rstrip("/")
    path = raw if raw.startswith("/") else f"/{raw}"
    if base:
        return f"{base}{path}"
    return path


def get_active_tag(db: Session, asset_id: UUID) -> AssetTag | None:
    return db.scalar(
        select(AssetTag).where(
            AssetTag.asset_id == asset_id,
            AssetTag.status == "active",
        )
    )


def ensure_active_tag(db: Session, asset: Asset) -> AssetTag:
    existing = get_active_tag(db, asset.id)
    if existing:
        asset.qr_payload = public_tag_url(existing.token)
        return existing

    for _ in range(8):
        token = _new_token()
        clash = db.scalar(select(AssetTag).where(AssetTag.token == token))
        if clash:
            continue
        tag = AssetTag(
            tenant_id=asset.tenant_id,
            asset_id=asset.id,
            token=token,
            status="active",
        )
        db.add(tag)
        db.flush()
        asset.qr_payload = public_tag_url(token)
        return tag
    raise RuntimeError("Could not allocate unique asset tag token")


def revoke_and_mint(db: Session, asset: Asset) -> AssetTag:
    now = datetime.now(timezone.utc)
    for tag in db.scalars(
        select(AssetTag).where(AssetTag.asset_id == asset.id, AssetTag.status == "active")
    ).all():
        tag.status = "revoked"
        tag.revoked_at = now
    db.flush()
    return ensure_active_tag(db, asset)


def resolve_tag(db: Session, token: str) -> tuple[AssetTag, Asset, Site, Client | None]:
    cleaned = (token or "").strip().upper()
    tag = db.scalar(
        select(AssetTag).where(AssetTag.token == cleaned, AssetTag.status == "active")
    )
    if not tag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="TAG_NOT_FOUND")
    asset = db.get(Asset, tag.asset_id)
    if not asset or asset.tenant_id != tag.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="TAG_NOT_FOUND")
    site = db.get(Site, asset.site_id)
    if not site:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="TAG_NOT_FOUND")
    client = db.get(Client, site.client_id) if site.client_id else None
    return tag, asset, site, client
