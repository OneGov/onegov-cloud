from onegov.core.request import CoreRequest
from unittest.mock import patch
from webtest.forms import Upload
from freezegun import freeze_time


def test_views_municipality(client):
    client.login_admin()

    # Add a municipality
    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "Adlikon"
    add.form['bfs_number'] = '21'
    add.form['payment_type'] = 'normal'
    added = add.form.submit().follow()
    assert "hinzugefügt." in added
    assert "Adlikon" in added

    # View the municipality
    view = client.get('/municipalities').click("Adlikon")
    assert "Adlikon" in view
    assert "21" in view
    assert "Normal" in view
    assert "7.00" in view

    # Edit the municipality
    edit = view.click("Bearbeiten")
    edit.form['name'] = "Aesch"
    edit.form['bfs_number'] = '241'
    edit.form['payment_type'] = 'spezial'
    edit.form['address_supplement'] = "Zusatz"
    edit.form['gpn_number'] = "12321"
    edited = edit.form.submit().follow()
    assert "geändert." in edited
    assert "Aesch" in edited
    view = edited.click("Aesch")
    assert "Spezial" in view
    assert "8.50" in view
    assert "12321" in view

    # Upload some dates
    upload = client.get('/municipalities').click("Daten importieren")
    upload.form['file'] = Upload(
        'test.csv',
        "Gemeinde;241;-1;Normal;12.2.2015".encode('cp1252'),
        'text/csv'
    )
    uploaded = upload.form.submit().follow()
    assert "Gemeindedaten importiert." in uploaded
    with freeze_time("2016-01-01"):
        assert "12.02.2015" in client.get('/municipalities').click("Aesch")
    with freeze_time("2018-01-01"):
        assert "12.02.2015" not in client.get('/municipalities').click("Aesch")

    # Delete some dates
    with freeze_time("2015-01-01"):
        clear = client.get('/municipalities').click("Aesch")\
            .click("Abholtermine löschen")
        cleared = clear.form.submit().follow()
    assert "Abholtermine gelöscht." in cleared
    with freeze_time("2016-01-01"):
        assert "12.02.2015" not in client.get('/municipalities').click("Aesch")

    # Delete the municipality
    deleted = client.get('/municipalities').click("Aesch").click("Löschen")
    assert deleted.status_int == 200
    assert "Aesch" not in client.get('/municipalities')


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_municipality_permissions(mock_method, client):
    client.login_admin()

    add = client.get('/municipalities').click(href='/add')
    add.form['name'] = "Adlikon"
    add.form['bfs_number'] = '21'
    add.form['payment_type'] = 'normal'
    assert "hinzugefügt." in add.form.submit().follow()
    id = client.get('/municipalities')\
        .click("Adlikon").request.url.split('/')[-1]

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
