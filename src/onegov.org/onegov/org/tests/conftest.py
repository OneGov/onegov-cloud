import onegov.ticket
import transaction
import pytest

from onegov.org import OrgApp
from onegov.org.initial_content import create_new_organisation
from onegov.org.layout import DefaultLayout
from onegov.org.new_elements import Element
from onegov_testing import Client
from onegov_testing.utils import create_app
from onegov.user import User
from pytest_localserver.http import WSGIServer


@pytest.fixture(scope="session", autouse=True)
def import_scan():
    """ Scans all the onegov.* sources to make sure that the tables are
    created.

    """

    import importscan
    import onegov
    importscan.scan(onegov, ignore=['.test', '.tests'])


@pytest.fixture(scope='session')
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}


@pytest.fixture(scope='function')
def org_app(request):
    yield create_org_app(request, use_elasticsearch=False)


@pytest.fixture(scope='function')
def es_org_app(request):
    yield create_org_app(request, use_elasticsearch=True)


@pytest.fixture(scope='function')
def browser(browser, org_app_url):
    browser.baseurl = org_app_url
    yield browser


@pytest.fixture(scope='function')
def org_app_url(request, org_app):
    org_app.print_exceptions = True
    server = WSGIServer(application=org_app)
    server.start()
    yield server.url
    server.stop()


def create_org_app(request, use_elasticsearch, cls=OrgApp):
    app = create_app(cls, request, use_elasticsearch=use_elasticsearch)
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


@pytest.fixture(scope='function')
def render_element(request):
    class App(OrgApp):
        pass

    @App.path(path='/element', model=Element)
    def get_element(app):
        return app.element

    @App.html(model=Element)
    def render_element(self, request):
        return self(DefaultLayout(getattr(self, 'model', None), request))

    app = create_org_app(request, use_elasticsearch=False, cls=App)
    client = Client(app)

    def render(element):
        app.element = element
        return client.get('/element')

    return render
