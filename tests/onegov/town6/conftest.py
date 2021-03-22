import onegov.core
import onegov.town6
import pytest
import transaction

from onegov.core.utils import module_path
from tests.onegov.org.conftest import Client
from tests.shared.utils import create_app
from onegov.town6 import TownApp
from onegov.town6.initial_content import builtin_form_definitions
from onegov.town6.initial_content import create_new_organisation
from onegov.user import User
from pytest_localserver.http import WSGIServer


@pytest.fixture(scope='session')
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}


@pytest.fixture(scope='session')
def forms():
    yield list(builtin_form_definitions(
        module_path('onegov.town6', 'forms/builtin')))


@pytest.fixture(scope='function')
def town_app(request):
    yield create_town_app(request, use_elasticsearch=False)


@pytest.fixture(scope='function')
def client(town_app):
    return Client(town_app)


@pytest.fixture(scope='function')
def browser(browser, town_app_url):
    browser.baseurl = town_app_url
    yield browser


@pytest.fixture(scope='function')
def town_app_url(request, town_app):
    town_app.print_exceptions = True
    server = WSGIServer(application=town_app)
    server.start()
    yield server.url
    server.stop()


@pytest.fixture(scope='function')
def es_town_app(request):
    yield create_town_app(request, use_elasticsearch=True)


def create_town_app(request, use_elasticsearch):
    app = create_app(TownApp, request, use_elasticsearch=False)
    session = app.session()

    forms = request.getfixturevalue('forms')
    create_new_organisation(
        app, 'Govikon', 'mails@govikon.ch', forms, create_files=False)

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
