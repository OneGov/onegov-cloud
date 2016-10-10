from datetime import datetime, timedelta
from freezegun import freeze_time
from onegov.core.framework import Framework
from onegov.core.request import CoreRequest, ReturnToMixin
from onegov.core.utils import Bunch
from webtest import TestApp as Client


def test_url_safe_token():

    request = CoreRequest(environ={
        'PATH_INFO': '/',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https'
    }, app=Bunch(identity_secret='asdf', lookup=None))

    token = request.new_url_safe_token({'foo': 'bar'})

    assert request.load_url_safe_token(token) == {'foo': 'bar'}
    assert request.load_url_safe_token(token, salt='x') is None

    with freeze_time(datetime.now() + timedelta(seconds=2)):
        assert request.load_url_safe_token(token, max_age=1) is None


def test_return_to_mixin():

    class Request(ReturnToMixin):

        GET = {}

        @property
        def identity_secret(self):
            return 'foobar'

        @property
        def url(self):
            return 'http://here'

    def param(url):
        return url.split('=')[1]

    r = Request()

    assert r.return_to('https://example.org', '/')\
        .startswith('https://example.org?return-to=')

    assert r.return_here('https://example.org')\
        .startswith('https://example.org?return-to=')

    assert not r.return_to('https://example.org?return-to=foobar', '/')\
        .startswith('https://example.org?return-to=foobar')

    r.GET['return-to'] = 'http://phising'
    assert r.redirect('http://safe').location == 'http://safe'

    r.GET['return-to'] = param(r.return_here('http://safe'))
    assert r.redirect('http://safe').location == 'http://here'

    r.GET['return-to'] = param(r.return_to('http://safe', 'http://known'))
    assert r.redirect('http://safe').location == 'http://known'

    r.GET['return-to'] = param(r.return_to('http://safe', 'http://known'))
    r.GET['return-to'] += 'tampering'
    assert r.redirect('http://safe').location == 'http://safe'


def test_return_to():

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root)
    def homepage(self, request):
        return request.return_to(request.link(self, 'do-something'), '/')

    @App.view(model=Root, name='do-something')
    def do_something(self, request):
        return request.redirect('/default')

    App.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        disable_memcached=True
    )

    c = Client(app)
    do_something_url = c.get('/').text
    assert c.get(do_something_url).location == 'http://localhost/'
    assert c.get(do_something_url + 'x').location == 'http://localhost/default'
    assert c.get('/do-something').location == 'http://localhost/default'
