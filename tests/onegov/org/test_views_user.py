import re

import transaction

from onegov.user import UserCollection


def test_disable_users(client):
    client.login_admin()

    users = client.get('/usermanagement')
    assert 'admin@example.org' in users
    assert 'editor@example.org' in users

    editor = users.click('Ansicht', index=1).click('Bearbeiten')
    editor.form['state'] = 'inactive'
    editor.form.submit()

    login = client.spawn().login_editor()
    assert login.status_code == 200

    editor = users.click('Ansicht', index=1).click('Bearbeiten')
    editor.form['role'] = 'member'
    editor.form['state'] = 'active'
    editor.form.submit()

    login = client.spawn().login_editor()
    assert login.status_code == 302


def test_change_role(client):
    client.login_admin()

    user = client.spawn()
    user.login_editor()
    assert user.get('/userprofile').status_code == 200

    client.app.enable_yubikey = True

    editor = client.get('/usermanagement').click('Ansicht', index=1)
    editor = editor.click('Bearbeiten')
    assert "müssen zwingend einen YubiKey" in editor.form.submit()

    editor.form['role'] = 'member'
    assert editor.form.submit().status_code == 302
    assert user.get('/userprofile', expect_errors=True).status_code == 403
    user.login_editor()

    editor.form['role'] = 'admin'
    editor.form['state'] = 'inactive'
    assert editor.form.submit().status_code == 302
    assert user.get('/userprofile', expect_errors=True).status_code == 403
    user.login_editor()

    editor.form['role'] = 'admin'
    editor.form['state'] = 'active'
    editor.form['yubikey'] = 'cccccccdefgh'
    assert editor.form.submit().status_code == 302
    assert user.get('/userprofile', expect_errors=True).status_code == 403
    user.login_editor()

    client.app.enable_yubikey = False
    editor.form['role'] = 'admin'
    editor.form['state'] = 'active'
    editor.form['yubikey'] = ''
    assert editor.form.submit().status_code == 302
    assert user.get('/userprofile', expect_errors=True).status_code == 403


def test_user_source(client):
    client.login_admin()

    page = client.get('/usermanagement')
    assert 'Quellen' not in page
    assert 'Bearbeiten' in page.click('Ansicht', index=1)

    users = UserCollection(client.app.session())
    user = users.by_username('editor@example.org')
    user.source = 'msal'
    user.source_id = '1234'
    transaction.commit()

    page = client.get('/usermanagement')
    assert 'Herkunft' in page
    page = page.click('Ansicht', index=1)
    assert 'Bearbeiten' not in page
    assert 'Azure' in page
    assert '1234' in page


def test_unique_yubikey(client):
    client.login_admin()

    client.app.enable_yubikey = True

    users = client.get('/usermanagement')
    admin = users.click('Ansicht', index=0).click('Bearbeiten')
    editor = users.click('Ansicht', index=1).click('Bearbeiten')

    admin.form['yubikey'] = 'cccccccdefgh'
    assert admin.form.submit().status_code == 302

    editor.form['yubikey'] = 'cccccccdefgh'
    assert "bereits von admin@example.org verwendet" in editor.form.submit()

    # make sure the current owner can save its own yubikey
    admin = users.click('Ansicht', index=0).click('Bearbeiten')
    assert admin.form.submit().status_code == 302


def test_add_new_user_without_activation_email(client):
    client.login_admin()

    client.app.enable_yubikey = True

    new = client.get('/usermanagement').click('Benutzer', href='new')
    new.form['username'] = 'admin@example.org'

    assert "existiert bereits" in new.form.submit()

    new.form['username'] = 'secondadmin@example.org'
    new.form['role'] = 'admin'

    assert "müssen zwingend einen YubiKey" in new.form.submit()

    new.form['role'] = 'member'
    new.form['send_activation_email'] = False
    added = new.form.submit()

    assert "Passwort" in added
    password = added.pyquery('.panel strong').text()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'secondadmin@example.org'
    login.form['password'] = password
    assert login.form.submit().status_code == 302


def test_add_new_user_with_activation_email(client):
    client.login_admin()

    client.app.enable_yubikey = False

    new = client.get('/usermanagement').click('Benutzer', href='new')
    new.form['username'] = 'newmember@example.org'
    new.form['role'] = 'member'
    new.form['send_activation_email'] = True
    added = new.form.submit()

    assert "Passwort" not in added
    assert "Anmeldungs-Anleitung wurde an den Benutzer gesendet" in added

    email = client.get_email(0)['TextBody']
    reset = re.search(
        r'(http://localhost/auth/reset-password[^)]+)', email).group()

    page = client.spawn().get(reset)
    page.form['email'] = 'newmember@example.org'
    page.form['password'] = 'p@ssw0rd'
    page.form.submit()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'newmember@example.org'
    login.form['password'] = 'p@ssw0rd'
    assert login.form.submit().status_code == 302


def test_edit_user_settings(client):
    client.login_admin()

    client.app.enable_yubikey = False

    new = client.get('/usermanagement').click('Benutzer', href='new')
    new.form['username'] = 'new@example.org'
    new.form['role'] = 'member'
    new.form.submit()

    users = UserCollection(client.app.session())
    assert not users.by_username('new@example.org').data

    edit = client.get('/usermanagement').click('Ansicht', index=3)
    edit = edit.click('Bearbeiten')
    assert "new@example.org" in edit

    edit.form.get('daily_ticket_statistics').checked = False
    edit.form.submit()

    assert not users.by_username('new@example.org')\
        .data['daily_ticket_statistics']
