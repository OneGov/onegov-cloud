from __future__ import annotations

from onegov.core.directives import query_form_class
from onegov.core.framework import Framework
from onegov.core.security import Secret
from webtest import TestApp as Client
from wtforms import Form


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest


def test_form_directive(redis_url: str) -> None:

    class App(Framework):
        pass

    @App.path(path='/')
    class Root:
        pass

    @App.form(model=Root, form=Form)
    def handle_form(self: Root, request: CoreRequest, form: Form) -> str:
        return ' '.join(('1', request.method, form.action))  # type: ignore[attr-defined]

    @App.form(model=Root, name='separate', request_method='GET', form=Form)
    def get_form(self: Root, request: CoreRequest, form: Form) -> str:
        return ' '.join(('2', request.method, form.action))  # type: ignore[attr-defined]

    @App.form(model=Root, name='separate', request_method='POST', form=Form)
    def post_form(self: Root, request: CoreRequest, form: Form) -> str:
        return ' '.join(('3', request.method, form.action))  # type: ignore[attr-defined]

    @App.form(model=Root, name='1', form=Form, permission=Secret)
    def handle_blocked_one(
        self: Root,
        request: CoreRequest,
        form: Form
    ) -> None:
        pass

    @App.form(model=Root, name='2', form=Form, permission=Secret,
              request_method='GET')
    def handle_blocked_two(
        self: Root,
        request: CoreRequest,
        form: Form
    ) -> None:
        pass

    @App.form(model=Root, name='3', form=Form, permission=Secret,
              request_method='POST')
    def handle_blocked_three(
        self: Root,
        request: CoreRequest,
        form: Form
    ) -> None:
        pass

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/foo')

    client = Client(app)
    assert client.get('/').text == '1 GET http://localhost/'
    assert client.post('/').text == '1 POST http://localhost/'
    assert client.get('/separate').text == '2 GET http://localhost/separate'
    assert client.post('/separate').text == '3 POST http://localhost/separate'

    assert client.get('/1', expect_errors=True).status_code == 403
    assert client.post('/1', expect_errors=True).status_code == 403
    assert client.get('/2', expect_errors=True).status_code == 403
    assert client.post('/2', expect_errors=True).status_code == 405
    assert client.get('/3', expect_errors=True).status_code == 405
    assert client.post('/3', expect_errors=True).status_code == 403


def test_query_form_class(redis_url: str) -> None:

    class FormA(Form):
        pass

    class FormB(Form):
        pass

    def get_form_b(self: Root, request: CoreRequest) -> type[FormB]:
        return FormB

    class App(Framework):
        pass

    @App.path(path='/')
    class Root:
        pass

    @App.form(model=Root, form=FormA)
    def handle_form(self: Root, request: CoreRequest, form: FormA) -> str:
        return ''

    @App.form(model=Root, name='b', form=get_form_b)
    def get_form(self: Root, request: CoreRequest, form: FormB) -> str:
        return ''

    @App.view(model=Root, name='assert-form-a')
    def assert_form_a(self: Root, request: CoreRequest) -> None:
        assert query_form_class(request, Root) is FormA

    @App.view(model=Root, name='assert-form-b')
    def assert_form_b(self: Root, request: CoreRequest) -> None:
        assert query_form_class(request, Root, name='b') is FormB

    @App.view(model=Root, name='assert-form-missing')
    def assert_form_c(self: Root, request: CoreRequest) -> None:
        assert query_form_class(request, Root, name='foobar') is None

    App.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.set_application_id('test/foo')

    client = Client(app)
    assert client.get('/assert-form-a')
    assert client.get('/assert-form-b')
    assert client.get('/assert-form-missing')
