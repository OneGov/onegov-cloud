import morepath
import onegov.core.security

from onegov.core.framework import Framework
from onegov.core.security import Public, Personal, Private, Secret
from onegov.core.security import forget, remembered
from webtest import TestApp as Client


def spawn_basic_permissions_app(redis_url):

    class App(Framework):
        pass

    class Root(object):
        pass

    @App.path(path='', model=Root)
    def get_root():
        return Root()

    @App.path(path='/hidden')
    class HiddenFromPublic(object):
        is_hidden_from_public = True

    @App.view(model=Root, name='public', permission=Public)
    def public_view(self, request):
        return 'public'

    @App.view(model=Root, name='private', permission=Private)
    def private_view(self, request):
        return 'private'

    @App.view(model=Root, name='personal', permission=Personal)
    def personal_view(self, request):
        return 'personal'

    @App.view(model=Root, name='secret', permission=Secret)
    def secret_view(self, request):
        return 'secret'

    @App.view(model=HiddenFromPublic, permission=Public)
    def hidden_from_public_view(self, request):
        return 'hidden'

    @App.view(
        model=Root,
        name='login',
        permission=Public,
        request_method='POST'
    )
    def login(self, request):
        userid = request.params.get('userid')
        groupid = request.params.get('groupid')
        role = request.params.get('role')
        identity = request.app.application_bound_identity(
            userid, groupid, role
        )

        @request.after
        def remember(response):
            request.app.remember_identity(response, request, identity)

    @App.view(model=Root, name='logout', permission=Private)
    def logout(self, request):

        @request.after
        def forget(response):
            request.app.forget_identity(response, request)

    # the scan is required (happens automatically if using onegov.server)
    morepath.scan(onegov.core.security)

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/app')

    return app


def test_anonymous_access(redis_url):
    client = Client(spawn_basic_permissions_app(redis_url))

    assert client.get('/public').text == 'public'
    assert client.get('/personal', expect_errors=True).status_code == 403
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403
    assert client.get('/hidden', expect_errors=True).status_code == 403


def test_personal_access(redis_url):
    client = Client(spawn_basic_permissions_app(redis_url))
    # use the userid 'admin' to be sure that we don't let it matter
    client.post(
        '/login',
        {'userid': 'admin', 'groupid': 'admins', 'role': 'member'}
    )

    assert client.get('/public').text == 'public'
    assert client.get('/personal').text == 'personal'
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403
    assert client.get('/hidden', expect_errors=True).status_code == 403


def test_private_access(redis_url):
    client = Client(spawn_basic_permissions_app(redis_url))
    # use the userid 'admin' to be sure that we don't let it matter
    client.post(
        '/login',
        {'userid': 'admin', 'groupid': 'admins', 'role': 'editor'}
    )

    assert client.get('/public').text == 'public'
    assert client.get('/personal').text == 'personal'
    assert client.get('/private').text == 'private'
    assert client.get('/hidden').text == 'hidden'
    assert client.get('/secret', expect_errors=True).status_code == 403

    client.get('/logout')

    assert client.get('/public').text == 'public'
    assert client.get('/personal', expect_errors=True).status_code == 403
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403
    assert client.get('/hidden', expect_errors=True).status_code == 403


def test_secret_access(redis_url):
    client = Client(spawn_basic_permissions_app(redis_url))
    # use the userid 'editor' to be sure that we don't let it matter
    client.post(
        '/login',
        {'userid': 'editor', 'groupid': 'editors', 'role': 'admin'}
    )

    assert client.get('/public').text == 'public'
    assert client.get('/personal').text == 'personal'
    assert client.get('/private').text == 'private'
    assert client.get('/secret').text == 'secret'
    assert client.get('/hidden').text == 'hidden'

    client.get('/logout')

    assert client.get('/public').text == 'public'
    assert client.get('/personal', expect_errors=True).status_code == 403
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403
    assert client.get('/hidden', expect_errors=True).status_code == 403


def test_secure_cookie(redis_url):
    app = spawn_basic_permissions_app(redis_url)
    app.identity_secure = True

    client = Client(app)
    client.post(
        '/login', {'userid': 'editor', 'groupid': 'editors', 'role': 'admin'},
        extra_environ={'wsgi.url_scheme': 'http'}
    )

    cookie = client.cookiejar._cookies['localhost.local']['/']['session_id']
    assert cookie.secure


def test_forget(redis_url):
    app = spawn_basic_permissions_app(redis_url)
    client = Client(app)
    response = client.post(
        '/login',
        {'userid': 'user', 'groupid': 'users', 'role': 'admin'}
    )

    session_id = app.unsign(response.request.cookies['session_id'])
    assert remembered(app, session_id)

    assert client.get('/public').text == 'public'
    assert client.get('/personal').text == 'personal'
    assert client.get('/private').text == 'private'
    assert client.get('/secret').text == 'secret'
    assert client.get('/hidden').text == 'hidden'

    forget(app, session_id)
    assert not remembered(app, session_id)

    assert client.get('/public').text == 'public'
    assert client.get('/personal', expect_errors=True).status_code == 403
    assert client.get('/private', expect_errors=True).status_code == 403
    assert client.get('/secret', expect_errors=True).status_code == 403
    assert client.get('/logout', expect_errors=True).status_code == 403
    assert client.get('/hidden', expect_errors=True).status_code == 403
