from onegov.pas.collections import (
    RateSetCollection,
    SettlementRunCollection,
    ImportLogCollection
)
from onegov.user import UserCollection
import transaction
import pytest
from datetime import date


@pytest.mark.parametrize('role,user_email,should_access', [
    ('parliamentarian', 'test.parliamentarian@example.org', False),
    ('commission_president', 'test.president@example.org', False),
    ('admin', 'test.admin@example.org', True),
])
@pytest.mark.parametrize('path', [
    '/rate-sets',
    '/settlement-runs',
    '/import-logs',
    '/usermanagement'
])
def test_admin_only_collection_access(
    client, role, user_email, should_access, path
):
    session = client.app.session()

    # Create user with specified role
    users = UserCollection(session)
    user = users.add(
        username=user_email,
        password='test',
        role=role
    )
    transaction.commit()

    # Login and test access
    client.login(user_email, 'test')
    page = client.get(path, expect_errors=True)

    if should_access:
        assert page.status_code == 200
    else:
        assert page.status_code in (403, 302)  # Forbidden or redirect


@pytest.mark.parametrize('role,user_email', [
    ('parliamentarian', 'test.parliamentarian@example.org'),
    ('commission_president', 'test.president@example.org'),
])
def test_admin_only_individual_items_denied(client, role, user_email):
    '''Individual admin-only items should deny access to parliamentarians'''
    session = client.app.session()

    # Create test data as admin would
    rate_sets = RateSetCollection(session)
    rate_set = rate_sets.add(year=2025)

    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Test Settlement Run',
        start=date.today(),
        end=date.today(),
        active=True
    )

    import_logs = ImportLogCollection(session)
    import_log = import_logs.add(
        details={'filename': 'test_import.csv'},
        status='completed',
        import_type='upload'
    )

    # Get IDs before creating users
    rate_set_id = rate_set.id
    settlement_run_id = settlement_run.id
    import_log_id = import_log.id

    # Create user with specified role
    users = UserCollection(session)
    user = users.add(
        username=user_email,
        password='test',
        role=role
    )
    transaction.commit()

    # Test individual item access
    client.login(user_email, 'test')

    # Test with actual IDs from created objects
    admin_paths = [
        f'/rate-set/{rate_set_id}',
        f'/settlement-run/{settlement_run_id}',
        f'/import-log/{import_log_id}'
    ]

    for path in admin_paths:
        page = client.get(path, expect_errors=True)
        assert page.status_code in (403, 302)


def test_admin_can_access_admin_only_items(client):
    session = client.app.session()

    # Create test data
    rate_sets = RateSetCollection(session)
    rate_set = rate_sets.add(year=2025)

    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Admin Test Settlement Run',
        start=date.today(),
        end=date.today(),
        active=True
    )

    import_logs = ImportLogCollection(session)
    import_log = import_logs.add(
        details={'filename': 'admin_test_import.csv'},
        status='completed',
        import_type='upload'
    )

    # Get IDs
    rate_set_id = rate_set.id
    settlement_run_id = settlement_run.id
    import_log_id = import_log.id

    # Create admin user
    users = UserCollection(session)
    admin_user = users.add(
        username='test.admin2@example.org',
        password='test',
        role='admin'
    )
    transaction.commit()

    # Login as admin and verify access
    client.login('test.admin2@example.org', 'test')

    # Test collections
    admin_collection_paths = [
        '/rate-sets',
        '/settlement-runs',
        '/import-logs'
    ]

    for path in admin_collection_paths:
        page = client.get(path)
        assert page.status_code == 200

    # Test individual items
    admin_item_paths = [
        f'/rate-set/{rate_set_id}',
        f'/settlement-run/{settlement_run_id}',
        f'/import-log/{import_log_id}'
    ]

    for path in admin_item_paths:
        page = client.get(path)
        assert page.status_code == 200
