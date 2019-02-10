from webtest import TestApp as Client


def test_view_home(swissvotes_app):
    client = Client(swissvotes_app)
    home = client.get('/').maybe_follow()
    assert "<h2>home</h2>" in home
    assert home.request.url.endswith('page/home')
