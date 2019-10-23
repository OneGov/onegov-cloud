import pytest
import transaction

from onegov.user import User
from onegov.fsi import FsiApp
from onegov.fsi.initial_content import create_new_organisation
from tests.shared.utils import create_app
from tests.onegov.org.conftest import Client


@pytest.yield_fixture(scope='function')
def fsi_app(request):
    yield create_fsi_app(request, use_elasticsearch=False)


@pytest.yield_fixture(scope='function')
def es_fsi_app(request):
    yield create_fsi_app(request, use_elasticsearch=True)


@pytest.fixture(scope='function')
def client(fsi_app):
    return Client(fsi_app)


@pytest.fixture(scope='function')
def client_with_es(es_fsi_app):
    return Client(es_fsi_app)


def create_fsi_app(request, use_elasticsearch):

    app = create_app(
        app_class=FsiApp,
        request=request,
        use_elasticsearch=use_elasticsearch)

    session = app.session()

    org = create_new_organisation(app, name="Kursverwaltung")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

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
