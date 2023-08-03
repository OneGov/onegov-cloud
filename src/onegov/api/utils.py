from webob.exc import HTTPUnauthorized, HTTPClientError
from onegov.api.models import ApiException, ApiKey
from onegov.api.token import try_get_encoded_token, jwt_decode
import jwt
from datetime import datetime
from datetime import timedelta


def authenticate(request):
    try:
        auth = try_get_encoded_token(request)
        data = jwt_decode(request, auth)
    except jwt.ExpiredSignatureError as exception:
        raise HTTPUnauthorized() from exception
    except Exception as e:
        raise ApiException() from e

    if request.session.query(ApiKey).get(data['id']) is None:
        raise HTTPClientError()


def check_rate_limit(request):
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

    limit, expiration = request.app.rate_limit
    requests, timestamp = request.app.rate_limit_cache.get_or_create(
        request.client_addr,
        creator=lambda: (0, datetime.utcnow()),
    )
    if (datetime.utcnow() - timestamp).seconds < expiration:
        requests += 1
    else:
        timestamp = datetime.utcnow()
        requests = 1
    request.app.rate_limit_cache.set(
        request.client_addr, (requests, timestamp)
    )
    reset = timestamp + timedelta(seconds=expiration)
    headers = {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(max(limit - requests, 0)),
        'X-RateLimit-Reset': reset.strftime("%a, %d %b %Y %H:%M:%S GMT")
    }

    @request.after
    def add_headers(response):
        for header in headers.items():
            response.headers.add(*header)

    if requests > limit:
        headers['Retry-After'] = headers['X-RateLimit-Reset']
        raise ApiException(
            'Rate limit exceeded', status_code=429, headers=headers
        )

    return headers
