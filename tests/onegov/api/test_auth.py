from base64 import b64encode
from uuid import uuid4
from collections import namedtuple
import transaction
from onegov.api.models import ApiKey
from onegov.api.token import jwt_decode, get_token
from onegov.core.utils import Bunch
from onegov.user import UserCollection
from freezegun import freeze_time


def test_token_generation(session):

    user = UserCollection(session).add(
        username='a@a.a', password='a', role='admin'
    )
    # create an access key
    uuid = uuid4()
    key = ApiKey(
        name='key', read_only=False, last_used=None, key=uuid, user=user
    )
    session.add(key)
    session.flush()

    auth = str(key.key) + ':'

    authorization = namedtuple('authorization', ['authtype', 'params'])
    authorization.authtype = 'Basic'
    authorization.params = b64encode(auth.encode('utf-8')).decode()
    request = Bunch(
        **{
            'identity_secret': 'secret',
            'session': session,
            'authorization': authorization,
        }
    )
    time_restricted_token = get_token(request)['token']
    assert time_restricted_token
    # roundtrip

    decoded_result = jwt_decode(request, time_restricted_token)
    assert decoded_result['id'] == str(key.id)


def test_get_token(client):

    user = UserCollection(client.app.session()).add(
        username='a@a.a', password='a', role='admin'
    )
    # create an access key
    uuid = uuid4()
    key = ApiKey(
        name='key', read_only=False, last_used=None, key=uuid, user=user
    )
    client.app.session().add(key)
    transaction.commit()

    # basic authentication in the username part (the password part is not used)
    auth_header = b64encode(f"{str(uuid)}:".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}"
    }

    # Make a GET request to get the token
    response = client.get('/api/authenticate', headers=headers)
    assert response


def test_jwt_auth(client):

    user = UserCollection(client.app.session()).add(
        username='a@a.a', password='a', role='admin'
    )
    # create an access key
    uuid = uuid4()
    key = ApiKey(
        name='key', read_only=False, last_used=None, key=uuid, user=user
    )
    client.app.session().add(key)
    transaction.commit()

    auth_header = b64encode(f"{str(uuid)}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}
    response = client.get('/api/authenticate', headers=headers)
    assert response.status_code == 200
    resp = response.body.decode('utf-8')
    assert resp.startswith('{"token":')

    token = resp.split('"')[3]
    auth_header = b64encode(f"{token}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}

    response = client.get('/api/endpoint/1', headers=headers)
    assert response.status_code == 200


def test_jwt_expired(client):
    with freeze_time('2019-01-01T00:00:00'):
        user = UserCollection(client.app.session()).add(
            username='a@a.a', password='a', role='admin'
        )
        # create an access key
        uuid_key = uuid4()
        key = ApiKey(
            name='fo', read_only=False, last_used=None, key=uuid_key, user=user
        )
        client.app.session().add(key)
        transaction.commit()

        auth_header = b64encode(f"{str(uuid_key)}:".encode()).decode()
        headers = {"Authorization": f"Basic {auth_header}"}
        response = client.get('/api/authenticate', headers=headers)

        assert response.status_code == 200
        resp = response.body.decode('utf-8')
        assert resp.startswith('{"token":')

        token = resp.split('"')[3]
        auth_header = b64encode(f"{token}:".encode()).decode()
        headers = {"Authorization": f"Basic {auth_header}"}

    # 30 min later, still works:
    with freeze_time('2019-01-01T00:30:00'):
        response = client.get('/api/endpoint/1', headers=headers)
        assert response.status_code == 200

    # 1 hour later, expired:
    with freeze_time('2019-01-01T01:00:00'):
        response = client.get('/api/endpoint/1', headers=headers, status=401)
        assert response.status_code == 401
