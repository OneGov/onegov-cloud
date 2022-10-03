from freezegun import freeze_time
from collection_json import Collection
from unittest.mock import patch


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
    assert len(Collection.from_json(response.body).queries) == 1

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
            'href': 'http://localhost/api/endpoint',
            'links': [
                {'href': None, 'rel': 'prev'},
                {'href': None, 'rel': 'next'}
            ],
            'items': [
                {
                    'href': 'http://localhost/api/endpoint/1',
                    'data': [
                        {'name': 'title', 'value': 'First item'},
                        {'name': 'a', 'value': 1}
                    ],
                    'links': [
                        {'href': '2', 'rel': 'b'}
                    ]
                },
                {
                    'href': 'http://localhost/api/endpoint/2',
                    'data': [
                        {'name': 'title', 'value': 'Second item'},
                        {'name': 'a', 'value': 5}],
                    'links': [
                        {'href': '6', 'rel': 'b'}
                    ]
                }
            ]
        }
    }
    assert len(Collection.from_json(response.body).links) == 2
    assert len(Collection.from_json(response.body).items) == 2

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
                    'data': [
                        {'name': 'title', 'value': 'First item'},
                        {'name': 'a', 'value': 1}
                    ],
                    'links': [
                        {'href': '2', 'rel': 'b'}
                    ]
                },
            ]
        }
    }
    assert len(Collection.from_json(response.body).items) == 1

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

    # Exceptions
    for url in ('/api/entpoind', '/api/entpoind/one', '/api/endpoint/one'):
        response = client.get(url, status=404)
        headers = response.headers
        assert headers['Content-Type'] == 'application/vnd.collection+json'
        assert response.json == {
            'collection': {
                'version': '1.0',
                'href': f'http://localhost{url}',
                'error': {'message': 'Not found'}
            }
        }
        assert Collection.from_json(response.body).version == '1.0'

    with patch('onegov.api.models.ApiEndpointCollection'):
        for url in ('/api', '/api/endpoint', '/api/endpoint/1'):
            response = client.get('/api/endpoint/1', status=500)
            headers = response.headers
            assert headers['Content-Type'] == 'application/vnd.collection+json'
            assert response.json == {
                'collection': {
                    'version': '1.0',
                    'href': 'http://localhost/api/endpoint/1',
                    'error': {'message': 'Internal Server Error'}
                }
            }
            assert Collection.from_json(response.body).version == '1.0'
