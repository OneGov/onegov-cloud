from onegov.pas.app import PasApp
from onegov.pas.content.initial import create_new_organisation
from onegov.user import User
from pytest import fixture
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client
from tests.shared.utils import create_app
from transaction import commit


def create_pas_app(request, use_elasticsearch=False):
    app = create_app(
        PasApp,
        request,
        use_maildir=True,
        use_elasticsearch=use_elasticsearch,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    org = create_new_organisation(app, name="Govikon")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    session = app.session()
    test_password = request.getfixturevalue('test_password')
    session.add(
        User(
            username='admin@example.org',
            password_hash=test_password,
            role='admin'
        )
    )
    session.add(
        User(
            username='editor@example.org',
            password_hash=test_password,
            role='editor'
        )
    )
    session.add(
        User(
            username='member@example.org',
            password_hash=test_password,
            role='member'
        )
    )

    commit()
    close_all_sessions()
    return app


@fixture(scope='function')
def pas_app(request):
    app = create_pas_app(request, use_elasticsearch=False)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def es_pas_app(request):
    app = create_pas_app(request, use_elasticsearch=True)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def client(pas_app):
    client = Client(pas_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@fixture(scope='function')
def client_with_es(es_pas_app):
    client = Client(es_pas_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client
