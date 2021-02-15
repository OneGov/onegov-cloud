def test_sitecollection(client):

    assert client.get('/sitecollection', expect_errors=True).status_code == 403

    client.login_admin()

    collection = client.get('/sitecollection').json

    assert collection[0] == {
        'name': 'Kontakt',
        'url': 'http://localhost/topics/kontakt',
        'group': 'Themen'
    }
