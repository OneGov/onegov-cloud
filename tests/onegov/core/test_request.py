import morepath
import pytest

from datetime import datetime, timedelta
from freezegun import freeze_time
from onegov.core.framework import Framework
from onegov.core.request import CoreRequest, ReturnToMixin
from onegov.core.security import Public, Personal, Private, Secret
from onegov.core.utils import Bunch, scan_morepath_modules
from webtest import TestApp as Client
from urllib.parse import quote


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

    r.GET['return-to'] = 'http://phising'
    assert r.redirect('http://safe').location == 'http://safe'

    r.GET['return-to'] = param(r.return_here('http://safe'))
    assert r.redirect('http://safe').location == 'http://here'

    r.GET['return-to'] = param(r.return_to('http://safe', 'http://known'))
    assert r.redirect('http://safe').location == 'http://known'

    r.GET['return-to'] = param(r.return_to('http://safe', 'http://known'))
    r.GET['return-to'] += 'tampering'
    assert r.redirect('http://safe').location == 'http://safe'


def test_return_to(redis_url):

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
    app.configure_application(identity_secure=False, redis_url=redis_url)

    c = Client(app)
    do_something_url = c.get('/').text
    assert c.get(do_something_url).location == 'http://localhost/'
    assert c.get(do_something_url + 'x').location == 'http://localhost/default'
    assert c.get('/do-something').location == 'http://localhost/default'


def test_has_permission(redis_url):

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        allowed_for = (Public, Personal, Private, Secret)

    @App.view(model=Root, permission=Public)
    def view(self, request):
        permission = {
            'public': Public,
            'personal': Personal,
            'private': Private,
            'secret': Secret
        }[request.params.get('permission')]

        return request.has_permission(self, permission) and 'true' or 'false'

    @App.view(model=Root, permission=Public, name='login')
    def login(self, request):

        @request.after
        def remember_identity(response):
            request.app.remember_identity(response, request, morepath.Identity(
                userid='foo',
                groupid='admins',
                role='admin',
                application_id=request.app.application_id
            ))

        return 'ok'

    @App.permission_rule(model=Root, permission=object, identity=None)
    def has_permission_not_logged_in(identity, model, permission):
        return permission is Public

    @App.permission_rule(model=Root, permission=object)
    def has_permission_logged_in(identity, model, permission):
        return permission in model.allowed_for

    scan_morepath_modules(App)
    App.commit()

    app = App()

    app.application_id = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)

    c = Client(app)
    assert c.get('/?permission=public').text == 'true'
    assert c.get('/?permission=personal').text == 'false'
    assert c.get('/?permission=private').text == 'false'
    assert c.get('/?permission=secret').text == 'false'

    c.get('/login')

    assert c.get('/?permission=public').text == 'true'
    assert c.get('/?permission=personal').text == 'true'
    assert c.get('/?permission=private').text == 'true'
    assert c.get('/?permission=secret').text == 'true'


def test_permission_by_view(redis_url):
    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.view(model=Root, name='public', permission=Public)
    def public_view(self, request):
        assert False  # we don't want this view to be called

    @App.view(model=Root, name='personal', permission=Personal)
    def personal_view(self, request):
        assert False  # we don't want this view to be called

    @App.view(model=Root, name='private', permission=Private)
    def private_view(self, request):
        assert False  # we don't want this view to be called

    @App.view(model=Root, name='secret', permission=Secret)
    def secret_view(self, request):
        assert False  # we don't want this view to be called

    @App.view(model=Root, name='login', permission=Public)
    def login(self, request):

        @request.after
        def remember_identity(response):
            request.app.remember_identity(response, request, morepath.Identity(
                userid='foo',
                groupid='',
                role='admin',
                application_id=request.app.application_id,
            ))

        return 'ok'

    @App.view(model=Root)
    def view(self, request):
        url = request.params.get('url')
        return request.has_access_to_url(url) and 'true' or 'false'

    scan_morepath_modules(App)
    App.commit()

    app = App()

    app.application_id = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)

    c = Client(app)

    def has_access(url):
        return c.get('/?url={}'.format(quote(url))).text == 'true'

    assert app.permission_by_view(Root) is None
    assert app.permission_by_view(Root, 'login') is Public
    assert app.permission_by_view(Root, 'public') is Public
    assert app.permission_by_view(Root, 'personal') is Personal
    assert app.permission_by_view(Root, 'private') is Private
    assert app.permission_by_view(Root, 'secret') is Secret

    assert app.permission_by_view(Root()) is None
    assert app.permission_by_view(Root(), 'login') is Public
    assert app.permission_by_view(Root(), 'public') is Public
    assert app.permission_by_view(Root(), 'personal') is Personal
    assert app.permission_by_view(Root(), 'private') is Private
    assert app.permission_by_view(Root(), 'secret') is Secret

    with pytest.raises(AssertionError):
        app.permission_by_view(None)

    with pytest.raises(KeyError):
        app.permission_by_view(Root, 'foobar')

    # the domain is ignored
    for domain in ('', 'https://example.org'):
        assert has_access('{}/'.format(domain))
        assert has_access('{}/login'.format(domain))
        assert has_access('{}/public'.format(domain))
        assert not has_access('{}/personal'.format(domain))
        assert not has_access('{}/private'.format(domain))
        assert not has_access('{}/secret'.format(domain))

    c.get('/login')

    for domain in ('', 'https://example.org'):
        assert has_access('{}/'.format(domain))
        assert has_access('{}/login'.format(domain))
        assert has_access('{}/public'.format(domain))
        assert has_access('{}/personal'.format(domain))
        assert has_access('{}/private'.format(domain))
        assert has_access('{}/secret'.format(domain))
