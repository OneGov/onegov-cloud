from onegov.core.request import CoreRequest
from unittest.mock import patch


def test_views_notifications(client):
    client.login_admin()

    # Add a notification
    add = client.get('/notifications').click(href='/add')
    add.form['title'] = "Systemunterbruch"
    add.form['text'] = "Am 23. Februar 2017, finden Wartungsarbeiten statt."
    added = add.form.submit().follow()
    assert "Benachrichtigung hinzugefügt." in added
    assert "Systemunterbruch" in added

    # Dashboard
    view = client.get('/')
    assert "Systemunterbruch" in view
    assert "Wartungsarbeiten" in view

    # View the notification
    view = client.get('/notifications').click("Systemunterbruch")
    assert "Wartungsarbeiten" in view

    # Edit the notification
    edit = view.click("Bearbeiten")
    edit.form['title'] = "Wartungsarbeiten"
    edit.form['text'] = "24. Februar 2017"
    edited = edit.form.submit().follow()
    assert "Benachrichtigung geändert." in edited
    assert "Wartungsarbeiten" in edited

    # Delete the notification
    deleted = client.get('/notifications')\
        .click("Wartungsarbeiten").click("Löschen")
    assert deleted.status_int == 200
    assert "Wartungsarbeiten" not in client.get('/notifications')
    assert "Wartungsarbeiten" not in client.get('/').follow()


@patch.object(CoreRequest, 'assert_valid_csrf_token')
def test_views_notifications_permissions(mock_method, client):
    client.login_admin()

    add = client.get('/notifications').click(href='/add')
    add.form['title'] = "Systemunterbruch"
    add.form['text'] = "Am 23. Februar 2017, finden Wartungsarbeiten statt."
    assert "Benachrichtigung hinzugefügt." in add.form.submit().follow()
    id = client.get('/notifications')\
        .click("Systemunterbruch").request.url.split('/')[-1]

    client.logout()

    client.get('/notifications', status=403)
    client.get('/notifications/add', status=403)
    client.get(f'/notification/{id}', status=403)
    client.get(f'/notification/{id}/edit', status=403)
    client.delete(f'/notification/{id}', status=403)

    client.login_member()
    client.get('/notifications', status=403)
    client.get('/notifications/add', status=403)
    client.get(f'/notification/{id}')
    client.get(f'/notification/{id}/edit', status=403)
    client.delete(f'/notification/{id}', status=403)
    client.logout()

    client.login_editor()
    client.get('/notifications', status=403)
    client.get('/notifications/add', status=403)
    client.get(f'/notification/{id}')
    client.get(f'/notification/{id}/edit', status=403)
    client.delete(f'/notification/{id}', status=403)
    client.logout()

    client.login_admin()
    client.get('/notifications')
    client.get('/notifications/add')
    client.get(f'/notification/{id}')
    client.get(f'/notification/{id}/edit')
    client.delete(f'/notification/{id}')
    client.logout()
