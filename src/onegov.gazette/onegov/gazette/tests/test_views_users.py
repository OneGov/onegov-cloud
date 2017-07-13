from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_users(gazette_app):
    client = Client(gazette_app)
    login_admin(client)

    manage = client.get('/users')
    assert 'publisher@example.org' in manage
    assert 'editor@example.org' in manage

    # add a publisher
    manage = manage.click("Neu")
    manage.form['role'] = 'editor'
    manage.form['name'] = "New user"
    manage.form['email'] = "new_user@example.org"
    manage = manage.form.submit().follow()
    assert "Benutzer hinzugefügt." in manage
    assert "new_user@example.org" in manage

    # make it an editor
    manage = manage.click("Bearbeiten", href="new_user")
    manage.form['role'] = 'member'
    manage = manage.form.submit().follow()
    assert "Benutzer geändert." in manage

    # delete user
    manage = manage.click("Löschen", href="new_user").form.submit().follow()
    assert "Benutzer gelöscht." in manage
    assert "new_user@example.org" not in manage


def test_view_users_permissions(gazette_app):
    client = Client(gazette_app)

    login_admin(client)
    manage = client.get('/users')
    edit_link = manage.click("Bearbeiten", href='editor').request.url
    delete_link = manage.click("Löschen", href='edit').request.url

    login_publisher(client)
    client.get('/users', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor(client)
    client.get('/users', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)
