from onegov.pas.models.parliamentarian import PASParliamentarian
from onegov.pas.collections import PASParliamentarianCollection
import transaction
from tests.onegov.pas.conftest import DummyApp


def test_view_dashboard_as_parliamentarian(client):
    session = client.app.session()
    transaction.begin()
    par = PASParliamentarian(
        first_name='Pia',
        last_name='Parliamentarian',
        email_primary='pia.parliamentarian@example.org'
    )
    session.add(par)
    transaction.commit()

    # The user is created with password 'test' by default in debug
    client.login('pia.parliamentarian@example.org', 'test')

    # Access the dashboard
    page = client.get('/pas')
    assert page.status_code == 200
    assert 'Dashboard' in page
