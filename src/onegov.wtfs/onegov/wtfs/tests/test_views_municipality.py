
def test_views_municipality(client):
    client.login_admin()

    add = client.get('/municipalities').click(href='add')
    add.form['name'] = 'Adlikon'
    add.form['bfs_number'] = '21'
    added = add.form.submit().follow()
    assert "Gemeinde hinzugefügt." in added
    assert "Adlikon" in added

    view = client.get('/municipalities').click("Adlikon")
    assert "Adlikon" in view
    assert "21" in view

    edit = view.click("Bearbeiten")
    edit.form['name'] = 'Aesch'
    edit.form['bfs_number'] = '241'
    edited = edit.form.submit().follow()
    assert "Gemeinde geändert." in edited
    assert "Aesch" in edited

    deleted = client.get('/municipalities').click("Aesch").click("Löschen")
    assert deleted.status_int == 200

    assert "Aesch" not in client.get('/municipalities')


def test_views_municipality_permissions(client):
    client.login_admin()

    add = client.get('/municipalities').click(href='add')
    add.form['name'] = 'Adlikon'
    add.form['bfs_number'] = '21'
    assert "Gemeinde hinzugefügt." in add.form.submit().follow()

    client.logout()

    urls = [
        '/municipalities',
        '/municipalities/add',
        '/municipalities/municipality/1',
        '/municipalities/municipality/1/edit',
        '/municipalities/municipality/1/delete'
    ]

    for url in urls:
        client.get('/municipalities', status=403)

    client.login_member()
    for url in urls:
        client.get('/municipalities', status=403)
    client.logout()

    client.login_editor()
    for url in urls:
        client.get('/municipalities', status=403)
    client.logout()

    client.login_admin()
    for url in urls:
        client.get('/municipalities')
    client.logout()
