from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.content import create_new_organisation
from onegov.user import User
from pytest import fixture
from sqlalchemy.orm.session import close_all_sessions
from tests.onegov.town6.conftest import Client
from tests.shared.utils import create_app
from transaction import commit


def create_landsgemeinde_app(request, use_elasticsearch=False):
    app = create_app(
        LandsgemeindeApp,
        request,
        use_elasticsearch,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    session = app.session()

    create_new_organisation(
        app, 'Govikon', 'mails@govikon.ch', create_files=False
    )

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
    session.add(User(
        username='member@example.org',
        password_hash=test_password,
        role='member'
    ))

    commit()
    close_all_sessions()

    return app


@fixture(scope='function')
def landsgemeinde_app(request):
    yield create_landsgemeinde_app(request, False)


@fixture(scope='function')
def landsgemeinde_app_with_es(request):
    yield create_landsgemeinde_app(request, True)


@fixture(scope='function')
def client(landsgemeinde_app):
    return Client(landsgemeinde_app)


@fixture(scope='function')
def client_with_es(landsgemeinde_app_with_es):
    return Client(landsgemeinde_app_with_es)
