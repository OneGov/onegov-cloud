import onegov.ticket
import transaction
import pytest

from onegov.org import OrgApp
from onegov.user import User
from onegov.org.initial_content import create_new_organisation
from onegov.testing.utils import create_app


@pytest.yield_fixture(scope='session')
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}


@pytest.yield_fixture(scope='function')
def org_app(request):
    yield create_org_app(request, use_elasticsearch=False)


@pytest.yield_fixture(scope='function')
def es_org_app(request):
    yield create_org_app(request, use_elasticsearch=True)


def create_org_app(request, use_elasticsearch):
    app = create_app(OrgApp, request, use_elasticsearch=use_elasticsearch)
    session = app.session()

    org = create_new_organisation(app, name="Govikon")
    org.meta['reply_to'] = 'mails@govikon.ch'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.
    test_password = request.getfixturevalue('test_password')

    session.add(User(
        username='admin@example.org',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=test_password,
        role='editor'
    ))

    transaction.commit()
    session.close_all()

    return app
