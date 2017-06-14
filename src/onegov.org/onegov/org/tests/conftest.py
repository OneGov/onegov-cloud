import onegov.ticket
import transaction
import pytest

from onegov.org import OrgApp
from onegov.org.initial_content import create_new_organisation
from onegov.org.layout import DefaultLayout
from onegov.org.new_elements import Element
from onegov.org.testing import Client
from onegov.testing.utils import create_app
from onegov.user import User


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


@pytest.yield_fixture(scope='function')
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
