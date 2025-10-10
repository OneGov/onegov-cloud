

def test_basic_search(client_with_fts):
    client = client_with_fts
    client.login_admin()
    anom = client.spawn()

    assert 'Resultate' in client.get('/search?q=test')
    assert client.get('/search/suggest?q=test').json == []
    anom.get('/search?q=test', status=403)  # forbidden
    assert anom.get('/search/suggest?q=test', status=403)  # forbidden

    assert 'Resultate' in client.get('/search-postgres?q=test')
    assert client.get('/search/suggest?q=test').json == []
    anom.get('/search-postgres?q=test', status=403)  # forbidden
    assert anom.get('/search/suggest?q=test', status=403)  # forbidden
