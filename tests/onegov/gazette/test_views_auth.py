import onegov.gazette
import os
import pyotp
import transaction

from lxml.html import document_fromstring
from onegov.user import UserCollection
from pytest import mark
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client, utils


@mark.skip('Will mess up tests in the CI')
def test_view_permissions():
    # Probably colliding with the same test from the org package?
    # utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)
    utils.assert_explicit_permissions(
        onegov.gazette,
        onegov.gazette.GazetteApp
    )


def test_view_login_logout(gazette_app):
    client = Client(gazette_app)

    for username, realname in (
        ('admin@example.org', ''),
        ('editor1@example.org', 'First Editor'),
        ('editor2@example.org', 'Second Editor'),
        ('editor3@example.org', 'Third Editor'),
        ('publisher@example.org', 'Publisher'),
    ):
        login = client.get('/').maybe_follow().click('Anmelden')
        login.form['username'] = username
        login.form['password'] = 'hunter1'

        assert "Unbekannter Benutzername oder falsches Passwort" \
            in login.form.submit()
        assert 'Anmelden' in client.get('/').maybe_follow()

        login.form['password'] = 'hunter2'
        page = login.form.submit().maybe_follow()

        assert f'Angemeldet als {realname or username}' in page
        assert 'Abmelden' in page
        assert 'Anmelden' not in page

        page = client.get('/').maybe_follow().click('Abmelden').maybe_follow()
        assert 'Sie sind angemeldet' not in page
        assert 'Abmelden' not in page
        assert 'Anmelden' in page


def test_view_reset_password(gazette_app):
    client = Client(gazette_app)

    request_page = client.get('/auth/login').click('Passwort zurücksetzen')
    assert 'Passwort zurücksetzen' in request_page

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit()
    assert len(os.listdir(gazette_app.maildir)) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit()
    assert len(os.listdir(gazette_app.maildir)) == 1

    message = client.get_email(0)['HtmlBody']
    link = list(document_fromstring(message).iterlinks())[0][2]
    token = link.split('token=')[1]

    reset_page = client.get(link)
    assert token in reset_page.text

    reset_page.form['email'] = 'someone_else@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Adresse oder abgelaufener Link" in reset_page
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = '1234'
    reset_page = reset_page.form.submit()
    assert "Feld muss mindestens 8 Zeichen beinhalten" in reset_page
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    assert "Passwort geändert" in reset_page.form.submit().maybe_follow()

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'new_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Adresse oder abgelaufener Link" in reset_page

    login_page = client.get('/auth/login')
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page = login_page.form.submit()
    assert "Unbekannter Benutzername oder falsches Passwort" in login_page

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'new_password'
    login_page = login_page.form.submit().maybe_follow()
    assert "Angemeldet als admin@example.org" in login_page.maybe_follow()


def test_login_totp(gazette_app):
    gazette_app.totp_enabled = True
    client = Client(gazette_app)

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
    assert "TOTP eingeben" in totp_page.text
    totp_page.form['totp'] = 'bogus'
    totp_page = totp_page.form.submit()
    assert "Ungültige oder abgelaufenes TOTP eingegeben." in totp_page.text

    totp_page.form['totp'] = totp.now()
    page = totp_page.form.submit().maybe_follow()

    assert 'Angemeldet als admin@example.org' in page
    assert 'Abmelden' in page
    assert 'Anmelden' not in page

    page = client.get('/').maybe_follow().click('Abmelden').maybe_follow()
    assert 'Sie sind angemeldet' not in page
    assert 'Abmelden' not in page
    assert 'Anmelden' in page
