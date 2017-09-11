from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_principal(gazette_app):
    client = Client(gazette_app)

    assert 'auth/login' in client.get('/').maybe_follow().request.url

    login_admin(client)
    assert '/users' in client.get('/').maybe_follow().request.url

    login_publisher(client)
    assert '/notices' in client.get('/').maybe_follow().request.url

    login_editor_1(client)
    assert '/dashboard' in client.get('/').maybe_follow().request.url
