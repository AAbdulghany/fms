"""API client fixture for route integration tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture
def api_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def auth_header(user) -> dict[str, str]:
    from app.core.security import create_access_token

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
        is_platform_admin=user.is_platform_admin,
    )
    return {"Authorization": f"Bearer {token}"}


def assert_api_error(response, *, status: int, code: str) -> dict:
    """Assert NT-131 bilingual error shape (or legacy string detail)."""
    assert response.status_code == status
    detail = response.json()["detail"]
    if isinstance(detail, str):
        assert detail == code
        return {"code": code}
    assert detail["code"] == code
    assert "message_en" in detail
    assert "message_ar" in detail
    return detail
