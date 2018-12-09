from webtest import TestApp as Client


def test_view_change_site_locale(swissvotes_app):
    client = Client(swissvotes_app)

    page = client.get('/').maybe_follow()
    assert "Anmelden" in page
    assert "Se connecter" not in page
    assert "Login" not in page

    client.get('/locale/fr_CH').follow()
    page = client.get('/').maybe_follow()
    assert "Anmelden" not in page
    assert "Se connecter" in page
    assert "Login" not in page

    client.get('/locale/en_US').follow()
    page = client.get('/').maybe_follow()
    assert "Anmelden" not in page
    assert "Se connecter" not in page
    assert "Login" in page

    client.get('/locale/de_CH').follow()
    page = client.get('/').maybe_follow()
    assert "Anmelden" in page
    assert "Se connecter" not in page
    assert "Login" not in page
