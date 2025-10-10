from datetime import date
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.content import create_new_organisation
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from onegov.user import User
from pytest import fixture
from pytest_localserver.http import WSGIServer
from sqlalchemy.orm.session import close_all_sessions
from tests.onegov.town6.conftest import Client
from tests.shared.utils import create_app
from transaction import commit
from unittest.mock import Mock


@fixture(scope='function')
def assembly():
    assembly = Assembly(state='scheduled', date=date(2023, 5, 7))
    agenda_item_1 = AgendaItem(state='scheduled', number=1)
    agenda_item_2 = AgendaItem(state='scheduled', number=2)
    votum_1_1 = Votum(state='scheduled', number=1)
    votum_1_2 = Votum(state='scheduled', number=2)
    votum_2_1 = Votum(state='scheduled', number=1)
    votum_2_2 = Votum(state='scheduled', number=2)
    votum_2_3 = Votum(state='scheduled', number=3)
    agenda_item_1.vota.append(votum_1_2)
    agenda_item_1.vota.append(votum_1_1)
    agenda_item_2.vota.append(votum_2_2)
    agenda_item_2.vota.append(votum_2_3)
    agenda_item_2.vota.append(votum_2_1)
    assembly.agenda_items.append(agenda_item_2)
    assembly.agenda_items.append(agenda_item_1)
    yield assembly


def create_landsgemeinde_app(
    request, enable_search=False, websocket_config=None
):
    if websocket_config:
        websockets = {
            'client_url': websocket_config['url'],
            'client_csp': websocket_config['url'],
            'manage_url': websocket_config['url'],
            'manage_token': websocket_config['token']
        }
    else:
        websockets = {
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }

    app = create_app(
        LandsgemeindeApp,
        request,
        enable_search,
        websockets=websockets
    )
    if not websocket_config:
        app.send_websocket = Mock()

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
def fts_landsgemeinde_app(request):
    yield create_landsgemeinde_app(request, True)


@fixture(scope='function')
def client(landsgemeinde_app):
    return Client(landsgemeinde_app)


@fixture(scope='function')
def client_with_fts(fts_landsgemeinde_app):
    return Client(fts_landsgemeinde_app)


@fixture(scope='function')
def wsgi_server(request, websocket_config):
    app = create_landsgemeinde_app(request, False, websocket_config)
    app.print_exceptions = True
    server = WSGIServer(application=app)
    server.start()
    yield server
    server.stop()


@fixture(scope='function')
def browser(request, browser, websocket_server, wsgi_server):
    browser.baseurl = wsgi_server.url
    browser.websocket_server_url = websocket_server.url
    browser.websocket_server = websocket_server
    browser.wsgi_server = wsgi_server
    yield browser


@fixture(scope="session", autouse=True)
def enter_observer_scope():
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(LandsgemeindeApp)
