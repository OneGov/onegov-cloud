from onegov.server.application import Application
from onegov.server.core import Server
from onegov.server.config import Config
from webob import BaseRequest, Response
from webtest import TestApp as Client


def test_application_mapping():

    class EchoApplication(Application):

        def __call__(self, environ, start_response):
            response = Response()
            response.text = u', '.join(
                (self.application_base_path, self.application_id))

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/static',
                'class': EchoApplication
            },
            {
                'path': '/wildcard/*',
                'class': EchoApplication
            }
        ]
    }))

    c = Client(server)
    c.get('/static').body == b'/static, static'
    c.get('/static/').body == b'/static, static'
    c.get('/static/site').body == b'/static, static'
    c.get('/static/site/').body == b'/static, static'
    c.get('/wildcard/blog').body == b'/wildcard/blog, blog'
    c.get('/wildcard/blog/').body == b'/wildcard/blog, blog'
    c.get('/wildcard/blog/login').body == b'/wildcard/blog, blog'
    c.get('/wildcard/blog/login/').body == b'/wildcard/blog, blog'
    c.get('/wildcard/monitor/refresh').body == b'/wildcard/monitor, monitor'
    c.get('/wildcard/monitor/refresh/').body == b'/wildcard/monitor, monitor'

    c.get('/', status=404)
    c.get('/wildcard', status=404)
    c.get('/wildcard/', status=404)
    c.get('/not-there', status=404)


def test_path_prefix():

    class EchoApplication(Application):

        def __call__(self, environ, start_response):
            request = BaseRequest(environ)

            response = Response()
            response.text = u', '.join(
                (request.script_name, request.path_info))

            return response(environ, start_response)

    server = Server(Config({
        'applications': [
            {
                'path': '/static',
                'class': EchoApplication
            },
            {
                'path': '/wildcard/*',
                'class': EchoApplication
            },
        ]
    }))

    c = Client(server)
    c.get('/static').body == b'/static, '
    c.get('/static/info').body == b'/static, /info'
    c.get('/static/info/test').body == b'/static, /info/test'
    c.get('/wildcard/info').body == b'/wildcard/info, '
    c.get('/wildcard/info/test').body == b'/wildcard/info, /test'
    c.get('/wildcard/x/y/z').body == b'/wildcard/x, /y/z'
