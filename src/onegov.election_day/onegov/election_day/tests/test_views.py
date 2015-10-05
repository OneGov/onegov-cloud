import onegov.election_day

from onegov.testing import utils
from webtest import TestApp as Client


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.election_day)


def test_view_login_logout(election_day_app):
    client = Client(election_day_app)

    login = client.get('/').click('Anmelden')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter1'

    assert "Unbekannter Benutzername oder falsches Passwort" \
        in login.form.submit()
    assert 'Anmelden' in client.get('/')

    login.form['password'] = 'hunter2'
    homepage = login.form.submit().follow()

    assert 'Sie sind angemeldet' in homepage
    assert 'Abmelden' in homepage
    assert 'Anmelden' not in homepage

    assert 'Anmelden' in client.get('/').click('Abmelden').follow()
