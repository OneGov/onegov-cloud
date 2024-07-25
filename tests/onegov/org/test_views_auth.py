import json
import os
import re

from freezegun import freeze_time
from lxml.html import document_fromstring
from onegov.org.models import TANAccessCollection


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


def test_login_setup_mtan(client, smsdir):
    client.app.mtan_second_factor_enabled = True
    client.app.mtan_automatic_setup = True
    # descend to app-specific sms directory
    smsdir = os.path.join(smsdir, client.app.schema)
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
    mtan_page.form['tan'] = mtan

    index_page = mtan_page.form.submit().follow()
    assert "Sie wurden angemeldet" in index_page.text


def test_reset_password(client):
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


def test_registration(client):
    client.app.enable_user_registration = True

    register = client.get('/auth/register')
    register.form['username'] = 'user@example.org'
    register.form['password'] = 'p@ssw0rd'
    register.form['confirm'] = 'p@ssw0rd'

    assert "Vielen Dank" in register.form.submit().follow()

    message = client.get_email(0)['HtmlBody']
    assert "Anmeldung bestätigen" in message

    expr = r'href="[^"]+">Anmeldung bestätigen</a>'
    url = re.search(expr, message).group()
    url = client.extract_href(url)

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


def test_disabled_mtan(client):
    client.login_admin()

    client.app.mtan_second_factor_enabled = False
    assert 'mTAN' not in client.get('/usermanagement')

    client.app.mtan_second_factor_enabled = True
    assert 'mTAN' in client.get('/usermanagement')


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


def test_mtan_access(org_app, client, smsdir):
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

    smsdir = os.path.join(smsdir, org_app.schema)
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
        org_app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1
    assert accesses[0].url.endswith(page_url)

    # now that we're authenticated we should be able to
    # access the page normally on subsequent requests
    anonymous.get(page_url, status=200)

    # the second access should not create a new entry
    accesses = TANAccessCollection(
        org_app.session(),
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


def test_mtan_access_from_sms_url(org_app, client, smsdir):
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

    smsdir = os.path.join(smsdir, org_app.schema)
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
        org_app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1
    assert accesses[0].url.endswith(page_url)

    # now that we're authenticated we should be able to
    # access the page normally on subsequent requests
    anonymous.get(page_url, status=200)

    # the second access should not create a new entry
    accesses = TANAccessCollection(
        org_app.session(),
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


def test_secret_mtan_access(org_app, client, smsdir):
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

    smsdir = os.path.join(smsdir, org_app.schema)
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
        org_app.session(),
        session_id='+41791112233'
    ).query().all()
    assert len(accesses) == 1
    assert accesses[0].url.endswith(page_url)

    # now that we're authenticated we should be able to
    # access the page normally on subsequent requests
    anonymous.get(page_url, status=200)

    # the second access should not create a new entry
    accesses = TANAccessCollection(
        org_app.session(),
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


@freeze_time("2020-10-10", tick=True)
def test_mtan_access_unauthorized_resource(org_app, client, smsdir):
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
