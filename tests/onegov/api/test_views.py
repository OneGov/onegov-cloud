import transaction

from freezegun import freeze_time
from collection_json import Collection
from onegov.api.models import ApiKey
from onegov.user import UserCollection
from unittest.mock import patch
from uuid import uuid4


def test_view_api(client):

    user = UserCollection(client.app.session()).add(
        username='a@a.a', password='a', role='admin'
    )
    # create an access key with write access
    uuid = uuid4()
    key = ApiKey(
        name='key', read_only=False, last_used=None, key=uuid, user=user
    )
    client.app.session().add(key)
    transaction.commit()

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
            ],
            'template': {
                'data': [
                    {'name': 'title', 'prompt': 'Title'},
                ],
            }
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
            ],
            'template': {
                'data': [
                    {'name': 'title', 'prompt': 'Title'},
                ],
            }
        }
    }
    assert len(Collection.from_json(response.body).items) == 1

    # Edit Item
    with freeze_time('2020-02-02 20:20'):
        # Without a token that has write permissions we can't change anything
        response = client.put(
            '/api/endpoint/1',
            params='title=Changed',
            status=401
        )
        headers = response.headers
        assert headers['Content-Type'] == 'application/vnd.collection+json'
        assert response.json == {
            'collection': {
                'version': '1.0',
                'href': 'http://localhost/api/endpoint/1',
                'error': {'message': 'Unauthorized'}
            }
        }
        assert Collection.from_json(response.body).version == '1.0'

    # Hidden Item
    with freeze_time('2020-02-02 20:20'):
        response = client.get('/api/endpoint/3', status=404)
        headers = response.headers
        assert headers['Content-Type'] == 'application/vnd.collection+json'
        assert response.json == {
            'collection': {
                'version': '1.0',
                'href': 'http://localhost/api/endpoint/3',
                'error': {'message': 'Not Found'}
            }
        }
        assert Collection.from_json(response.body).version == '1.0'

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


    # Authorize
    headers = {"Authorization": f"Bearer {uuid}"}
    response = client.get('/api/authenticate', headers=headers)
    assert response.status_code == 200
    resp = response.body.decode('utf-8')
    assert resp.startswith('{"token":')

    token = resp.split('"')[3]
    headers = {"Authorization": f"Bearer {token}"}

    # Edit Item
    response = client.put(
        '/api/endpoint/1',
        params='title=Changed',
        headers=headers
    )
    assert response.status_code == 200

    # Edit Hidden Item
    response = client.put(
        '/api/endpoint/3',
        params='title=Changed',
        headers=headers,
        status=404
    )
    headers = response.headers
    assert headers['Content-Type'] == 'application/vnd.collection+json'
    assert response.json == {
        'collection': {
            'version': '1.0',
            'href': 'http://localhost/api/endpoint/3',
            'error': {'message': 'Not Found'}
        }
    }
    assert Collection.from_json(response.body).version == '1.0'
