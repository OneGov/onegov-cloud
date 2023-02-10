from asyncio import run
from onegov.core import Framework
from onegov.websockets import WebsocketsApp
from onegov.websockets.server import main
from os import path
from pytest import fixture
from pytest_localserver.http import WSGIServer
from tests.shared.client import Client
from tests.shared.utils import create_app
from threading import Thread
from yaml import dump


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


class App(Framework, WebsocketsApp):

    class Content:
        pass

    @Framework.path(path='/')
    class Root(Content):
        websocket_server_url = None

    @Framework.html(model=Content)
    def view_content(self, request):
        request.include('websockets')
        request.content_security_policy.connect_src.add('ws:')
        assert self.websocket_server_url
        return f"""
            <!doctype html>
            <html>
                <body>
                    <div id="x"></div>
                    <script>
                        WebsocketConfig = {{
                            endpoint: "{self.websocket_server_url}",
                            schema: "schema",
                            onrefresh: function(event) {{
                                document.getElementById("x").className += "y";
                            }}
                        }};
                    </script>
                </body>
            </html>
        """


@fixture(scope='function')
def app(request, websocket_config):
    websockets = {
        'client_url': websocket_config['url'],
        'manage_url': websocket_config['url'],
        'manage_token': websocket_config['token']
    }
    app = create_app(App, request, use_maildir=False, websockets=websockets)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def client(app):
    yield Client(app)


@fixture(scope='function')
def wsgi_server(request, app):
    app.print_exceptions = True
    server = WSGIServer(application=app)
    server.start()
    yield server
    server.stop()


@fixture(scope='function')
def browser(request, browser, websocket_server, wsgi_server):
    wsgi_server.app.Root.websocket_server_url = websocket_server.url
    browser.baseurl = wsgi_server.url
    browser.websocket_server_url = websocket_server.url
    yield browser


@fixture(scope='function')
def cfg_path(
    postgres_dsn, session_manager, temporary_directory, redis_url,
    websocket_config
):
    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'tests.onegov.websockets.conftest.App',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'websockets': {
                        'client_url': websocket_config['url'],
                        'manage_url': websocket_config['url'],
                        'manage_token': websocket_config['token']
                    }
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path
