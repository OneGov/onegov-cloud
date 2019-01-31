
def test_views_user_groups(client):
    client.login_admin()

    add = client.get('/user-groups').click(href='add')
    add.form['name'] = "Gruppe Adlikon"
    added = add.form.submit().follow()
    assert "Benutzergruppe hinzugefügt." in added
    assert "Gruppe Adlikon" in added

    view = client.get('/user-groups').click("Gruppe Adlikon")
    assert "Gruppe Adlikon" in view
    # link to municipalities is tested in test_views_municipality_group

    edit = view.click("Bearbeiten")
    edit.form['name'] = "Gruppe Aesch"
    edited = edit.form.submit().follow()
    assert "Benutzergruppe geändert." in edited
    assert "Gruppe Aesch" in edited

    deleted = client.get('/user-groups').click("Gruppe Aesch").click("Löschen")
    assert deleted.status_int == 200

    assert "Gruppe Aesch" not in client.get('/user-groups')


def test_views_user_groups_permissions(client):
    client.login_admin()

    add = client.get('/user-groups').click(href='add')
    add.form['name'] = "Gruppe Adlikon"
    assert "Benutzergruppe hinzugefügt." in add.form.submit().follow()

    client.logout()

    urls = [
        '/user-groups',
        '/user-groups/add',
        '/user-groups/municipality/1',
        '/user-groups/municipality/1/edit',
        '/user-groups/municipality/1/delete'
    ]

    for url in urls:
        client.get('/user-groups', status=403)

    client.login_member()
    for url in urls:
        client.get('/user-groups', status=403)
    client.logout()

    client.login_editor()
    for url in urls:
        client.get('/user-groups', status=403)
    client.logout()

    client.login_admin()
    for url in urls:
        client.get('/user-groups')
    client.logout()
