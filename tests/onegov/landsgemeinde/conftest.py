from __future__ import annotations

import pytest

from datetime import date
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.content import create_new_organisation
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from onegov.user import User
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from sqlalchemy.orm.session import close_all_sessions
from tests.onegov.town6.conftest import Client
from tests.shared.utils import create_app
from transaction import commit
from unittest.mock import Mock


from typing import cast, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from tests.shared.browser import ExtendedBrowser
    from tests.shared.fixtures import WebsocketThread
    from typing import type_check_only

    @type_check_only
    class WebsocketBrowser(ExtendedBrowser):
        websocket_server_url: str
        websocket_server: WebsocketThread
        wsgi_server: WSGIServer


class TestApp(LandsgemeindeApp):
    __test__ = False
    maildir: str


@pytest.fixture(scope='function')
def assembly() -> Iterator[Assembly]:
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
    request: pytest.FixtureRequest,
    enable_search: bool = False,
    websocket_config: dict[str, Any] | None = None
) -> TestApp:
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
        TestApp,
        request,
        enable_search,
        websockets=websockets
    )
    if not websocket_config:
        app.send_websocket = Mock()  # type: ignore[method-assign]

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


@pytest.fixture(scope='function')
def landsgemeinde_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_landsgemeinde_app(request, False)


@pytest.fixture(scope='function')
def fts_landsgemeinde_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_landsgemeinde_app(request, True)


@pytest.fixture(scope='function')
def client(landsgemeinde_app: TestApp) -> Client[TestApp]:
    return Client(landsgemeinde_app)


@pytest.fixture(scope='function')
def client_with_fts(fts_landsgemeinde_app: TestApp) -> Client[TestApp]:
    return Client(fts_landsgemeinde_app)


@pytest.fixture(scope='function')
def wsgi_server(
    request: pytest.FixtureRequest,
    websocket_config: dict[str, Any]
) -> Iterator[WSGIServer]:
    app = create_landsgemeinde_app(request, False, websocket_config)
    app.print_exceptions = True
    server = WSGIServer(application=app)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope='function')
def browser(
    request: pytest.FixtureRequest,
    browser: ExtendedBrowser,
    websocket_server: WebsocketThread,
    wsgi_server: WSGIServer
) -> Iterator[WebsocketBrowser]:
    browser = cast('WebsocketBrowser', browser)
    browser.baseurl = wsgi_server.url
    browser.websocket_server_url = websocket_server.url
    browser.websocket_server = websocket_server
    browser.wsgi_server = wsgi_server
    yield browser


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(LandsgemeindeApp)
