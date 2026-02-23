from __future__ import annotations

import jwt

from datetime import timedelta
from functools import lru_cache
from onegov.api import ApiApp
from onegov.api.models import ApiException, ApiKey
from onegov.api.token import try_get_encoded_token, jwt_decode
from sedate import utcnow
from webob.exc import HTTPUnauthorized, HTTPClientError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from morepath.request import Response


# TODO: Do we allow this to update request.identity, so we can elevate
#       privileges for what a given API token is allowed to see?
def authenticate(request: CoreRequest) -> ApiKey:
    if request.authorization is None:
        raise HTTPUnauthorized()

    with ApiException.capture_exceptions():
        try:
            auth = try_get_encoded_token(request)
            data = jwt_decode(request, auth)
        except jwt.ExpiredSignatureError as exception:
            raise HTTPUnauthorized() from exception

    api_key = request.session.get(ApiKey, data['id'])
    if api_key is None:
        raise HTTPClientError()

    return api_key


# NOTE: This is a workaround for the problem above, when we only care
#       about whether or not we're authorized and not what kind of
#       permissions are attached to our ApiKey, then we can use this
#       function.
@lru_cache(16)
def is_authorized(request: CoreRequest) -> bool:
    try:
        authenticate(request)
    except Exception:
        return False
    else:
        return True


def check_rate_limit(request: CoreRequest) -> dict[str, str]:
    """ Checks if the rate limit for the current client.

    Raises an exception if the rate limit is reached. Returns response headers
    containing informations about the remaining rate limit.

    Logged in users don't have rate limits. The same is true for users that
    have authenticated with a token.

    """

    if request.is_logged_in:
        return {}

    if request.authorization:
        authenticate(request)
        return {}

    assert isinstance(request.app, ApiApp)
    addr = request.client_addr or 'unknown'

    limit, expiration = request.app.rate_limit
    requests, timestamp = request.app.rate_limit_cache.get_or_create(
        addr,
        creator=lambda: (0, utcnow()),
    )
    if (utcnow() - timestamp).seconds < expiration:
        requests += 1
    else:
        timestamp = utcnow()
        requests = 1
    request.app.rate_limit_cache.set(
        addr, (requests, timestamp)
    )
    reset = timestamp + timedelta(seconds=expiration)
    headers = {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(max(limit - requests, 0)),
        'X-RateLimit-Reset': reset.strftime('%a, %d %b %Y %H:%M:%S GMT')
    }

    @request.after
    def add_headers(response: Response) -> None:
        for header in headers.items():
            response.headers.add(*header)

    if requests > limit:
        headers['Retry-After'] = headers['X-RateLimit-Reset']
        raise ApiException(
            'Rate limit exceeded', status_code=429, headers=headers
        )

    return headers
