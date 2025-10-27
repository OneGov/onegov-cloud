from __future__ import annotations

import re
import transaction

from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_disable_users(client: Client) -> None:
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


def test_change_role(client: Client) -> None:
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


def test_user_source(client: Client) -> None:
    client.login_admin()

    page = client.get('/usermanagement')
    assert 'Quellen' not in page
    assert 'Bearbeiten' in page.click('Ansicht', index=1)

    users = UserCollection(client.app.session())
    user = users.by_username('editor@example.org')
    assert user is not None
    user.source = 'msal'
    user.source_id = '1234'
    transaction.commit()

    page = client.get('/usermanagement')
    assert 'Herkunft' in page
    page = page.click('Ansicht', index=1)
    assert 'Bearbeiten' not in page
    assert 'Azure' in page
    assert '1234' in page


def test_unique_yubikey(client: Client) -> None:
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


def test_add_new_user_without_activation_email(client: Client) -> None:
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


def test_add_new_user_with_activation_email(client: Client) -> None:
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
    reset = re.search(  # type: ignore[union-attr]
        r'(http://localhost/auth/reset-password[^)]+)', email).group()

    page = client.spawn().get(reset)
    page.form['email'] = 'newmember@example.org'
    page.form['password'] = 'p@ssw0rd'
    page.form.submit()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'newmember@example.org'
    login.form['password'] = 'p@ssw0rd'
    assert login.form.submit().status_code == 302


def test_edit_user_settings(client: Client) -> None:
    client.login_admin()

    client.app.enable_yubikey = False

    new = client.get('/usermanagement').click('Benutzer', href='new')
    new.form['username'] = 'new@example.org'
    new.form['role'] = 'member'
    new.form.submit()

    users = UserCollection(client.app.session())
    assert users.by_username('new@example.org').data  # type: ignore[union-attr]

    edit = client.get('/usermanagement').click('Ansicht', index=-1)
    edit = edit.click('Bearbeiten')
    assert "new@example.org" in edit

    edit.form['ticket_statistics'] = 'never'
    edit.form.submit()

    assert (users.by_username('new@example.org')  # type: ignore[union-attr]
        .data['ticket_statistics'] == 'never')


def test_filters(client: Client) -> None:
    client.login_admin()

    client.app.enable_yubikey = False

    def add_user(username: str, role: str, state: str) -> None:
        new = client.get('/usermanagement').click('Benutzer', href='new')
        new.form['username'] = username
        new.form['role'] = role
        new.form['state'] = state
        new.form.submit()

    add_user('arno@example.org', 'member', 'active')
    add_user('beno@example.org', 'member', 'inactive')
    add_user('charles@example.org', 'editor', 'active')
    add_user('doris@example.org', 'editor', 'inactive')
    add_user('emilia@example.org', 'admin', 'active')
    add_user('frank@example.org', 'admin', 'inactive')

    # test active filter by default
    users = client.get('/usermanagement')
    assert not users.pyquery('.filter-active .active a')

    users = client.get('/usermanagement?active=1')
    assert users.pyquery('.filter-active .active a').text() == 'Aktiv'
    users = client.get('/usermanagement?active=0')
    assert users.pyquery('.filter-active .active a').text() == 'Inaktiv'
    # assert not users.pyquery('.filter-active .active a')

    # test active filter clicking breadcrumb (collection and user layout)
    users = users.click('Benutzerverwaltung')
    assert users.pyquery('.filter-active .active a').text() == 'Aktiv'
    user = users.click('Ansicht', index=0).click('Benutzerverwaltung')
    assert user.pyquery('.filter-active .active a').text() == 'Aktiv'

    # test active filter after submitting a user change
    user = users.click('Ansicht', index=0).click('Bearbeiten')
    users = user.form.submit().follow()
    assert users.pyquery('.filter-active .active a').text() == 'Aktiv'

    # test active filter via Menu user
    users = client.get('/').click('Benutzer', index=1)
    assert users.pyquery('.filter-active .active a').text() == 'Aktiv'
    assert 'arno' in users
    assert 'beno' not in users
    assert 'charles' in users
    assert 'doris' not in users
    assert 'emilia' in users
    assert 'frank' not in users

    # also switch 'inactive' filter to on
    users = users.click('Inaktiv')
    assert users.pyquery('.filter-active .active a').text() == 'Aktiv Inaktiv'
    assert 'arno' in users
    assert 'beno' in users
    assert 'charles' in users
    assert 'doris' in users
    assert 'emilia' in users
    assert 'frank' in users

    # show all 'active' 'admin' users
    users = users.click('Inaktiv')
    users = users.click('Administrator')
    assert 'arno' not in users
    assert 'beno' not in users
    assert 'charles' not in users
    assert 'doris' not in users
    assert 'emilia' in users
    assert 'frank' not in users

    # show 'active' and 'inactive' 'member' users
    users = client.get('/usermanagement')
    users = users.click('Aktiv', index=1)
    users = users.click('Inaktiv')
    users = users.click('Editor')
    assert 'arno' not in users
    assert 'beno' not in users
    assert 'charles' in users
    assert 'doris' in users
    assert 'emilia' not in users
    assert 'frank' not in users
