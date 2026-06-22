"""Phase 3.1 notification persistence tests."""

from uuid import uuid4

from app.models import User, UserRole
from app.services.notification_service import create_notification, list_notifications, mark_all_read, mark_read


def test_create_and_list_notifications(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="n@test.com",
        full_name="Notifier",
        role=UserRole.company_admin,
        password_hash="x",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    create_notification(
        db_session,
        tenant_id=sample_tenant.id,
        user_id=user.id,
        type="work_order.requested",
        title="New request",
        payload={"work_order_id": str(uuid4()), "action": "review_request"},
    )
    db_session.commit()

    rows = list_notifications(db_session, user.id, sample_tenant.id)
    assert len(rows) == 1
    assert rows[0].type == "work_order.requested"
    assert rows[0].read_at is None


def test_mark_read_and_mark_all(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="n2@test.com",
        full_name="Notifier2",
        role=UserRole.company_admin,
        password_hash="x",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    n1 = create_notification(
        db_session,
        tenant_id=sample_tenant.id,
        user_id=user.id,
        type="test",
        title="One",
    )
    create_notification(
        db_session,
        tenant_id=sample_tenant.id,
        user_id=user.id,
        type="test",
        title="Two",
    )
    db_session.commit()

    mark_read(db_session, user.id, sample_tenant.id, n1.id)
    db_session.commit()
    rows = list_notifications(db_session, user.id, sample_tenant.id)
    read_count = sum(1 for r in rows if r.read_at is not None)
    assert read_count == 1

    mark_all_read(db_session, user.id, sample_tenant.id)
    db_session.commit()
    rows = list_notifications(db_session, user.id, sample_tenant.id)
    assert all(r.read_at is not None for r in rows)
