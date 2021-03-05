import re
from lxml.html import document_fromstring
from purl import URL
from pytest import mark


def test_view_login(client):
    assert client.get('/auth/logout', expect_errors=True).status_code == 403

    response = client.get('/auth/login')

    # German is the default translation and there's no English translation yet
    # (the default *is* English, but it needs to be added as a locale, or it
    # won't be used)
    assert response.status_code == 200
    assert "E-Mail Adresse" in response
    assert "Passwort" in response

    assert client.get('/auth/logout', expect_errors=True).status_code == 403

    response.form.set('username', 'admin@example.org')
    response = response.form.submit()
    assert response.status_code == 200
    assert "E-Mail Adresse" in response
    assert "Passwort" in response
    assert "Dieses Feld wird benötigt." in response
    assert client.get('/auth/logout', expect_errors=True).status_code == 403

    response.form.set('username', 'admin@example.org')
    response.form.set('password', 'hunter2')
    response = response.form.submit()

    assert response.status_code == 302
    assert client.logout().status_code == 302
    assert client.get('/auth/logout', expect_errors=True).status_code == 403


def test_login(client):
    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Anmelden'

    login_page = client.get(links.attr('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = ''
    login_page = login_page.form.submit()

    assert "Dieses Feld wird benötigt" in login_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'wrong'
    login_page = login_page.form.submit()

    assert "Falsche E-Mail Adresse, falsches Passwort oder falscher Yubikey."\
        in login_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    index_page = login_page.form.submit().follow()
    assert "Sie wurden angemeldet" in index_page.text

    links = index_page.pyquery('.globals a.logout')
    assert links.text() == 'Abmelden'

    index_page = client.get(links.attr('href')).follow()
    links = index_page.pyquery('.globals a.login')
    assert links.text() == 'Anmelden'


def test_reset_password(client):
    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Anmelden'
    login_page = client.get(links.attr('href'))

    request_page = login_page.click('Passwort zurücksetzen')
    assert 'Passwort zurücksetzen' in request_page.text

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit().follow()
    assert len(client.app.smtp.outbox) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit().follow()
    assert len(client.app.smtp.outbox) == 1

    message = client.app.smtp.outbox[0]
    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('iso-8859-1')
    link = list(document_fromstring(message).iterlinks())[0][2]
    token = link.split('token=')[1]

    reset_page = client.get(link)
    assert token in reset_page.text

    reset_page.form['email'] = 'someone_else@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Adresse oder abgelaufener Link" in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = '1234'
    reset_page = reset_page.form.submit()
    assert "Feld muss mindestens 8 Zeichen beinhalten" in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    homepage = reset_page.form.submit().follow().text
    assert "Passwort geändert" in homepage
    assert "Anmelden" in homepage  # do not automatically log in the user

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Adresse oder abgelaufener Link" in reset_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page = login_page.form.submit()
    assert "Falsche E-Mail Adresse, falsches Passwort oder falscher Yubikey."\
        in login_page.text

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'new_password'
    assert "Sie wurden angemeldet" in login_page.form.submit().follow().text


def test_unauthorized(client):

    unauth_page = client.get('/settings', expect_errors=True)
    assert "Zugriff verweigert" in unauth_page.text
    assert "folgen Sie diesem Link um sich anzumelden" in unauth_page.text

    link = unauth_page.pyquery('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['username'] = 'editor@example.org'
    login_page.form['password'] = 'hunter2'
    unauth_page = login_page.form.submit().follow(expect_errors=True)

    assert "Zugriff verweigert" in unauth_page.text
    assert "mit einem anderen Benutzer anzumelden" in unauth_page.text

    link = unauth_page.pyquery('#alternate-login-link')[0]
    login_page = client.get(link.attrib.get('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    settings_page = login_page.form.submit().follow()

    assert settings_page.status_code == 200
    assert "Zugriff verweigert" not in settings_page


def test_registration_honeypot(client):
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'spam@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'
    register.form['roboter_falle'] = 'buy pills now'

    assert "Das Feld ist nicht leer" in register.form.submit()


@mark.skip(reason='Passes locally, but not in CI, skip for now')
def test_registration(client):
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'user@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'

    assert "Vielen Dank" in register.form.submit().follow()

    message = client.get_email(0, 1)
    assert "Anmeldung bestätigen" in message

    expr = r'href="[^"]+">Anmeldung bestätigen</a>'
    url = re.search(expr, message).group()
    url = client.extract_href(url)

    faulty = URL(url).query_param('token', 'asdf').as_string()

    assert "Ungültiger Aktivierungscode" in client.get(faulty).follow()
    assert "Konto wurde aktiviert" in client.get(url).follow()
    assert "Konto wurde bereits aktiviert" in client.get(url).follow()

    logged_in = client.login('user@example.org', 'p@ssw0rd').follow()
    assert "angemeldet" in logged_in


def test_registration_disabled(client):

    client.app.enable_user_registration = False

    assert client.get('/auth/register', status=404)


def test_disabled_yubikey(client):
    client.login_admin()

    client.app.enable_yubikey = False
    assert 'YubiKey' not in client.get('/auth/login')
    assert 'YubiKey' not in client.get('/usermanagement')

    client.app.enable_yubikey = True
    assert 'YubiKey' in client.get('/auth/login')
    assert 'YubiKey' in client.get('/usermanagement')


def test_login_with_required_userprofile(client):
    # userprofile is not complete
    client.app.settings.org.require_complete_userprofile = True
    client.app.settings.org.is_complete_userprofile = lambda r, u: False

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'wrong-password'
    page = page.form.submit()

    assert 'falsches Passwort' in page

    page.form['password'] = 'hunter2'
    page = page.form.submit().follow()

    assert 'userprofile' in page.request.url
    assert "Ihr Benutzerprofil ist unvollständig" in page
    page = page.form.submit().follow()

    assert 'settings' in page.request.url

    # userprofile is complete
    client.app.settings.org.require_complete_userprofile = True
    client.app.settings.org.is_complete_userprofile = lambda r, u: True

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'hunter2'
    page = page.form.submit()

    assert 'settings' in page.request.url

    # completeness not required
    client.app.settings.org.require_complete_userprofile = False
    client.app.settings.org.is_complete_userprofile = lambda r, u: True

    page = client.get('/auth/login?to=/settings')
    page.form['username'] = 'admin@example.org'
    page.form['password'] = 'hunter2'
    page = page.form.submit()

    assert 'settings' in page.request.url
