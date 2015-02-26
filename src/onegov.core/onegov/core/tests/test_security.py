import morepath
import onegov.core.security

from onegov.core import Framework
from onegov.core.security import Public, Private, Secret
from webtest import TestApp as Client


def spawn_basic_permissions_app():

    config = morepath.setup()

    class App(Framework):
        testing_config = config

    @App.path(path='')
    class Root(object):
        pass

    @App.view(model=Root, name='public', permission=Public)
    def public_view(self, request):
        return 'public'

    @App.view(model=Root, name='private', permission=Private)
    def private_view(self, request):
        return 'private'

    @App.view(model=Root, name='secret', permission=Secret)
    def secret_view(self, request):
        return 'secret'

    @App.view(
        model=Root,
        name='login',
        permission=Public,
        request_method='POST'
    )
    def login(self, request):
        userid = request.params.get('userid')
        role = request.params.get('role')
        identity = request.app.application_bound_identity(userid, role)

        @request.after
        def remember(response):
            morepath.remember_identity(response, request, identity)

    @App.view(model=Root, name='logout', permission=Private)
    def logout(self, request):

        @request.after
        def forget(response):
            morepath.forget_identity(response, request)

    # the scan is required (happens automatically if using onegov.server)
    config.scan(onegov.core.security)
    config.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False)
    app.set_application_id('test/app')

    return app


def test_anonymous_access():
    client = Client(spawn_basic_permissions_app())

    assert client.get('/public').text == 'public'
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403


def test_private_access():
    client = Client(spawn_basic_permissions_app())
    # use the userid 'admin' to be sure that we don't let it matter
    client.post('/login', {'userid': 'admin', 'role': 'editor'})

    assert client.get('/public').text == 'public'
    assert client.get('/private').text == 'private'
    assert client.get('/secret', expect_errors=True).status_code == 403

    client.get('/logout')

    assert client.get('/public').text == 'public'
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403


def test_secret_access():
    client = Client(spawn_basic_permissions_app())
    # use the userid 'editor' to be sure that we don't let it matter
    client.post('/login', {'userid': 'editor', 'role': 'admin'})

    assert client.get('/public').text == 'public'
    assert client.get('/private').text == 'private'
    assert client.get('/secret').text == 'secret'

    client.get('/logout')

    assert client.get('/public').text == 'public'
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403


def test_secure_cookie():
    app = spawn_basic_permissions_app()
    app.identity_secure = True

    client = Client(app)
    client.post(
        '/login', {'userid': 'editor', 'role': 'admin'},
        extra_environ={'wsgi.url_scheme': 'http'}
    )

    assert client.cookiejar._cookies['localhost.local']['/']['userid'].secure
