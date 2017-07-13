from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_principal(gazette_app):
    client = Client(gazette_app)

    assert 'auth/login' in client.get('/').follow().request.url

    login_admin(client)
    assert '/users' in client.get('/').follow().request.url

    login_publisher(client)
    assert '/notices' in client.get('/').follow().request.url

    login_editor(client)
    assert '/dashboard' in client.get('/').follow().request.url
