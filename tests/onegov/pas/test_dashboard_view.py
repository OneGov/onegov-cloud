from onegov.pas.collections import PASParliamentarianCollection
import transaction
from tests.onegov.pas.conftest import DummyApp


def test_view_dashboard_as_parliamentarian(client, session):
    # Create a parliamentarian
    parliamentarians = PASParliamentarianCollection(DummyApp(session=session))
    parliamentarians.add(
        first_name='Pia',
        last_name='Parliamentarian',
        email_primary='pia.parliamentarian@example.org'
    )
    transaction.commit()

    # The user is created with password 'test' by default in debug
    client.login('pia.parliamentarian@example.org', 'test')

    # Access the dashboard
    page = client.get('/pas')
    assert page.status_code == 200
    assert 'Dashboard' in page
