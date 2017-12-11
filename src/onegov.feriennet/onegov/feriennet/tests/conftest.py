import transaction
import pytest

from onegov.feriennet import FeriennetApp
from onegov.feriennet.initial_content import create_new_organisation
from onegov.user import User
from onegov_testing.utils import create_app
from pytest_localserver.http import WSGIServer


@pytest.fixture(scope="session", autouse=True)
def import_scan():
    """ Scans all the onegov.* sources to make sure that the tables are
    created.

    """

    import importscan
    import onegov
    importscan.scan(onegov, ignore=['.test', '.tests'])


@pytest.yield_fixture(scope='function')
def feriennet_app(request):
    yield create_feriennet_app(request, use_elasticsearch=False)


@pytest.yield_fixture(scope='function')
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
        use_elasticsearch=use_elasticsearch)
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
