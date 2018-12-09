from webtest import TestApp as Client


def test_view_home(swissvotes_app):
    client = Client(swissvotes_app)
    home = client.get('/').follow()
    assert "Startseite" in home
    assert home.request.url.endswith('page/home')
