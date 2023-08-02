from base64 import b64decode
from datetime import timedelta
import jwt
from sedate import utcnow
from onegov.api.models import ApiKey
from onegov.core.request import CoreRequest


from typing import Any


def jwt_decode(request: CoreRequest, token: str | bytes) -> Any:
    return jwt.decode(token, request.identity_secret, algorithms=['HS512'])


def jwt_encode(request: CoreRequest, payload: dict[str, str]) -> str:
    iat = utcnow()
    exp = iat + timedelta(hours=1)
    headers = {
        'iat': int(iat.strftime('%s')),
        'exp': int(exp.strftime('%s')),
    }
    return jwt.encode(
        payload, request.identity_secret, algorithm='HS512', headers=headers
    )


def get_token(request: CoreRequest) -> dict[str, str]:
    assert request.authorization[0].lower() == 'basic'  # type: ignore[index]
    auth = b64decode(
        request.authorization[1].strip()  # type: ignore[index, union-attr]
    ).decode('utf-8')

    key, _ = auth.split(':', 1)

    session = request.session
    api_key = session.query(ApiKey).filter_by(key=str(key)).one()

    today = utcnow()
    api_key.last_used = today

    payload = {
        'id': str(api_key.id),
    }
    return {'token': jwt_encode(request, payload)}
