from __future__ import annotations

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
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response


def test_url_safe_token() -> None:

    request = CoreRequest(environ={
        'PATH_INFO': '/',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https'
    }, app=Bunch(identity_secret='asdf', lookup=None))  # type: ignore[arg-type]

    token = request.new_url_safe_token({'foo': 'bar'})

    assert request.load_url_safe_token(token) == {'foo': 'bar'}
    assert request.load_url_safe_token(token, salt='x') is None

    with freeze_time(datetime.now() + timedelta(seconds=2)):
        assert request.load_url_safe_token(token, max_age=1) is None


def test_return_to_mixin() -> None:

    class Request(ReturnToMixin):

        if not TYPE_CHECKING:
            GET = {}

        @property
        def identity_secret(self) -> str:
            return 'foobar'

        @property
        def url(self) -> str:
            return 'http://here'

    def param(url: str) -> str:
        return url.split('=')[1]

    r = Request()  # type: ignore[call-arg]

    assert r.return_to('https://example.org', '/').startswith(
        'https://example.org?return-to=')

    assert r.return_here('https://example.org').startswith(
        'https://example.org?return-to=')

    r.GET['return-to'] = 'http://phising'
    assert r.redirect('http://safe').location == 'http://safe'

    r.GET['return-to'] = param(r.return_here('http://safe'))
    assert r.redirect('http://safe').location == 'http://here'

    r.GET['return-to'] = param(r.return_to('http://safe', 'http://known'))
    assert r.redirect('http://safe').location == 'http://known'

    r.GET['return-to'] = param(r.return_to('http://safe', 'http://known'))
    r.GET['return-to'] += 'tampering'
    assert r.redirect('http://safe').location == 'http://safe'


def test_vhm_root_urls() -> None:

    request = CoreRequest(environ={
        'wsgi.url_scheme': 'https',
        'PATH_INFO': '/events',
        'QUERY_STRING': 'page=1',
        'SCRIPT_NAME': '/town/example',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https',
        'HTTP_HOST': 'example.com',
        'HTTP_X_VHM_ROOT': '/town/example/',
    }, app=Bunch())  # type: ignore[arg-type]

    assert request.x_vhm_root == '/town/example'
    assert request.application_url == 'https://example.com'
    assert request.path_url == 'https://example.com/events'
    assert request.url == 'https://example.com/events?page=1'


def test_return_to(redis_url: str) -> None:

    class App(Framework):
        pass

    @App.path(path='/')
    class Root:
        pass

    @App.view(model=Root)
    def homepage(self: Root, request: CoreRequest) -> str:
        return request.return_to(request.link(self, 'do-something'), '/')

    @App.view(model=Root, name='do-something')
    def do_something(self: Root, request: CoreRequest) -> Response:
        return request.redirect('/default')

    App.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/test')

    c = Client(app)
    do_something_url = c.get('/').text
    assert c.get(do_something_url).location == 'http://localhost/'
    assert c.get(do_something_url + 'x').location == 'http://localhost/default'
    assert c.get('/do-something').location == 'http://localhost/default'


@pytest.mark.parametrize('class_link', [False, True])
def test_link_with_query_parameters_and_fragment(
    redis_url: str,
    class_link: bool
) -> None:

    class App(Framework):
        pass

    @App.path(path='/')
    class Root:
        def __init__(self, foo: str | None = None) -> None:
            self.foo = foo

    @App.view(model=Root)
    def homepage(self: Root, request: CoreRequest) -> str:
        link: Any
        if class_link:
            def link(obj: Root, **kwargs: Any) -> str | None:
                return request.class_link(Root, {'foo': obj.foo}, **kwargs)
        else:
            link = request.link

        foo = Root(foo='bar')
        return '\n'.join((
            link(self),
            link(self, query_params={'a': '1'}),
            link(self, query_params={'a': '1', 'b': 2}),
            link(self, fragment='main'),
            link(self, query_params={'a': '1'}, fragment='main'),
            link(foo),
            link(foo, query_params={'a': '1'}),
            link(foo, query_params={'a': '1', 'b': 2}),
            link(foo, fragment='main'),
            link(foo, query_params={'a': '1'}, fragment='main'),
        ))

    @App.view(model=Root, name='foo')
    def do_something(self: Root, request: CoreRequest) -> Response:
        return request.redirect('/default')

    App.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/test')

    client = Client(app)
    assert client.get('/').text == (
        'http://localhost/\n'
        'http://localhost/?a=1\n'
        'http://localhost/?a=1&b=2\n'
        'http://localhost/#main\n'
        'http://localhost/?a=1#main\n'
        'http://localhost/?foo=bar\n'
        'http://localhost/?foo=bar&a=1\n'
        'http://localhost/?foo=bar&a=1&b=2\n'
        'http://localhost/?foo=bar#main\n'
        'http://localhost/?foo=bar&a=1#main'
    )


def test_has_permission(redis_url: str) -> None:

    class App(Framework):
        pass

    @App.path(path='/')
    class Root:
        allowed_for = (Public, Personal, Private, Secret)

    @App.view(model=Root, permission=Public)
    def view(self: Root, request: CoreRequest) -> str:
        permission = {
            'public': Public,
            'personal': Personal,
            'private': Private,
            'secret': Secret
        }[request.GET['permission']]

        user: Any = request.GET.get('user')
        if user:
            user = Bunch(username=user, id=uuid4(), groups=[], role=None)

        if request.has_permission(self, permission, user):
            return 'true'
        return 'false'

    @App.view(model=Root, permission=Public, name='login')
    def login(self: Root, request: CoreRequest) -> str:

        @request.after
        def remember_identity(response: Response) -> None:
            request.app.remember_identity(response, request, morepath.Identity(
                uid='1',
                userid='foo',
                groupids=frozenset({'admins'}),
                role='admin',
                application_id=request.app.application_id
            ))

        return 'ok'

    @App.permission_rule(model=Root, permission=object, identity=None)
    def has_permission_not_logged_in(
        identity: None,
        model: Root,
        permission: object
    ) -> bool:
        return permission is Public

    @App.permission_rule(model=Root, permission=object)
    def has_permission_logged_in(
        identity: morepath.Identity,
        model: Root,
        permission: object
    ) -> bool:
        return permission in model.allowed_for

    scan_morepath_modules(App)
    App.commit()

    app = App()

    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/test')

    c = Client(app)

    assert c.get('/?permission=public').text == 'true'
    assert c.get('/?permission=personal').text == 'false'
    assert c.get('/?permission=private').text == 'false'
    assert c.get('/?permission=secret').text == 'false'

    assert c.get('/?user=foo&permission=public').text == 'true'
    assert c.get('/?user=foo&permission=personal').text == 'true'
    assert c.get('/?user=foo&permission=private').text == 'true'
    assert c.get('/?user=foo&permission=secret').text == 'true'

    c.get('/login')

    assert c.get('/?permission=public').text == 'true'
    assert c.get('/?permission=personal').text == 'true'
    assert c.get('/?permission=private').text == 'true'
    assert c.get('/?permission=secret').text == 'true'


def test_permission_by_view(redis_url: str) -> None:
    class App(Framework):
        pass

    @App.path(path='/')
    class Root:
        pass

    @App.view(model=Root, name='public', permission=Public)
    def public_view(self: Root, request: CoreRequest) -> None:
        raise AssertionError()  # we don't want this view to be called

    @App.view(model=Root, name='personal', permission=Personal)
    def personal_view(self: Root, request: CoreRequest) -> None:
        raise AssertionError()  # we don't want this view to be called

    @App.view(model=Root, name='private', permission=Private)
    def private_view(self: Root, request: CoreRequest) -> None:
        raise AssertionError()  # we don't want this view to be called

    @App.view(model=Root, name='secret', permission=Secret)
    def secret_view(self: Root, request: CoreRequest) -> None:
        raise AssertionError()  # we don't want this view to be called

    @App.view(model=Root, name='login', permission=Public)
    def login(self: Root, request: CoreRequest) -> str:

        @request.after
        def remember_identity(response: Response) -> None:
            request.app.remember_identity(response, request, morepath.Identity(
                uid='1',
                userid='foo',
                groupids=frozenset(),
                role='admin',
                application_id=request.app.application_id,
            ))

        return 'ok'

    @App.view(model=Root)
    def view(self: Root, request: CoreRequest) -> str:
        url = request.GET['url']
        return request.has_access_to_url(url) and 'true' or 'false'

    scan_morepath_modules(App)
    App.commit()

    app = App()

    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/test')

    c = Client(app)

    def has_access(url: str) -> bool:
        return c.get(f'/?url={quote(url)}').text == 'true'

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
        assert has_access(f'{domain}/')
        assert has_access(f'{domain}/login')
        assert has_access(f'{domain}/public')
        assert not has_access(f'{domain}/personal')
        assert not has_access(f'{domain}/private')
        assert not has_access(f'{domain}/secret')

    c.get('/login')

    for domain in ('', 'https://example.org'):
        assert has_access(f'{domain}/')
        assert has_access(f'{domain}/login')
        assert has_access(f'{domain}/public')
        assert has_access(f'{domain}/personal')
        assert has_access(f'{domain}/private')
        assert has_access(f'{domain}/secret')
