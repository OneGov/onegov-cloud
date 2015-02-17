from onegov.server.application import Application
from onegov.server.core import Server
from onegov.server.config import Config
from webob import Response
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
