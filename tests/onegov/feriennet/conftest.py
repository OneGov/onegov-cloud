import transaction
import pytest

from onegov.feriennet import FeriennetApp
from onegov.feriennet.initial_content import create_new_organisation
from onegov.feriennet.models import VacationActivity
from onegov.user import User
from pytest_localserver.http import WSGIServer
from sqlalchemy.orm.session import close_all_sessions
from tests.onegov.activity.fixtures.scenario import Scenario
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app


class Client(BaseClient):
    skip_n_forms = 1
    use_intercooler = True

    def fill_out_profile(self, first_name="Scrooge", last_name="McDuck"):
        profile = self.get('/userprofile')
        profile.form['salutation'] = 'mr'
        profile.form['first_name'] = first_name
        profile.form['last_name'] = last_name
        profile.form['address'] = 'foobar'
        profile.form['zip_code'] = '1234'
        profile.form['place'] = 'Duckburg'
        profile.form['emergency'] = f'0123 456 789 ({first_name} {last_name})'
        if 'political_municipality' in profile.form.fields:
            profile.form['political_municipality'] = 'Bruckerburg'

        profile.form.submit()


@pytest.fixture(scope='function')
def client(feriennet_app):
    return Client(feriennet_app)


@pytest.fixture(scope='function')
def client_with_es(es_feriennet_app):
    return Client(es_feriennet_app)


@pytest.fixture(scope='function')
def feriennet_app(request):
    yield create_feriennet_app(request, use_elasticsearch=False)


@pytest.fixture(scope='function')
def es_feriennet_app(request):
    yield create_feriennet_app(request, use_elasticsearch=True)


@pytest.fixture(scope='function')
def browser(browser, feriennet_app_url):
    browser.baseurl = feriennet_app_url
    yield browser


@pytest.fixture(scope='function')
def feriennet_app_url(request, feriennet_app):
    feriennet_app.print_exceptions = True
    server = WSGIServer(application=feriennet_app)
    server.start()
    yield server.url
    server.stop()


def create_feriennet_app(request, use_elasticsearch):
    app = create_app(
        app_class=FeriennetApp,
        request=request,
        use_elasticsearch=use_elasticsearch,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
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

    org = create_new_organisation(app, name="Govikon", create_files=False)
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.
    test_password = request.getfixturevalue('test_password')

    session.add(User(
        username='admin@example.org',
        realname='Foo Bar',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        realname='Boo Far',
        password_hash=test_password,
        role='editor'
    ))

    transaction.commit()
    close_all_sessions()

    return app


@pytest.fixture(scope='function')
def scenario(request, session, test_password):
    for name in request.fixturenames:
        if name in ('feriennet_app', 'es_feriennet_app'):
            session = request.getfixturevalue(name).session()

    yield Scenario(session, test_password, activity_model=VacationActivity)
