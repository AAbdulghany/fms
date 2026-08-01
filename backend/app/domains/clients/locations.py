"""P2-F5: Hierarchical locations under sites."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Location, Site, User, UserRole, UserSiteScope
from app.schemas import LocationCreate, LocationOut, LocationTreeNode, LocationUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/locations", tags=["locations"])

_roles = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.client_admin,
        UserRole.site_manager,
    )
)


def _ensure_site(
    db: Session,
    current: User,
    site_id: UUID,
) -> Site:
    site = db.get(Site, site_id)
    if not site or site.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.client_admin and current.client_id and site.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = list(
            db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        )
        if site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return site


def _ensure_location(db: Session, current: User, loc_id: UUID) -> Location:
    loc = db.get(Location, loc_id)
    if not loc or loc.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    _ensure_site(db, current, loc.site_id)
    return loc


def _build_tree(nodes: list[Location]) -> list[LocationTreeNode]:
    by_parent: dict[UUID | None, list[Location]] = {}
    for n in sorted(nodes, key=lambda x: (x.sort_order, x.name)):
        by_parent.setdefault(n.parent_id, []).append(n)

    def walk(parent: UUID | None) -> list[LocationTreeNode]:
        out: list[LocationTreeNode] = []
        for n in by_parent.get(parent, []):
            out.append(
                LocationTreeNode(
                    id=n.id,
                    site_id=n.site_id,
                    parent_id=n.parent_id,
                    name=n.name,
                    location_type=n.location_type,
                    sort_order=n.sort_order,
                    children=walk(n.id),
                )
            )
        return out

    return walk(None)


@router.get("", response_model=list[LocationOut])
def list_locations(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _roles],
    site_id: UUID = Query(..., description="Site to list locations for"),
) -> list[Location]:
    _ensure_site(db, current, site_id)
    q = select(Location).where(Location.tenant_id == current.tenant_id, Location.site_id == site_id)
    return list(db.scalars(q.order_by(Location.sort_order, Location.name)).all())


@router.get("/tree", response_model=list[LocationTreeNode])
def location_tree(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _roles],
    site_id: UUID = Query(...),
) -> list[LocationTreeNode]:
    _ensure_site(db, current, site_id)
    nodes = list(
        db.scalars(
            select(Location).where(Location.tenant_id == current.tenant_id, Location.site_id == site_id)
        ).all()
    )
    return _build_tree(nodes)


@router.post("", response_model=LocationOut)
def create_location(
    body: LocationCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _roles],
) -> Location:
    site = _ensure_site(db, current, body.site_id)
    if body.parent_id:
        parent = db.get(Location, body.parent_id)
        if not parent or parent.site_id != site.id or parent.tenant_id != current.tenant_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PARENT")
    loc = Location(
        tenant_id=current.tenant_id,
        site_id=body.site_id,
        parent_id=body.parent_id,
        name=body.name,
        location_type=body.location_type,
        sort_order=body.sort_order,
        metadata_json=body.metadata_json,
    )
    db.add(loc)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="location",
        entity_id=str(loc.id),
        after={"name": loc.name, "site_id": str(loc.site_id)},
    )
    db.commit()
    db.refresh(loc)
    return loc


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(
    location_id: UUID,
    body: LocationUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _roles],
) -> Location:
    loc = _ensure_location(db, current, location_id)
    if body.parent_id is not None:
        if body.parent_id == loc.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PARENT")
        if body.parent_id:
            parent = db.get(Location, body.parent_id)
            if not parent or parent.site_id != loc.site_id or parent.tenant_id != current.tenant_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PARENT")
    if body.name is not None:
        loc.name = body.name
    if body.parent_id is not None:
        loc.parent_id = body.parent_id
    if body.location_type is not None:
        loc.location_type = body.location_type
    if body.sort_order is not None:
        loc.sort_order = body.sort_order
    if body.metadata_json is not None:
        loc.metadata_json = body.metadata_json
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _roles],
) -> None:
    loc = _ensure_location(db, current, location_id)
    child = db.scalars(select(Location.id).where(Location.parent_id == loc.id).limit(1)).first()
    if child:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="HAS_CHILDREN")
    db.delete(loc)
    db.commit()
