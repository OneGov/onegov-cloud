
def test_view_home(client):
    assert 'auth/login' in client.get('/').follow().request.url

    client.login_admin()

    assert "/scan-jobs" in client.get('/').follow().request.url

    add = client.get('/notifications').click(href='/add')
    add.form['title'] = "Systemunterbruch"
    add.form['text'] = "Am 23. Februar 2017, finden Wartungsarbeiten statt."
    assert "Benachrichtigung hinzugefügt." in add.form.submit().follow()

    assert "Systemunterbruch" in client.get('/')
    assert "Wartungsarbeiten" in client.get('/')

    client.logout()
