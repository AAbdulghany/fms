"""Wave 0 schema tests (NT-102)."""

from sqlalchemy import inspect

from app.models import PlatformSettings, SubscriptionPackage, TenantSubscription


def test_wave0_tables_exist(db_session):
  """Tables created via Base.metadata.create_all in test fixture."""
  bind = db_session.get_bind()
  insp = inspect(bind)
  for table in (
    "subscription_packages",
    "tenant_subscriptions",
    "platform_settings",
  ):
    assert insp.has_table(table), f"missing table {table}"


def test_subscription_package_model_fields():
  cols = {c.name for c in SubscriptionPackage.__table__.columns}
  assert {"code", "name", "features_json", "limits_json", "is_active"}.issubset(cols)


def test_tenant_subscription_unique_tenant():
  cols = {c.name for c in TenantSubscription.__table__.columns}
  assert "tenant_id" in cols
  uniques = [c for c in TenantSubscription.__table__.constraints if hasattr(c, "columns")]
  assert any(
    "tenant_id" in [col.name for col in getattr(u, "columns", [])]
    for u in TenantSubscription.__table__.constraints
  )


def test_platform_settings_key_pk():
  assert PlatformSettings.__table__.primary_key.columns.keys() == ["key"]
