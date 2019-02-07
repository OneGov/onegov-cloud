from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload


def test_views_municipality(client):
    client.login_admin()

    add = client.get('/municipalities').click(href='add')
    add.form['name'] = "Gemeinde Adlikon"
    add.form['bfs_number'] = '21'
    added = add.form.submit().follow()
    assert "Gemeinde hinzugefügt." in added
    assert "Gemeinde Adlikon" in added

    view = client.get('/municipalities').click("Gemeinde Adlikon")
    assert "Gemeinde Adlikon" in view
    assert "21" in view

    edit = view.click("Bearbeiten")
    edit.form['name'] = "Gemeinde Aesch"
    edit.form['bfs_number'] = '241'
    edited = edit.form.submit().follow()
    assert "Gemeinde geändert." in edited
    assert "Gemeinde Aesch" in edited

    upload = client.get('/municipalities').click("Daten importieren")
    upload.form['file'] = Upload(
        'test.csv',
        (
            "Gemeinde,Gemeinde-Nr,Vordefinierte Termine\n"
            "Gemeinde Aesch,241,12.2.2015"
        ).encode('utf-8'),
        'text/csv'
    )
    uploaded = upload.form.submit().follow()
    assert "Gemeindedaten importiert." in uploaded
    assert "12.02.2015" in client.get('/municipalities')\
        .click("Gemeinde Aesch")

    clear = client.get('/municipalities').click("Gemeinde Aesch")\
        .click("Abholtermine löschen")
    cleared = clear.form.submit().follow()
    assert "Abholtermine gelöscht." in cleared
    assert "12.02.2015" not in client.get('/municipalities')\
        .click("Gemeinde Aesch")

    deleted = client.get('/municipalities').click("Gemeinde Aesch")\
        .click("Löschen")
    assert deleted.status_int == 200
    assert "Gemeinde Aesch" not in client.get('/municipalities')


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_municipality_permissions(mock_method, client):
    client.login_admin()

    add = client.get('/municipalities').click(href='add')
    add.form['name'] = "Gemeinde Adlikon"
    add.form['bfs_number'] = '21'
    assert "Gemeinde hinzugefügt." in add.form.submit().follow()
    id = client.get('/municipalities')\
        .click("Gemeinde Adlikon").request.url.split('/')[-1]

    client.logout()

    urls = [
        '/municipalities',
        '/municipalities/add',
        f'/municipality/{id}',
        f'/municipality/{id}/edit'
    ]

    for url in urls:
        client.get(url, status=403)
    client.delete(f'/municipality/{id}', status=403)

    client.login_member()
    for url in urls:
        client.get(url, status=403)
    client.delete(f'/municipality/{id}', status=403)
    client.logout()

    client.login_editor()
    for url in urls:
        client.get(url, status=403)
    client.delete(f'/municipality/{id}', status=403)
    client.logout()

    client.login_admin()
    for url in urls:
        client.get(url)
    client.delete(f'/municipality/{id}')
    client.logout()


def test_views_municipality_group(client):
    client.login_admin()

    add = client.get('/user-groups').click(href='add')
    add.form['name'] = "Gruppe Adlikon"
    assert "Benutzergruppe hinzugefügt." in add.form.submit().follow()

    add = client.get('/user-groups').click(href='add')
    add.form['name'] = "Gruppe Aesch"
    assert "Benutzergruppe hinzugefügt." in add.form.submit().follow()

    add = client.get('/municipalities').click(href='add')
    add.form['name'] = "Gemeinde Adlikon"
    add.form['bfs_number'] = '21'
    add.form['group_id'].select(text="Gruppe Aesch")
    assert "Gemeinde hinzugefügt." in add.form.submit().follow()
    assert "Gruppe Aesch" in client.get('/municipalities')\
        .click("Gemeinde Adlikon")
    assert "Gemeinde Adlikon" in client.get('/user-groups')\
        .click("Gruppe Aesch")
    assert "ic-delete-from" not in client.get('/user-groups')\
        .click("Gruppe Aesch")
    assert "Gruppe Aesch" not in client.get('/municipalities')\
        .click(href='add')

    edit = client.get('/municipalities').click("Gemeinde Adlikon")\
        .click("Bearbeiten")
    edit.form['group_id'].select(text="Gruppe Adlikon")
    assert "Gemeinde geändert." in edit.form.submit().follow()
    assert "Gruppe Adlikon" in client.get('/municipalities')\
        .click("Gemeinde Adlikon")
    assert "Gemeinde Adlikon" in client.get('/user-groups')\
        .click("Gruppe Adlikon")
    assert "Gruppe Adlikon" not in client.get('/municipalities')\
        .click(href='add')
