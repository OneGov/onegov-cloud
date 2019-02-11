from onegov.core.request import CoreRequest
from unittest.mock import patch


def test_views_user_groups(client):
    client.login_admin()

    # Add a group
    add = client.get('/user-groups').click(href='add')
    add.form['name'] = "Gruppe Adlikon"
    added = add.form.submit().follow()
    assert "Benutzergruppe hinzugefügt." in added
    assert "Gruppe Adlikon" in added

    # View the group
    view = client.get('/user-groups').click("Gruppe Adlikon")
    assert "Gruppe Adlikon" in view

    # Edit the group
    edit = view.click("Bearbeiten")
    edit.form['name'] = "Gruppe Aesch"
    edited = edit.form.submit().follow()
    assert "Benutzergruppe geändert." in edited
    assert "Gruppe Aesch" in edited

    # Delete the group
    deleted = client.get('/user-groups').click("Gruppe Aesch").click("Löschen")
    assert deleted.status_int == 200
    assert "Gruppe Aesch" not in client.get('/user-groups')


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_user_groups_permissions(mock_method, client):
    client.login_admin()

    add = client.get('/user-groups').click(href='add')
    add.form['name'] = "Gruppe Adlikon"
    assert "Benutzergruppe hinzugefügt." in add.form.submit().follow()
    id = client.get('/user-groups')\
        .click("Gruppe Adlikon").request.url.split('/')[-1]

    client.logout()

    urls = [
        '/user-groups',
        '/user-groups/add',
        f'/user-group/{id}',
        f'/user-group/{id}/edit',
    ]

    for url in urls:
        client.get(url, status=403)
    client.delete(f'/user-group/{id}', status=403)

    client.login_member()
    for url in urls:
        client.get(url, status=403)
    client.delete(f'/user-group/{id}', status=403)
    client.logout()

    client.login_editor()
    for url in urls:
        client.get(url, status=403)
    client.delete(f'/user-group/{id}', status=403)
    client.logout()

    client.login_admin()
    for url in urls:
        client.get(url)
    client.delete(f'/user-group/{id}')
    client.logout()
