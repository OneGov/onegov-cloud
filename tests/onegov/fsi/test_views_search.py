

def test_basic_search(client_with_es):
    client = client_with_es
    client.login_admin()
    anom = client.spawn()

    'Resultate' in client.get('/search?q=test')
    anom.get('/search?q=test', status=403)  # forbidden
