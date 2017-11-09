from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_principal(gazette_app):
    client = Client(gazette_app)

    assert 'auth/login' in client.get('/').maybe_follow().request.url

    login_admin(client)
    assert '/notices' in client.get('/').maybe_follow().request.url

    login_publisher(client)
    assert '/notices' in client.get('/').maybe_follow().request.url

    login_editor_1(client)
    assert '/dashboard' in client.get('/').maybe_follow().request.url


def test_view_help_link(gazette_app):
    client = Client(gazette_app)

    result = client.get('/').maybe_follow()
    assert 'Hilfe' not in result

    principal = gazette_app.principal
    principal.help_link = 'https://help.me'
    gazette_app.cache.set('principal', principal)

    result = client.get('/').maybe_follow()
    assert 'Hilfe' in result
    assert 'https://help.me' in result
