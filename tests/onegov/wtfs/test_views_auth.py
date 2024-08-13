import onegov
import os
import pyotp
import transaction

from lxml.html import document_fromstring
from onegov.user import UserCollection
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client, utils


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.wtfs,
        onegov.wtfs.WtfsApp
    )


def test_view_login_logout(client):
    error = "Unbekannter Benutzername oder falsches Passwort"

    for user in ('admin', 'editor', 'member'):
        login = client.get('/').maybe_follow().click('Anmelden')
        login.form['username'] = f'{user}@example.org'
        login.form['password'] = 'hunter1'
        page = login.form.submit().maybe_follow()
        assert error in page
        assert 'Abmelden' not in page
        assert 'Anmelden' in page

        login = client.get('/').maybe_follow().click('Anmelden')
        login.form['username'] = f'{user}@example.org'
        login.form['password'] = 'hunter2'
        page = login.form.submit().maybe_follow()
        assert error not in page
        assert 'Abmelden' in page
        assert 'Anmelden' not in page

        page = page.click('Abmelden').maybe_follow()
        assert 'Abmelden' not in page
        assert 'Anmelden' in page


def test_view_reset_password(wtfs_app):
    client = Client(wtfs_app)

    home = client.get('/').maybe_follow()

    request_page = home.click('Anmelden').click('Passwort zurücksetzen')
    request_page.form['email'] = 'someone@example.org'
    request_page.form.submit()
    assert len(os.listdir(wtfs_app.maildir)) == 0

    request_page.form['email'] = 'admin@example.org'
    request_page.form.submit()
    assert len(os.listdir(wtfs_app.maildir)) == 1

    message = client.get_email(0)
    message = message['HtmlBody']
    link = list(document_fromstring(message).iterlinks())[0][2]
    token = link.split('token=')[1]

    reset_page = client.get(link)
    assert token in reset_page.text

    reset_page.form['email'] = 'someone_else@example.org'
    reset_page.form['password'] = 'password1'
    reset_page = reset_page.form.submit()
    assert "Ungültige E-Mail oder abgelaufener Link" in reset_page
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = '1234'
    reset_page = reset_page.form.submit()
    assert "Feld muss mindestens 8 Zeichen beinhalten" in reset_page
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'password2'
    assert "Passwort geändert" in reset_page.form.submit().maybe_follow()

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'password3'
    reset_page = reset_page.form.submit()
    assert "Ungültige E-Mail oder abgelaufener Link" in reset_page

    login_page = client.get('/auth/login')
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page = login_page.form.submit()
    assert "Unbekannter Benutzername oder falsches Passwort" in login_page

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'password2'
    login_page = login_page.form.submit().maybe_follow()
    assert "Abmelden" in login_page.maybe_follow()


def test_login_totp(wtfs_app):
    wtfs_app.totp_enabled = True
    client = Client(wtfs_app)

    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)

    # configure TOTP for admin user
    users = UserCollection(client.app.session())
    admin = users.by_username('admin@example.org')
    admin.second_factor = {'type': 'totp', 'data': totp_secret}
    transaction.commit()
    close_all_sessions()

    login_page = client.get('/').maybe_follow().click('Anmelden')
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    totp_page = login_page.form.submit().maybe_follow()
    assert "Bitte geben Sie den sechsstelligen Code" in totp_page.text
    totp_page.form['totp'] = 'bogus'
    totp_page = totp_page.form.submit()
    assert "Ungültige oder abgelaufenes TOTP eingegeben." in totp_page.text

    totp_page.form['totp'] = totp.now()
    page = totp_page.form.submit().maybe_follow()
    assert 'Abmelden' in page
    assert 'Anmelden' not in page

    page = client.get('/').maybe_follow().click('Abmelden').maybe_follow()
    assert 'Abmelden' not in page
    assert 'Anmelden' in page
