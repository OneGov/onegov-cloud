from webtest import TestApp as Client


def test_view_change_site_locale(swissvotes_app):
    client = Client(swissvotes_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    page = client.get('/').maybe_follow()
    assert "Abmelden" in page
    assert "Se déconnecter" not in page
    assert "Logout" not in page

    client.get('/locale/fr_CH').follow()
    page = client.get('/').maybe_follow()
    assert "Abmelden" not in page
    assert "Se déconnecter" in page
    assert "Logout" not in page

    client.get('/locale/en_US').follow()
    page = client.get('/').maybe_follow()
    assert "Abmelden" not in page
    assert "Se déconnecter" not in page
    assert "Logout" in page

    client.get('/locale/de_CH').follow()
    page = client.get('/').maybe_follow()
    assert "Abmelden" in page
    assert "Se déconnecter" not in page
    assert "Logout" not in page
