from __future__ import annotations

import jwt

from base64 import b64decode
from datetime import timedelta
from onegov.api.models import ApiKey
from sedate import utcnow
from webob.exc import HTTPBadRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest


def jwt_decode(request: CoreRequest, token: str | bytes) -> Any:
    return jwt.decode(token, request.identity_secret, algorithms=['HS512'])


def jwt_encode(request: CoreRequest, payload: dict[str, Any]) -> str:

    iat = utcnow()  # This has to be UTC,
    # not local
    exp = iat + timedelta(hours=1)
    claims = {'iat': iat, 'exp': exp}
    payload.update(claims)

    return jwt.encode(payload, request.identity_secret, algorithm='HS512')


def get_token(request: CoreRequest) -> dict[str, str]:

    key = try_get_encoded_token(request)

    api_key = request.session.query(ApiKey).filter_by(key=key).one()
    today = utcnow()
    api_key.last_used = today
    payload = {
        'id': str(api_key.id),
    }
    return {'token': jwt_encode(request, payload)}


def try_get_encoded_token(request: CoreRequest) -> str:
    assert request.authorization is not None
    assert isinstance(request.authorization.params, str)
    if request.authorization.authtype == 'Basic':
        auth = b64decode(
            request.authorization.params.strip()
        ).decode('utf-8')
        auth, _ = auth.split(':', 1)
        return auth
    elif request.authorization.authtype == 'Bearer':
        return request.authorization.params
    else:
        raise HTTPBadRequest('Unsupported authorization scheme')
