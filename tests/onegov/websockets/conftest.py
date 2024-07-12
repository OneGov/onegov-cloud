from onegov.core import Framework
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.websockets import WebsocketsApp
from pytest import fixture
from pytest_localserver.http import WSGIServer
from tests.shared.client import Client
from tests.shared.utils import create_app


class WebsocketsTestApp(Framework, WebsocketsApp):
    pass


@WebsocketsApp.path(path='')
class WebsocketsRoot:
    html = ''


@WebsocketsApp.html(model=WebsocketsRoot)
def view_root(self, request):
    request.include('websockets')
    return self.html


@fixture(scope='function')
def websockets_app(request, websocket_config):
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


@fixture(scope='function')
def client(websockets_app):
    yield Client(websockets_app)


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


@fixture(scope="session", autouse=True)
def enter_observer_scope():
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(WebsocketsTestApp)
