from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_editor_2
from onegov.gazette.tests import login_editor_3
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_users(gazette_app):
    client = Client(gazette_app)
    login_admin(client)

    manage = client.get('/users')
    assert 'publisher@example.org' in manage
    assert 'editor1@example.org' in manage
    assert 'editor2@example.org' in manage
    assert 'editor3@example.org' in manage

    # try to add a user with a already taken address
    manage = manage.click("Neu")
    manage.form['role'] = 'editor'
    manage.form['name'] = "New editor"
    manage.form['email'] = "editor1@example.org"
    manage = manage.form.submit()
    assert "Ein Benutzer mit dieser E-Mail-Adresse existiert bereits" in manage

    # add a publisher
    manage = client.get('/users')
    manage = manage.click("Neu")
    manage.form['role'] = 'editor'
    manage.form['name'] = "New user"
    manage.form['email'] = "new_user@example.org"
    manage = manage.form.submit().maybe_follow()
    assert "Benutzer hinzugefügt." in manage
    assert "new_user@example.org" in manage

    assert len(gazette_app.smtp.outbox) == 1
    message = gazette_app.smtp.outbox[0]
    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "Benutzerkonto Amtsblattredaktion erstellt" in message

    # make it an editor
    manage = manage.click("Bearbeiten", href="new_user")
    manage.form['role'] = 'member'
    manage = manage.form.submit().maybe_follow()
    assert "Benutzer geändert." in manage

    # try to change the email adress to an already taken one
    manage = manage.click("Bearbeiten", href="new_user")
    manage.form['email'] = 'publisher@example.org'
    manage = manage.form.submit()
    assert "Ein Benutzer mit dieser E-Mail-Adresse existiert bereits" in manage

    # delete user
    manage = client.get('/users').click("Löschen", href="new_user")
    manage = manage.form.submit().maybe_follow()
    assert "Benutzer gelöscht." in manage
    assert "new_user@example.org" not in manage


def test_view_users_permissions(gazette_app):
    client = Client(gazette_app)

    login_admin(client)
    manage = client.get('/users')
    edit_link = manage.click("Bearbeiten", href='editor1').request.url
    delete_link = manage.click("Löschen", href='editor1').request.url

    login_publisher(client)
    client.get('/users', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor_1(client)
    client.get('/users', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor_2(client)
    client.get('/users', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor_3(client)
    client.get('/users', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)
