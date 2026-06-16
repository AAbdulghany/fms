"""Phase 3.1 subscription enforcement tests (legacy JSON path)."""

from app.services.subscription import get_subscription, is_subscription_active, update_subscription


def test_default_subscription_active(db_session, sample_tenant):
    assert is_subscription_active(db_session, sample_tenant) is True
    sub = get_subscription(db_session, sample_tenant)
    assert sub["status"] == "active"


def test_suspended_subscription_blocks(db_session, sample_tenant, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    update_subscription(db_session, sample_tenant, {"status": "suspended"})
    db_session.commit()
    db_session.refresh(sample_tenant)
    assert is_subscription_active(db_session, sample_tenant) is False

    update_subscription(db_session, sample_tenant, {"status": "active"})
    db_session.commit()
    assert is_subscription_active(db_session, sample_tenant) is True

    get_settings.cache_clear()
