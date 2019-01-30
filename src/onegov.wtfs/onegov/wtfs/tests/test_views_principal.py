
def test_view_home(client):
    assert 'auth/login' in client.get('/').follow().request.url
