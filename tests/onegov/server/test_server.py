from __future__ import annotations

from onegov.server.application import Application
from onegov.server.core import Server
from onegov.server.config import Config
from webob import Response
from webob.request import BaseRequest
from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed.wsgi import WSGIEnvironment, StartResponse
    from collections.abc import Iterable


def test_application_mapping() -> None:

    class EchoApplication(Application):

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = ', '.join(
                (self.application_base_path, self.application_id))

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/static',
                'application': EchoApplication,
                'namespace': 'stag'
            },
            {
                'path': '/wildcard/*',
                'application': EchoApplication,
                'namespace': 'wild'
            }
        ]
    }))

    c = Client(server)
    assert c.get('/static').body == b'/static, stag/static'
    assert c.get('/static/').body == b'/static, stag/static'
    assert c.get('/static/site').body == b'/static, stag/static'
    assert c.get('/static/site/').body == b'/static, stag/static'
    assert c.get('/wildcard/blog').body == b'/wildcard/blog, wild/blog'
    assert c.get('/wildcard/blog/').body == b'/wildcard/blog, wild/blog'
    assert c.get('/wildcard/blog/login').body == b'/wildcard/blog, wild/blog'
    assert c.get('/wildcard/blog/login/').body == b'/wildcard/blog, wild/blog'
    assert c.get('/wildcard/monitor/refresh').body\
        == b'/wildcard/monitor, wild/monitor'
    assert c.get('/wildcard/monitor/refresh/').body\
        == b'/wildcard/monitor, wild/monitor'

    c.get('/', status=404)
    c.get('/wildcard', status=404)
    c.get('/wildcard/', status=404)
    c.get('/not-there', status=404)


def test_path_prefix() -> None:

    class EchoApplication(Application):

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            request = BaseRequest(environ)

            response = Response()
            response.text = ', '.join(
                (request.script_name, request.path_info))

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/static',
                'application': EchoApplication,
                'namespace': 'static'
            },
            {
                'path': '/wildcard/*',
                'application': EchoApplication,
                'namespace': 'wildcard'
            },
        ]
    }))

    c = Client(server)
    assert c.get('/static').body == b'/static, '
    assert c.get('/static/info').body == b'/static, /info'
    assert c.get('/static/info/test').body == b'/static, /info/test'
    assert c.get('/wildcard/info').body == b'/wildcard/info, '
    assert c.get('/wildcard/info/test').body == b'/wildcard/info, /test'
    assert c.get('/wildcard/x/y/z').body == b'/wildcard/x, /y/z'


def test_environ_changes() -> None:

    class EchoApplication(Application):

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = ', '.join((
                environ['SCRIPT_NAME'],
                environ['PATH_INFO']
            ))

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/static',
                'application': EchoApplication,
                'namespace': 'static'
            },
            {
                'path': '/wildcard/*',
                'application': EchoApplication,
                'namespace': 'wildcard'
            },
        ]
    }))

    c = Client(server)
    assert c.get('/static').body == b'/static, '
    assert c.get('/static/static').body == b'/static, /static'
    assert c.get('/static/static/static').body == b'/static, /static/static'
    assert c.get('/wildcard/wildcard').body == b'/wildcard/wildcard, '
    assert c.get('/wildcard/wildcard/wildcard').body\
        == b'/wildcard/wildcard, /wildcard'


def test_invalid_host_request() -> None:

    class HelloApplication(Application):


        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = 'hello'

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/static',
                'application': HelloApplication,
                'namespace': 'static'
            }
        ]
    }))

    c = Client(server)

    response = c.get('/static')
    assert response.body == b'hello'

    response = c.get(
        '/static', headers={'X_VHM_HOST': 'https://example.org'}, status=403)
    assert response.status_code == 403

    response = c.get(
        '/static', headers={'HOST': 'example.org:8080'}, status=403)
    assert response.status_code == 403

    app = server.applications.get('/static')
    assert app is not None
    app.allowed_hosts.add('example.org')

    response = c.get('/static', headers={'X_VHM_HOST': 'https://example.org'})
    assert response.body == b'hello'

    response = c.get('/static', headers={'HOST': 'example.org:8080'})
    assert response.body == b'hello'


def test_not_allowed_application_id() -> None:

    class HelloApplication(Application):

        def is_allowed_application_id(self, application_id: str) -> bool:
            return application_id == 'foobar'

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = 'hello'

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/sites/*',
                'application': HelloApplication,
                'namespace': 'sites'
            }
        ]
    }))

    c = Client(server)

    assert c.get('/sites/abc', expect_errors=True).status_code == 404
    assert c.get('/sites/foobar', expect_errors=False).status_code == 200


def test_aliases() -> None:

    class EchoApplication(Application):

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = ''.join((self.application_id))

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/sites/*',
                'application': EchoApplication,
                'namespace': 'aliases'
            }
        ]
    }))

    application = server.applications.get('/sites')
    assert application is not None

    c = Client(server)

    response = c.get('/sites/main')
    assert response.body == b'aliases/main'

    response = c.get('/sites/blog')
    assert response.body == b'aliases/blog'

    application.alias('main', 'blog')

    response = c.get('/sites/blog')
    assert response.body == b'aliases/main'


def test_application_id_dashes() -> None:

    class HelloApplication(Application):

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = self.application_id

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/foo-bar/*',
                'application': HelloApplication,
                'namespace': 'foo-bar'
            }
        ]
    }))

    c = Client(server)
    assert c.get('/foo-bar/bar-foo').text == 'foo_bar/bar_foo'


def test_exception_handler() -> None:

    class ErrorApplication(Application):

        def __call__(
            self,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            raise RuntimeError()

        def handle_exception(
            self,
            exception: BaseException,
            environ: WSGIEnvironment,
            start_response: StartResponse
        ) -> Iterable[bytes]:

            response = Response()
            response.text = exception.__class__.__name__

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/sites/*',
                'application': ErrorApplication,
                'namespace': 'sites'
            }
        ]
    }))

    c = Client(server)
    assert c.get('/sites/test').text == 'RuntimeError'
