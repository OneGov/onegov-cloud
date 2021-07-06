import onegov.ticket
import pytest
import transaction

from onegov.core.utils import module_path
from onegov.town6 import TownApp
from onegov.town6.initial_content import builtin_form_definitions
from onegov.town6.initial_content import create_new_organisation
from onegov.user import User
from pytest_localserver.http import WSGIServer
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app


class Client(BaseClient):
    skip_first_form = True
    use_intercooler = True

    def login_member(self, to=None):
        return self.login('member@example.org', 'hunter2', to)

    def bound_reserve(self, allocation):

        default_start = '{:%H:%M}'.format(allocation.start)
        default_end = '{:%H:%M}'.format(allocation.end)
        default_whole_day = allocation.whole_day
        resource = allocation.resource
        allocation_id = allocation.id

        def reserve(
            start=default_start,
            end=default_end,
            quota=1,
            whole_day=default_whole_day
        ):
            return self.post(
                f'/allocation/{resource}/{allocation_id}/reserve'
                f'?start={start}&end={end}&quota={quota}'
                f'&whole_day={whole_day and "1" or "0"}'
            )

        return reserve


@pytest.fixture(scope='function')
def handlers():
    before = onegov.ticket.handlers.registry
    onegov.ticket.handlers.registry = {}
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = before


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
    app.configure_payment_providers(**{
        'payment_providers_enabled': True,
        'payment_provider_defaults': {
            'stripe_connect': {
                'client_id': 'foo',
                'client_secret': 'foo',
                'oauth_gateway': 'https://oauth.example.org',
                'oauth_gateway_auth': 'foo',
                'oauth_gateway_secret': 'bar'
            }
        }
    })
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
    close_all_sessions()

    return app
