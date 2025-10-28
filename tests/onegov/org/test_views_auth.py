from __future__ import annotations

import json
import os
import pyotp
import re
import transaction

from freezegun import freeze_time
from lxml.html import document_fromstring
from onegov.org.models import TANAccessCollection
from onegov.user import UserCollection
from sqlalchemy.orm.session import close_all_sessions

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_login(client: Client) -> None:
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


def test_login(client: Client) -> None:
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


def test_login_setup_mtan(client: Client, smsdir: str) -> None:
    client.app.mtan_second_factor_enabled = True
    client.app.mtan_automatic_setup = True
    # descend to app-specific sms directory
    smsdir = os.path.join(smsdir, client.app.schema)

    client2 = client.spawn()
    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Anmelden'

    login_page = client.get(links.attr('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    mtan_setup_page = login_page.form.submit().follow()
    assert "Sie wurden angemeldet" not in mtan_setup_page.text
    assert "mTAN aktivieren" in mtan_setup_page.text
    mtan_setup_page.form['phone_number'] = '078 720 20 20'

    mtan_page = mtan_setup_page.form.submit().follow()
    assert "Wir haben einen mTAN" in mtan_page.text
    assert "mTAN eingeben" in mtan_page.text
    sms_files = os.listdir(smsdir)
    assert len(sms_files) == 1
    sms_path = os.path.join(smsdir, sms_files[0])
    with open(sms_path) as fd:
        content = json.loads(fd.read())
    os.unlink(sms_path)
    mtan_page.form['tan'] = 'bogus'
    mtan_page = mtan_page.form.submit()
    assert "Ungültige oder abgelaufene mTAN eingegeben." in mtan_page.text

    mtan = content['content'].split(' ', 1)[0]
    mtan_page.form['tan'] = mtan

    index_page = mtan_page.form.submit().follow()
    assert "Sie wurden angemeldet" in index_page.text

    users_page = client.get('/usermanagement')
    assert 'mTAN' in users_page
    assert '+41787202020' in users_page

    links = index_page.pyquery('.globals a.logout')
    assert links.text() == 'Abmelden'

    index_page = client.get(links.attr('href')).follow()
    links = index_page.pyquery('.globals a.login')
    assert links.text() == 'Anmelden'

    # now test a regular login without mTAN setup step
    login_page = client.get(links.attr('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    mtan_page = login_page.form.submit().follow()
    assert "mTAN eingeben" in mtan_page.text
    assert "mTAN aktivieren" not in mtan_page.text
    assert "Sie wurden angemeldet" not in mtan_page.text
    sms_files = os.listdir(smsdir)
    assert len(sms_files) == 1
    sms_path = os.path.join(smsdir, sms_files[0])
    with open(sms_path) as fd:
        content = json.loads(fd.read())
    mtan = content['content'].split(' ', 1)[0]

    # we do it one more time because we're impatient
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page.form.submit().follow()

    sms_files2 = os.listdir(smsdir)
    assert len(sms_files2) == 2
    sms_path2 = os.path.join(smsdir, next(
        file
        for file in sms_files2
        if file != sms_files[0]
    ))
    with open(sms_path2) as fd:
        content2 = json.loads(fd.read())
    mtan2 = content2['content'].split(' ', 1)[0]

    mtan_page.form['tan'] = mtan
    index_page = mtan_page.form.submit().follow()
    assert "Sie wurden angemeldet" in index_page.text

    # someone else can't reuse the same mTAN
    links = client2.get('/').pyquery('.globals a.login')
    assert links.text() == 'Anmelden'

    login_page = client2.get(links.attr('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    mtan_page = login_page.form.submit().follow()
    mtan_page.form['tan'] = mtan
    mtan_page = mtan_page.form.submit()
    assert 'Ungültige oder abgelaufene mTAN' in mtan_page

    # and they also can't use the redundant mTAN we didn't end up using
    mtan_page.form['tan'] = mtan
    mtan_page = mtan_page.form.submit()
    assert 'Ungültige oder abgelaufene mTAN' in mtan_page

def test_login_totp(client: Client, test_password: str) -> None:
    client.app.totp_enabled = True
    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)

    # configure TOTP for admin user
    users = UserCollection(client.app.session())
    admin = users.by_username('admin@example.org')
    assert admin is not None
    admin.second_factor = {'type': 'totp', 'data': totp_secret}
    transaction.commit()
    close_all_sessions()

    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Anmelden'

    login_page = client.get(links.attr('href'))
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    totp_page = login_page.form.submit().follow()
    assert "TOTP eingeben" in totp_page.text
    totp_page.form['totp'] = 'bogus'
    totp_page = totp_page.form.submit()
    assert "Ungültige oder abgelaufenes TOTP eingegeben." in totp_page.text

    totp_page.form['totp'] = totp.now()
    index_page = totp_page.form.submit().follow()
    assert "Sie wurden angemeldet" in index_page.text

    links = index_page.pyquery('.globals a.logout')
    assert links.text() == 'Abmelden'

    index_page = client.get(links.attr('href')).follow()
    links = index_page.pyquery('.globals a.login')
    assert links.text() == 'Anmelden'


def test_reset_password(client: Client) -> None:
    links = client.get('/').pyquery('.globals a.login')
    assert links.text() == 'Anmelden'
    login_page = client.get(links.attr('href'))

    request_page = login_page.click('Passwort zurücksetzen')
    assert 'Passwort zurücksetzen' in request_page.text

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 1

    message = client.get_email(0)['HtmlBody']
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

    # Deactivate member login
    client.login_admin()
    page = client.get('/usermanagement')
    page = page.click('Ansicht', index=2)
    page = page.click('Bearbeiten')
    page.form['state'] = 'inactive'
    assert page.form.submit().status_code == 302
    client.logout()

    # Do not send email if user is deactivated
    assert 'Passwort zurücksetzen' in request_page.text
    request_page.form['email'] = 'member@example.org'
    request_page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 1


def test_unauthorized(client: Client) -> None:

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


def test_registration_honeypot(client: Client) -> None:
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'spam@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'
    register.form['roboter_falle'] = 'buy pills now'

    assert "Das Feld ist nicht leer" in register.form.submit()


def test_registration(client: Client) -> None:
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'user@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'

    assert "Vielen Dank" in register.form.submit().follow()

    message = client.get_email(0)['HtmlBody']
    assert "Anmeldung bestätigen" in message

    expr = r'href="[^"]+">Anmeldung bestätigen</a>'
    url = re.search(expr, message).group()  # type: ignore[union-attr]
    url = client.extract_href(url)
    assert url is not None

    assert "Konto wurde aktiviert" in client.get(url).follow()
    assert "Konto wurde bereits aktiviert" in client.get(url).follow()

    logged_in = client.login('user@example.org', 'p@ssw0rd').follow()
    assert "angemeldet" in logged_in


def test_registration_disabled(client: Client) -> None:

    client.app.enable_user_registration = False

    assert client.get('/auth/register', status=404)


def test_disabled_yubikey(client: Client) -> None:
    client.login_admin()

    client.app.enable_yubikey = False
    assert 'YubiKey' not in client.get('/auth/login')
    assert 'YubiKey' not in client.get('/usermanagement')

    client.app.enable_yubikey = True
    assert 'YubiKey' in client.get('/auth/login')
    assert 'YubiKey' in client.get('/usermanagement')


def test_disabled_mtan(client: Client) -> None:
    client.login_admin()

    client.app.mtan_second_factor_enabled = False
    assert 'mTAN' not in client.get('/usermanagement')

    client.app.mtan_second_factor_enabled = True
    assert 'mTAN' in client.get('/usermanagement')


def test_login_with_required_userprofile(client: Client) -> None:
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


def test_mtan_access(client: Client, smsdir: str) -> None:
    client.login_editor()

    new_page = client.get('/topics/organisation').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['access'] = 'mtan'
    new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    # editors and admins should still have normal access
    client.get(page_url, status=200)

    anonymous = client.spawn()
    mtan_page = anonymous.get(page_url, status=302).follow()
    assert 'mTAN' in mtan_page
    mtan_page.form['phone_number'] = '+41791112233'
    verify_page = mtan_page.form.submit().follow()

    smsdir = os.path.join(smsdir, client.app.schema)
    files = os.listdir(smsdir)
    assert len(files) == 1

    with open(os.path.join(smsdir, files[0]), mode='r') as fp:
        sms_content = json.loads(fp.read())

    assert sms_content['receivers'] == ['+41791112233']
    # tan should be the last url parameter in the SMS
    _, _, tan = sms_content['content'].rpartition('=')

    # because we're impatient we request another mTAN
    mtan_page.form['phone_number'] = '+41791112233'
    mtan_page.form.submit().follow()
    files2 = os.listdir(smsdir)
    assert len(files2) == 2
    new_file = next(file for file in files2 if file != files[0])

    with open(os.path.join(smsdir, new_file), mode='r') as fp:
        sms_content2 = json.loads(fp.read())

    assert sms_content2['receivers'] == ['+41791112233']
    _, _, tan2 = sms_content2['content'].rpartition('=')

    verify_page.form['tan'] = tan
    page = verify_page.form.submit().follow()
    assert 'Test' in page

    # the access to the protected page should have been logged
    accesses = TANAccessCollection(
        client.app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1
    assert accesses[0].url.endswith(page_url)

    # now that we're authenticated we should be able to
    # access the page normally on subsequent requests
    anonymous.get(page_url, status=200)

    # the second access should not create a new entry
    accesses = TANAccessCollection(
        client.app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1

    # a second anonymous user should not have access however
    anonymous2 = client.spawn()
    mtan_page = anonymous2.get(page_url, status=302).follow()
    assert 'mTAN' in mtan_page
    mtan_page.form['phone_number'] = '+41791112233'
    verify_page = mtan_page.form.submit().follow()

    # the second user should not be able to re-use the mTAN
    # from the first one
    verify_page.form['tan'] = tan
    verify_page = verify_page.form.submit()
    assert 'Ungültige oder abgelaufene mTAN' in verify_page

    # the second user should also not be able to use the redundant
    # mTAN we didn't end up using
    verify_page.form['tan'] = tan2
    verify_page = verify_page.form.submit()
    assert 'Ungültige oder abgelaufene mTAN' in verify_page


def test_mtan_access_from_sms_url(client: Client, smsdir: str) -> None:
    client.login_editor()

    new_page = client.get('/topics/organisation').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['access'] = 'mtan'
    new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    # editors and admins should still have normal access
    client.get(page_url, status=200)

    anonymous = client.spawn()
    mtan_page = anonymous.get(page_url, status=302).follow()
    assert 'mTAN' in mtan_page
    mtan_page.form['phone_number'] = '+41791112233'
    verify_page = mtan_page.form.submit().follow()

    smsdir = os.path.join(smsdir, client.app.schema)
    files = os.listdir(smsdir)
    assert len(files) == 1

    with open(os.path.join(smsdir, files[0]), mode='r') as fp:
        sms_content = json.loads(fp.read())

    assert sms_content['receivers'] == ['+41791112233']
    # tan should be the last url parameter in the SMS
    _, _, tan = sms_content['content'].rpartition('=')
    assert f'/mtan/auth?tan={tan}' in sms_content['content']

    # we should not have to enter anything it should just submit
    # and we should end up where we started despite the missing to
    # in the url
    verify_page = anonymous.get(f'/mtan/auth?tan={tan}')
    page = verify_page.form.submit().follow()
    assert 'Test' in page

    # the access to the protected page should have been logged
    accesses = TANAccessCollection(
        client.app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1
    assert accesses[0].url.endswith(page_url)

    # now that we're authenticated we should be able to
    # access the page normally on subsequent requests
    anonymous.get(page_url, status=200)

    # the second access should not create a new entry
    accesses = TANAccessCollection(
        client.app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1

    # a second anonymous user should not have access however
    anonymous2 = client.spawn()
    mtan_page = anonymous2.get(page_url, status=302).follow()
    assert 'mTAN' in mtan_page
    mtan_page.form['phone_number'] = '+41791112233'
    verify_page = mtan_page.form.submit().follow()

    # the second user should not be able to re-use the mTAN
    # from the first one
    verify_page.form['tan'] = tan
    verify_page = verify_page.form.submit()
    assert 'Ungültige oder abgelaufene mTAN' in verify_page


def test_secret_mtan_access(client: Client, smsdir: str) -> None:
    client.login_editor()

    new_page = client.get('/topics/organisation').click('Thema')

    new_page.form['title'] = "Test"
    new_page.form['access'] = 'secret_mtan'
    new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    # editors and admins should still have normal access
    client.get(page_url, status=200)

    anonymous = client.spawn()
    mtan_page = anonymous.get(page_url, status=302).follow()
    assert 'mTAN' in mtan_page
    mtan_page.form['phone_number'] = '+41791112233'
    verify_page = mtan_page.form.submit().follow()

    smsdir = os.path.join(smsdir, client.app.schema)
    files = os.listdir(smsdir)
    assert len(files) == 1

    with open(os.path.join(smsdir, files[0]), mode='r') as fp:
        sms_content = json.loads(fp.read())

    assert sms_content['receivers'] == ['+41791112233']
    # tan should be the last url parameter in the SMS
    _, _, tan = sms_content['content'].rpartition('=')

    verify_page.form['tan'] = tan
    page = verify_page.form.submit().follow()
    assert 'Test' in page

    # the access to the protected page should have been logged
    accesses = TANAccessCollection(
        client.app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1
    assert accesses[0].url.endswith(page_url)

    # now that we're authenticated we should be able to
    # access the page normally on subsequent requests
    anonymous.get(page_url, status=200)

    # the second access should not create a new entry
    accesses = TANAccessCollection(
        client.app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1

    # a second anonymous user should not have access however
    anonymous2 = client.spawn()
    mtan_page = anonymous2.get(page_url, status=302).follow()
    assert 'mTAN' in mtan_page
    mtan_page.form['phone_number'] = '+41791112233'
    verify_page = mtan_page.form.submit().follow()

    # the second user should not be able to re-use the mTAN
    # from the first one
    verify_page.form['tan'] = tan
    verify_page = verify_page.form.submit()
    assert 'Ungültige oder abgelaufene mTAN' in verify_page


def test_mtan_access_limit(client: Client, smsdir: str) -> None:
    with freeze_time("2020-10-10 08:00", tick=True):
        client.login_admin()

        # set a rate limit
        settings_page = client.get('/module-settings')
        settings_page.form['mtan_session_duration_seconds'] = '86400'
        settings_page.form['mtan_access_window_requests'] = '1'
        settings_page.form['mtan_access_window_seconds'] = '3600'
        settings_page.form.submit().follow()

        new_page = client.get('/topics/organisation').click('Thema')

        new_page.form['title'] = "Test"
        new_page.form['access'] = 'mtan'
        new_page.form.submit().follow()
        page_url = '/topics/organisation/test'

        new_page = client.get('/topics/organisation').click('Thema')

        new_page.form['title'] = "Test2"
        new_page.form['access'] = 'mtan'
        new_page.form.submit().follow()
        page2_url = '/topics/organisation/test2'

        # editors and admins should still have normal access
        client.get(page_url, status=200)
        client.get(page2_url, status=200)

        anonymous = client.spawn()
        mtan_page = anonymous.get(page_url, status=302).follow()
        assert 'mTAN' in mtan_page
        mtan_page.form['phone_number'] = '+41791112233'
        verify_page = mtan_page.form.submit().follow()

        smsdir = os.path.join(smsdir, client.app.schema)
        files = os.listdir(smsdir)
        assert len(files) == 1

        with open(os.path.join(smsdir, files[0]), mode='r') as fp:
            sms_content = json.loads(fp.read())

        assert sms_content['receivers'] == ['+41791112233']
        # tan should be the last url parameter in the SMS
        _, _, tan = sms_content['content'].rpartition('=')

        verify_page.form['tan'] = tan
        page = verify_page.form.submit().follow()
        assert 'Test' in page

        # the access to the protected page should have been logged
        accesses = TANAccessCollection(
            client.app.session(),
            session_id='+41791112233'
        ).query().all()
        assert len(accesses) == 1
        assert accesses[0].url.endswith(page_url)

        # now that we're authenticated we should be able to
        # access the page normally on subsequent requests
        anonymous.get(page_url, status=200)

        # the second access should not create a new entry
        accesses = TANAccessCollection(
            client.app.session(),
            session_id='+41791112233'
        ).query().all()
        assert len(accesses) == 1

        # a second access will exceed the access limit
        error_page = anonymous.get(page2_url, status=423)
        assert 'mTAN Zugriffslimit Überschritten' in error_page

        # since it didn't succeed it should not create a new entry
        accesses = TANAccessCollection(
            client.app.session(),
            session_id='+41791112233'
        ).query().all()
        assert len(accesses) == 1

        # but the original page should still be accesible
        anonymous.get(page_url, status=200)

    with freeze_time("2020-10-10 09:01", tick=True):
        # but an hour later we get to do a new access
        anonymous.get(page2_url, status=200)

        # which creates a new access
        accesses = TANAccessCollection(
            client.app.session(),
            session_id='+41791112233'
        ).query().all()
        assert len(accesses) == 2
        assert accesses[1].url.endswith(page2_url)

        # but now we still can't access a second page
        # even one we had accessed before
        anonymous.get(page_url, status=423)


@freeze_time("2020-10-10", tick=True)
def test_mtan_access_unauthorized_resource(
    client: Client,
    smsdir: str
) -> None:

    client.login_editor()

    new_page = client.get('/topics/organisation').click('Thema')

    new_page.form['title'] = 'Test'
    new_page.form['access'] = 'mtan'
    # publication starts in the future so the resource is not yet
    # accessible regardless of whether we enter an mTAn or not
    new_page.form['publication_start'] = '2020-11-10T08:30:00'
    new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    # editors and admins should still have normal access
    client.get(page_url, status=200)

    anonymous = client.spawn()
    unauth_page = anonymous.get(page_url, expect_errors=True)
    assert "Zugriff verweigert" in unauth_page.text
    assert "folgen Sie diesem Link um sich anzumelden" in unauth_page.text


def test_citizen_login(client: Client) -> None:
    admin = client.spawn()
    client2 = client.spawn()

    # by default it is off
    links = client.get('/').pyquery('.globals a.citizen-login')
    assert not list(links.items())
    assert client.get('/auth/citizen-login', status=404)
    assert client.get('/auth/confirm-citizen-login', status=404)

    # let's enable it
    admin.login_admin()
    settings = admin.get('/').click('Einstellungen').click('Kunden-Login')
    settings.form['citizen_login_enabled'].checked = True
    settings.form.submit().follow()

    # now it should be there
    links = client.get('/').pyquery('.globals a.citizen-login')
    assert links.text() == 'Kunden-Login'

    login_page = client.get(links.attr('href'))
    login_page.form['email'] = 'citizen@example.org'
    confirm_page = login_page.form.submit().follow()
    assert "Kunden-Login bestätigen" in confirm_page.text
    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)['TextBody']
    assert 'confirm-citizen-login' in message
    token = re.search(r'&token=([^)]+)', message).group(1)  # type: ignore[union-attr]

    # because we're impatient we request another TAN
    login_page.form['email'] = 'citizen@example.org'
    login_page.form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 2
    message2 = client.get_email(0)['TextBody']
    assert 'confirm-citizen-login' in message2
    token2 = re.search(r'&token=([^)]+)', message2).group(1)  # type: ignore[union-attr]

    # finish login with the token
    confirm_page.form['token'] = token
    index_page = confirm_page.form.submit().follow()

    links = index_page.pyquery('.globals a.logout')
    assert links.text() == 'Abmelden'

    # visiting the login/confimation view while authenticated redirects you
    assert client.get('/auth/citizen-login').follow().request.path == '/'
    assert client.get(
        '/auth/confirm-citizen-login'
    ).follow().request.path == '/'

    index_page = client.get(links.attr('href')).follow()
    links = index_page.pyquery('.globals a.citizen-login')
    assert links.text() == 'Kunden-Login'

    # a second user can't use the same token to login as well
    confirm_page = client.get('/auth/confirm-citizen-login')
    confirm_page.form['token'] = token
    login_page = confirm_page.form.submit().follow()
    assert login_page.request.path == '/auth/citizen-login'
    assert 'Ungültiger oder abgelaufener Login-Code' in login_page

    # they also can't use the redundant token, since it has been
    # invalidate as well
    confirm_page = client.get('/auth/confirm-citizen-login')
    confirm_page.form['token'] = token2
    login_page = confirm_page.form.submit().follow()
    assert login_page.request.path == '/auth/citizen-login'
    assert 'Ungültiger oder abgelaufener Login-Code' in login_page


def test_citizen_login_via_confirm_url(client: Client) -> None:
    admin = client.spawn()
    client2 = client.spawn()

    # by default it is off
    links = client.get('/').pyquery('.globals a.citizen-login')
    assert not list(links.items())

    # let's enable it
    admin.login_admin()
    settings = admin.get('/').click('Einstellungen').click('Kunden-Login')
    settings.form['citizen_login_enabled'].checked = True
    settings.form.submit().follow()

    # now it should be there
    links = client.get('/').pyquery('.globals a.citizen-login')
    assert links.text() == 'Kunden-Login'

    login_page = client.get(links.attr('href'))
    login_page.form['email'] = 'citizen@example.org'
    confirm_page = login_page.form.submit().follow()
    assert "Kunden-Login bestätigen" in confirm_page.text
    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0)['TextBody']
    assert 'confirm-citizen-login' in message
    url = re.search(r'localhost(/auth/[^)]+)', message).group(1)  # type: ignore[union-attr]

    # finish login with the confirm url
    confirm_page = client.get(url)
    index_page = confirm_page.form.submit().follow()

    links = index_page.pyquery('.globals a.logout')
    assert links.text() == 'Abmelden'

    index_page = client.get(links.attr('href')).follow()
    links = index_page.pyquery('.globals a.citizen-login')
    assert links.text() == 'Kunden-Login'
