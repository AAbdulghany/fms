"""NT-131: API error handler returns bilingual user messages."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_error_handler_expands_string_code():
    # Trigger 401 with invalid login — uses INVALID_CREDENTIALS
    res = client.post("/api/v1/auth/login", json={"email": "nope@test.com", "password": "wrong"})
    assert res.status_code == 401
    detail = res.json()["detail"]
    assert detail["code"] == "INVALID_CREDENTIALS"
    assert "message_en" in detail
    assert "message_ar" in detail
    assert "Invalid email" in detail["message_en"]


def test_error_handler_expands_feature_gate(api_client, db_session, sample_tenant, monkeypatch):
    from uuid import uuid4

    from app.config import get_settings
    from app.core.security import hash_password
    from app.models import SubscriptionPackage, TenantSubscription, User, UserRole

    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="gate@test.com",
        password_hash=hash_password("pass123"),
        full_name="Gate",
        role=UserRole.company_admin,
        is_active=True,
    )
    pkg = SubscriptionPackage(
        code="assets_only",
        name="Assets Only",
        features_json=["assets"],
        limits_json={"max_users": 5},
        is_active=True,
    )
    db_session.add_all([user, pkg])
    db_session.flush()
    db_session.add(
        TenantSubscription(tenant_id=sample_tenant.id, package_id=pkg.id, status="active")
    )
    db_session.commit()

    from tests.api_helpers import auth_header

    res = api_client.get("/api/v1/invoices", headers=auth_header(user))
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["code"] == "FEATURE_NOT_AVAILABLE"
    assert "subscription" in detail["message_en"].lower()

    get_settings.cache_clear()
