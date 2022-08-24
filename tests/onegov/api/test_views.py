from freezegun import freeze_time


def test_view_api(client):
    # Collection
    response = client.get('/api')
    headers = response.headers
    assert headers['Content-Type'] == 'application/vnd.collection+json'
    assert 'X-RateLimit-Limit' not in headers
    assert response.json == {
        'collection': {
            'version': '1.0',
            'href': 'http://localhost/api',
            'queries': [{
                'rel': 'endpoint',
                'href': 'http://localhost/api/endpoint',
                'data': []
            }]
        }
    }

    # Endpoint
    with freeze_time('2020-02-02 20:20'):
        response = client.get('/api/endpoint')
    headers = response.headers
    assert headers['Content-Type'] == 'application/vnd.collection+json'
    assert headers['X-RateLimit-Limit'] == '100'
    assert headers['X-RateLimit-Remaining'] == '99'
    assert headers['X-RateLimit-Reset'] == 'Sun, 02 Feb 2020 20:35:00 GMT'
    assert response.json == {
        'collection': {
            'version': '1.0',
            'href': 'http://localhost/api/endpoint?page=0',
            'links': [
                {'href': None, 'rel': 'prev'},
                {'href': None, 'rel': 'next'}
            ],
            'items': [
                {
                    'href': 'http://localhost/api/endpoint/1',
                    'data': [{'title': 'First item'}],
                },
                {
                    'href': 'http://localhost/api/endpoint/2',
                    'data': [{'title': 'Second item'}],
                }
            ]
        }
    }

    # Item
    with freeze_time('2020-02-02 20:20'):
        response = client.get('/api/endpoint/1')
    headers = response.headers
    assert headers['Content-Type'] == 'application/vnd.collection+json'
    assert headers['X-RateLimit-Limit'] == '100'
    assert headers['X-RateLimit-Remaining'] == '98'
    assert headers['X-RateLimit-Reset'] == 'Sun, 02 Feb 2020 20:35:00 GMT'
    assert response.json == {
        'collection': {
            'version': '1.0',
            'href': 'http://localhost/api/endpoint',
            'items': [
                {
                    'href': 'http://localhost/api/endpoint/1',
                    'data': [{'name': 'a', 'value': 1}],
                    'links': [{'href': '2', 'rel': 'b'}]
                },
            ]
        }
    }

    # Rate Limit
    client.app.rate_limit = (2, 900)
    with freeze_time('2020-02-02 20:20'):
        response = client.get('/api/endpoint/1', status=429)
    headers = response.headers
    assert headers['Content-Type'] == 'application/vnd.collection+json'
    assert headers['Retry-After'] == 'Sun, 02 Feb 2020 20:35:00 GMT'
    assert headers['X-RateLimit-Limit'] == '2'
    assert headers['X-RateLimit-Remaining'] == '0'
    assert headers['X-RateLimit-Reset'] == 'Sun, 02 Feb 2020 20:35:00 GMT'

    with freeze_time('2020-02-02 20:36'):
        response = client.get('/api/endpoint/1')
    headers = response.headers
    assert headers['Content-Type'] == 'application/vnd.collection+json'
    assert headers['X-RateLimit-Limit'] == '2'
    assert headers['X-RateLimit-Remaining'] == '1'
    assert headers['X-RateLimit-Reset'] == 'Sun, 02 Feb 2020 20:51:00 GMT'

    client.app.rate_limit = (100, 900)

# todo: text exceptions
