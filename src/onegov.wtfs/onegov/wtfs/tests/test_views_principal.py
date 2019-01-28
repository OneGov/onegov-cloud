from webtest import TestApp as Client


def test_view_home(wtfs_app):
    client = Client(wtfs_app)
    assert 'auth/login' in client.get('/').follow().request.url
