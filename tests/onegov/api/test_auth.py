from base64 import b64encode
from uuid import uuid4

import transaction

from onegov.api.models import ApiKey
from onegov.api.token import jwt_decode, get_token
from onegov.core.utils import Bunch
from onegov.user import UserCollection


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
    request = Bunch(
        **{
            'app.identity_secret': 'secret',
            'session': session,
            'authorization': ('Basic', b64encode(auth.encode('utf-8'))),
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
