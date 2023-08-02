from base64 import b64decode
from datetime import timedelta, timezone
import datetime
import jwt
from sedate import utcnow
from onegov.api.models import ApiKey
from onegov.core.request import CoreRequest


from typing import Any


def jwt_decode(request: CoreRequest, token: str | bytes) -> Any:
    return jwt.decode(token, request.identity_secret, algorithms=['HS512'])


def jwt_encode(request: CoreRequest, payload: dict[str, Any]) -> str:

    iat = datetime.datetime.now(tz=timezone.utc)  # This has to be UTC,
    # not local
    exp = iat + timedelta(hours=1)
    claims = {"iat": iat, "exp": exp}
    payload.update(claims)

    return jwt.encode(payload, request.identity_secret, algorithm='HS512')


def get_token(request: CoreRequest) -> dict[str, str]:

    key = try_get_encoded_token(request)

    api_key = request.session.query(ApiKey).filter_by(key=str(key)).one()
    today = utcnow()
    api_key.last_used = today
    payload = {
        'id': str(api_key.id),
    }
    return {'token': jwt_encode(request, payload)}


def try_get_encoded_token(request: CoreRequest) -> str:
    assert request.authorization[0].lower() == 'basic'  # type: ignore[index]
    auth = b64decode(
        request.authorization[1].strip()  # type: ignore[index, union-attr]
    ).decode('utf-8')
    auth, _ = auth.split(':', 1)
    return auth
