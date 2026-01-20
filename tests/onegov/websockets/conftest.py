from __future__ import annotations

import pytest

from onegov.core import Framework
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.websockets import WebsocketsApp
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from tests.shared.client import Client
from tests.shared.utils import create_app


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from tests.shared.browser import ExtendedBrowser
    from tests.shared.fixtures import WebsocketThread
    from typing import type_check_only

    @type_check_only
    class WebsocketBrowser(ExtendedBrowser):
        websocket_server_url: str


class WebsocketsTestApp(Framework, WebsocketsApp):
    pass


@WebsocketsApp.path(path='')
class WebsocketsRoot:
    html = ''


@WebsocketsApp.html(model=WebsocketsRoot)
def view_root(self: WebsocketsRoot, request: CoreRequest) -> str:
    request.include('websockets')
    return self.html.replace(
        '${nonce}',
        request.content_security_policy_nonce('script')
    )


@pytest.fixture(scope='function')
def websockets_app(
    request: pytest.FixtureRequest,
    websocket_config: dict[str, Any]
) -> Iterator[WebsocketsTestApp]:

    websockets = {
        'client_url': websocket_config['url'],
        'client_csp': websocket_config['url'],
        'manage_url': websocket_config['url'],
        'manage_token': websocket_config['token']
    }
    app = create_app(
        WebsocketsTestApp,
        request,
        use_maildir=False,
        websockets=websockets
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def client(websockets_app: WebsocketsTestApp) -> Iterator[Client]:
    yield Client(websockets_app)


@pytest.fixture(scope='function')
def wsgi_server(
    request: pytest.FixtureRequest,
    websockets_app: WebsocketsTestApp
) -> Iterator[WSGIServer]:

    websockets_app.print_exceptions = True
    server = WSGIServer(application=websockets_app)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope='function')
def browser(
    request: pytest.FixtureRequest,
    browser: WebsocketBrowser,
    websocket_server: WebsocketThread,
    wsgi_server: WSGIServer
) -> Iterator[WebsocketBrowser]:
    browser.baseurl = wsgi_server.url
    browser.websocket_server_url = websocket_server.url
    yield browser


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(WebsocketsTestApp)
