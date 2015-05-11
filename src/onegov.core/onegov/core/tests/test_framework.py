import json
import pytest

from datetime import datetime, timedelta
from freezegun import freeze_time
from morepath import setup
from onegov.core import Framework
from onegov.server import Config, Server
from webtest import TestApp as Client
from wtforms import Form, StringField


def test_set_application_id():
    app = Framework()
    app.namespace = 'namespace'
    app.configure_application()
    app.set_application_id('namespace/id')

    assert app.schema == 'namespace-id'


def test_virtual_host_request():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.path(path='/blog')
    class Blog(object):
        pass

    @App.view(model=Root)
    def view_root(self, request):
        return request.link(self) + ' - root'

    @App.view(model=Blog)
    def view_blog(self, request):
        return request.link(self) + ' - blog'

    config.commit()

    app = App()
    app.configure_application()

    c = Client(app)

    response = c.get('/')
    assert response.body == b'http://localhost/ - root'

    response = c.get('/blog')
    assert response.body == b'http://localhost/blog - blog'

    # X_VHM_HOST is a simple prefix..
    response = c.get('/', headers={'X_VHM_HOST': 'http://example.org'})
    assert response.body == b'http://example.org/ - root'

    response = c.get('/blog', headers={'X_VHM_HOST': 'http://example.org'})
    assert response.body == b'http://example.org/blog - blog'

    # .. though it won't lead to '//'s in the url
    response = c.get('/', headers={'X_VHM_HOST': 'http://example.org/'})
    assert response.body == b'http://example.org/ - root'

    # X_VHM_ROOT set to '/' has no influence
    response = c.get('/', headers={'X_VHM_ROOT': '/'})
    assert response.body == b'http://localhost/ - root'

    # just like X_VHM_HOST it tries to not introduce any '//'s
    response = c.get('/blog', headers={'X_VHM_ROOT': '/blog'})
    assert response.body == b'http://localhost/ - blog'

    response = c.get('/blog', headers={'X_VHM_ROOT': '/blog/'})
    assert response.body == b'http://localhost/ - blog'

    # X_VHM_HOST and X_VHM_ROOT may be used together
    response = c.get('/blog', headers={
        'X_VHM_ROOT': '/blog', 'X_VHM_HOST': 'https://blog.example.org/'})
    assert response.body == b'https://blog.example.org/ - blog'

    response = c.get('/blog', headers={
        'X_VHM_ROOT': '/blog',
        'X_VHM_HOST': 'https://blog.example.org/'})
    assert response.body == b'https://blog.example.org/ - blog'


def test_browser_session_request():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root)
    def view_root(self, request):
        # the session id is only available if there's a change in the
        # browser session
        request.browser_session['foo'] = 'bar'
        return request.cookies['session_id']

    @App.view(model=Root, name='login')
    def view_login(self, request):
        request.browser_session.logged_in = True
        return 'logged in'

    @App.view(model=Root, name='status')
    def view_status(self, request):
        if request.browser_session.has('logged_in'):
            return 'logged in'
        else:
            return 'logged out'

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    c1 = Client(app)
    c2 = Client(app)

    c1.get('/').text == c1.get('/').text
    c1.get('/').text != c2.get('/').text
    c2.get('/').text == c2.get('/').text

    c1.get('/status').text == 'logged out'
    c2.get('/status').text == 'logged out'

    c1.get('/login')

    c1.get('/status').text == 'logged in'
    c2.get('/status').text == 'logged out'


def test_browser_session_dirty():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, name='undirty')
    def view_undirty(self, request):
        request.browser_session.get('foo')
        return ''

    @App.view(model=Root, name='dirty')
    def view_dirty(self, request):
        request.browser_session['foo'] = 'bar'
        return ''

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    client = Client(app)

    client.get('/undirty')
    assert 'session_id' not in client.cookies

    client.get('/dirty')
    assert 'session_id' in client.cookies

    old_session_id = client.cookies['session_id']

    client.get('/undirty')
    assert client.cookies['session_id'] == old_session_id

    client.get('/undirty')
    assert client.cookies['session_id'] == old_session_id


def test_request_messages():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    class Message(object):
        def __init__(self, text, type):
            self.text = text
            self.type = type

    @App.path(model=Message, path='/messages')
    def get_message(text, type):
        return Message(text, type)

    @App.view(model=Message, name='add')
    def view_add_message(self, request):
        request.message(self.text, self.type)

    @App.view(model=Root)
    def view_root(self, request):
        return json.dumps(list(request.consume_messages()))

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(identity_secure=False)  # allow http

    app.cache_backend = 'dogpile.cache.memory'
    app.cache_backend_arguments = {}

    c1 = Client(app)
    c2 = Client(app)
    c1.get('/messages/add?text=one&type=info')
    c1.get('/messages/add?text=two&type=warning')
    c2.get('/messages/add?text=three&type=error')

    messages = json.loads(c1.get('/').text)
    assert len(messages) == 2
    assert messages[0][0] == 'one'
    assert messages[1][0] == 'two'
    assert messages[0][1] == 'info'
    assert messages[1][1] == 'warning'

    messages = json.loads(c1.get('/').text)
    assert len(messages) == 0

    messages = json.loads(c2.get('/').text)
    assert len(messages) == 1

    assert messages[0][0] == 'three'
    assert messages[0][1] == 'error'

    messages = json.loads(c2.get('/').text)
    assert len(messages) == 0


def test_fix_webassets_url():
    config = setup()

    import more.webassets
    import onegov.core
    config.scan(more.webassets)
    config.scan(onegov.core)

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.html(model=Root)
    def view_root(self, request):
        return '/' + request.app.webassets_url + '/jquery.js'

    config.commit()

    class TestServer(Server):

        def configure_morepath(self, *args, **kwargs):
            pass

    server = TestServer(Config({
        'applications': [
            {
                'path': '/towns/*',
                'application': App,
                'namespace': 'towns'
            }
        ]
    }))

    client = Client(server)

    # more.webassets doesn't know about virtual hosting (that is to say
    # Morepath does not know about it).
    #
    # Since it wants to create urls for the root of the application ('/'),
    # it will create something like '/xxx/jquery.js'
    #
    # We really want '/towns/test/xxx' here, which is something the onegov
    # core Framework application fixes through a tween.
    response = client.get('/towns/test')
    assert response.body == (b'http://localhost/towns/test/'
                             b'7da9c72a3b5f9e060b898ef7cd714b8a/jquery.js')


def test_sign_unsign():
    framework = Framework()
    framework.identity_secret = 'test'
    framework.application_id = 'one'

    assert framework.sign('foo').startswith('foo.')
    assert framework.unsign(framework.sign('foo')) == 'foo'

    signed_by_one = framework.sign('foo')
    framework.application_id = 'two'
    assert framework.unsign(signed_by_one) is None
    framework.application_id = 'one'
    assert framework.unsign(signed_by_one) == 'foo'

    signed = framework.sign('foo')
    framework.identity_secret = 'asdf'
    assert framework.unsign(signed) is None

    signed = framework.sign('foo')
    framework.unsign('bar' + signed) is None


def test_csrf_secret_key():
    app = Framework()

    with pytest.raises(AssertionError):
        app.configure_application(identity_secret='test', csrf_secret='test')

    with pytest.raises(AssertionError):
        app.configure_application(identity_secret='very-secret-key')

    with pytest.raises(AssertionError):
        app.configure_application(csrf_secret='another-very-secret-key')

    app.configure_application(identity_secret='x', csrf_secret='y')


def test_csrf():

    class MyForm(Form):
        name = StringField(u'Name')

    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, request_method='GET')
    def view_get_root(self, request):
        form = request.get_form(MyForm, i18n_support=False)
        return form.csrf_token._value()

    @App.view(model=Root, request_method='POST')
    def view_post_root(self, request):
        if request.get_form(MyForm, i18n_support=False).validate():
            return 'success'
        else:
            return 'fail'

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        disable_memcached=True,
        csrf_time_limit=60
    )

    client = Client(app)
    csrf_token = client.get('/').text
    assert client.post('/', {'csrf_token': csrf_token}).text == 'success'
    assert client.post('/', {'csrf_token': csrf_token + 'x'}).text == 'fail'
    assert client.post('/', {'csrf_token': csrf_token}).text == 'success'

    with freeze_time(datetime.now() + timedelta(minutes=2)):
        assert client.post('/', {'csrf_token': csrf_token}).text == 'fail'
