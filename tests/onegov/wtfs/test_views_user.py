from onegov.core.request import CoreRequest
from unittest.mock import patch


def test_views_user(client):
    client.login_admin()

    # Add a municipality
    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "Adlikon"
    add.form['bfs_number'] = '1'
    add.form['payment_type'] = 'normal'
    assert "Adlikon" in add.form.submit().follow()

    # Add a user
    add = client.get('/users').click(href='/add')
    add.form['realname'] = "Hans Muster"
    add.form['username'] = "hans.muster@winterthur.ch"
    add.form['role'].select('editor')
    add.form['municipality_id'].select(text="Adlikon (1)")
    add.form['contact'] = True
    added = add.form.submit().follow()
    assert "Benutzer hinzugefügt." in added
    assert "Hans Muster" in added
    assert "Hans Muster" in client.get('/municipalities').click("Adlikon")

    # Add a user without a group
    add = client.get('/users').click(href='/add')
    add.form['realname'] = "Optimo X"
    add.form['username'] = "info@optimo.info"
    add.form['role'].select('member')
    added = add.form.submit().follow()
    assert "Benutzer hinzugefügt." in added
    assert "Optimo X" in added

    # View users
    view = client.get('/users').click("Hans Muster")
    assert "Gemeindeadministrator" in view
    assert "hans.muster@winterthur.ch" in view
    assert "✔︎" in view
    assert "Adlikon" in view

    view = client.get('/users').click("Optimo X")
    assert "Benutzer" in view
    assert "info@optimo.info" in view
    assert "✘︎" in view

    # Edit user
    edit = client.get('/users').click("Hans Muster").click("Bearbeiten")
    edit.form['realname'] = "Hans-Peter Muster"
    edit.form['username'] = "hans-peter.muster@winterthur.ch"
    edit.form['role'].select('member')
    assert "Benutzer geändert." in edit.form.submit().follow()
    view = client.get('/users').click("Hans-Peter Muster")
    assert "Hans-Peter Muster" in view
    assert "Benutzer" in view
    assert "hans-peter.muster@winterthur.ch" in view
    assert "✔︎" in view
    assert "Adlikon" in view

    # Delete user
    deleted = client.get('/users').click("Hans-Peter Muster").click("Löschen")
    assert deleted.status_int == 200
    deleted = client.get('/users').click("Optimo X").click("Löschen")
    assert deleted.status_int == 200
    assert "Hans-Peter Muster" not in client.get('/users')
    assert "Optimo X" not in client.get('/users')

    # Edit ourself
    edit = client.get('/users').click("Admin").click("Bearbeiten")
    edit.form['realname'] = "Administrator"
    edit.form['username'] = "administrator@winterthur.ch"
    edited = edit.form.submit().follow()
    assert "Benutzer geändert." in edited
    assert "Passwort vergessen?" in edited
    edited.form['username'] = "administrator@winterthur.ch"
    edited.form['password'] = "hunter2"
    assert "Administrator" in edited.form.submit().follow()


def test_views_user_editor(client):
    client.login_editor()

    # Add a user
    add = client.get('/users').click(href='/add')
    add.form['realname'] = "Hans Muster"
    add.form['username'] = "hans.muster@winterthur.ch"
    add.form['contact'] = True
    added = add.form.submit().follow()
    assert "Benutzer hinzugefügt." in added
    assert "Hans Muster" in added

    # View the user
    view = client.get('/users').click("Hans Muster")
    assert "Benutzer" in view
    assert "hans.muster@winterthur.ch" in view
    assert "✔︎" in view
    assert "My Municipality" in view

    # Edit the user
    edit = client.get('/users').click("Hans Muster").click("Bearbeiten")
    edit.form['realname'] = "Hans-Peter Muster"
    edit.form['username'] = "hans-peter.muster@winterthur.ch"
    edit.form['contact'] = False
    assert "Benutzer geändert." in edit.form.submit().follow()
    view = client.get('/users').click("Hans-Peter Muster")
    assert "Hans-Peter Muster" in view
    assert "Benutzer" in view
    assert "hans-peter.muster@winterthur.ch" in view
    assert "✘︎" in view
    assert "My Municipality" in view

    # Delete the user
    deleted = client.get('/users').click("Hans-Peter Muster").click("Löschen")
    assert deleted.status_int == 200
    assert "Hans-Peter Muster" not in client.get('/users')

    # Edit ourself
    edit = client.get('/users').click("Editor").click("Bearbeiten")
    edit.form['realname'] = "Gemeinde-Administrator"
    edit.form['username'] = "administrator@gemeinde.ch"
    edited = edit.form.submit().follow()
    assert "Benutzer geändert." in edited
    assert "Passwort vergessen?" in edited
    edited.form['username'] = "administrator@gemeinde.ch"
    edited.form['password'] = "hunter2"
    assert "Gemeinde-Administrator" in edited.form.submit().follow()


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_users_permissions(mock_method, client):
    client.login_admin()

    add = client.get('/users').click(href='/add')
    add.form['realname'] = "Optimo X"
    add.form['username'] = "info@optimo.info"
    add.form['role'].select('member')
    assert "Benutzer hinzugefügt." in add.form.submit().follow()

    client.logout()

    urls = [
        '/users',
        '/users/add',
        '/users/add-unrestricted'
    ]
    users = [
        'member%40example.org',
        'editor%40example.org',
        'info%40optimo.info',
        'admin%40example.org',
    ]

    for url in urls:
        client.get(url, status=403)
    for user in users:
        client.get(f'/user/{user}', status=403)
        client.get(f'/user/{user}/edit', status=403)
        client.get(f'/user/{user}/edit-unrestricted', status=403)
        client.delete(f'/user/{user}', status=403)

    client.login_member()
    for url in urls:
        client.get(url, status=403)
    for user in users:
        client.get(f'/user/{user}', status=403)
        client.get(f'/user/{user}/edit', status=403)
        client.get(f'/user/{user}/edit-unrestricted', status=403)
        client.delete(f'/user/{user}', status=403)
    client.logout()

    client.login_editor()
    client.get('/users')
    client.get('/users/add')
    client.get('/users/add-unrestricted', status=403)
    for user in users[:1]:
        client.get(f'/user/{user}')
        client.get(f'/user/{user}/edit')
        client.get(f'/user/{user}/edit-unrestricted', status=403)
        client.delete(f'/user/{user}')
    for user in users[1:2]:
        client.get(f'/user/{user}')
        client.get(f'/user/{user}/edit')
        client.get(f'/user/{user}/edit-unrestricted', status=403)
        client.delete(f'/user/{user}', status=403)
    for user in users[2:]:
        client.get(f'/user/{user}', status=403)
        client.get(f'/user/{user}/edit', status=403)
        client.get(f'/user/{user}/edit-unrestricted', status=403)
        client.delete(f'/user/{user}', status=403)
    client.logout()

    client.login_admin()
    for user in users[1:]:
        client.get(f'/user/{user}')
        client.get(f'/user/{user}/edit')
        client.get(f'/user/{user}/edit-unrestricted')
    for user in users[1:-1]:
        client.delete(f'/user/{user}')
    for user in users[-1:]:
        client.delete(f'/user/{user}', status=403)
    client.logout()
