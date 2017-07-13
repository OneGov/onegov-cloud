from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_groups(gazette_app):
    client = Client(gazette_app)
    login_admin(client)

    # no groups yet
    manage = client.get('/groups')
    assert "Keine Gruppen." in manage

    # add a group
    manage = manage.click("Neu")
    manage.form['name'] = "Gruppe XY"
    manage = manage.form.submit().follow()
    assert "Gruppe hinzugefügt." in manage
    assert "Gruppe XY" in manage
    assert "Bearbeiten" in manage
    assert "Löschen" in manage
    assert "0" in [t.text for t in manage.pyquery('table.groups tbody tr td')]

    # edit group
    manage = manage.click("Bearbeiten")
    manage.form['name'] = "Gruppe YZ"
    manage = manage.form.submit().follow()
    assert "Gruppe geändert." in manage
    assert "Gruppe XY" not in manage
    assert "Gruppe YZ" in manage

    # add users
    manage = client.get('/users').click("Neu")
    assert 'Gruppe YZ' in manage
    manage.form['role'] = 'editor'
    manage.form['group'] = manage.form['group'].options[1][0]
    manage.form['name'] = 'User A'
    manage.form['email'] = 'user_a@example.com'
    manage = manage.form.submit().follow()
    assert "Benutzer hinzugefügt." in manage

    # delete group
    manage = client.get('/groups')
    assert "1" in [t.text for t in manage.pyquery('table.groups tbody tr td')]
    assert "Bearbeiten" in manage
    assert "Löschen" not in manage
    link = manage.pyquery('.action-edit')[0].attrib['href']
    link = link.replace('/edit', '/delete')
    manage = client.get(link)
    assert "Es können nur Gruppen ohne Benutzer gelöscht werden." in manage

    # delete user and group
    manage = client.get('/user/user_a%40example.com/edit')
    manage.form['group'] = ''
    manage = manage.form.submit().follow()

    manage = client.get('/groups')
    assert "Löschen" in manage
    manage = manage.click("Löschen").form.submit().follow()
    assert "Gruppe gelöscht." in manage
    assert "Keine Gruppen." in manage


def test_view_groups_permissions(gazette_app):
    client = Client(gazette_app)

    login_admin(client)
    manage = client.get('/groups').click("Neu")
    manage.form['name'] = 'XY'
    manage = manage.form.submit().follow()
    edit_link = manage.click('Bearbeiten').request.url
    delete_link = manage.click('Löschen').request.url

    login_publisher(client)
    client.get('/groups', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor(client)
    client.get('/groups', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)
