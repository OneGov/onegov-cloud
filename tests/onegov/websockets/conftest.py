from asyncio import run
from onegov.core import Framework
from onegov.websockets import WebsocketsApp
from onegov.websockets.server import main
from pytest import fixture
from pytest_localserver.http import WSGIServer
from tests.shared.utils import create_app
from threading import Thread


@fixture(scope='function')
def websocket_config():
    return {
        'host': '127.0.0.1',
        'port': 9876,
        'token': 'super-super-secret-token',
        'url': 'ws://127.0.0.1:9876'
    }


_websocket_server = None


@fixture(scope='function')
def websocket_server(websocket_config):

    def _main():
        run(
            main(
                websocket_config['host'],
                websocket_config['port'],
                websocket_config['token']
            )
        )

    # Run the socket server in a deamon thread, this way it automatically gets
    # termined when all tests are finished.
    global _websocket_server
    if not _websocket_server:
        _websocket_server = Thread(target=_main, daemon=True)
        _websocket_server.url = websocket_config['url']
        _websocket_server.start()

    yield _websocket_server


class WebsocketsTestApp(Framework, WebsocketsApp):
    pass


@WebsocketsApp.path(path='')
class WebsocketsRoot:
    html = ''


@WebsocketsApp.html(model=WebsocketsRoot)
def view_root(self, request):
    request.include('websockets')
    request.content_security_policy.connect_src.add('ws:')
    return self.html


@fixture(scope='function')
def websockets_app(request, websocket_config):
    websockets = {
        'client_url': websocket_config['url'],
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


@fixture(scope='function')
def wsgi_server(request, websockets_app):
    websockets_app.print_exceptions = True
    server = WSGIServer(application=websockets_app)
    server.start()
    yield server
    server.stop()


@fixture(scope='function')
def browser(request, browser, websocket_server, wsgi_server):
    browser.baseurl = wsgi_server.url
    browser.websocket_server_url = websocket_server.url
    yield browser
