from morepath import setup
from onegov.core import Framework
from onegov.core.security import Secret
from webtest import TestApp as Client
from wtforms import Form


def test_form_directive():
    config = setup()

    class App(Framework):
        testing_config = config

    @App.path(path='/')
    class Root(object):
        pass

    @App.form(model=Root, form=Form)
    def handle_form(self, request, form):
        return ' '.join(('1', request.method, form.action))

    @App.form(model=Root, name='separate', request_method='GET', form=Form)
    def get_form(self, request, form):
        return ' '.join(('2', request.method, form.action))

    @App.form(model=Root, name='separate', request_method='POST', form=Form)
    def post_form(self, request, form):
        return ' '.join(('3', request.method, form.action))

    @App.form(model=Root, name='1', form=Form, permission=Secret)
    def handle_blocked_one(self, request, form):
        pass

    @App.form(model=Root, name='2', form=Form, permission=Secret,
              request_method='GET')
    def handle_blocked_two(self, request, form):
        pass

    @App.form(model=Root, name='3', form=Form, permission=Secret,
              request_method='POST')
    def handle_blocked_three(self, request, form):
        pass

    config.commit()

    app = App()
    app.application_id = 'test'
    app.configure_application(
        identity_secure=False,
        disable_memcached=True
    )

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
