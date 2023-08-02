from base64 import b64decode
from datetime import datetime
from datetime import timedelta

import jwt
from sqlalchemy.orm.exc import NoResultFound
from webob.exc import HTTPUnauthorized, HTTPClientError

from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint, ApiException, AuthEndpoint, ApiKey
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.token import get_token, jwt_decode
from onegov.core.security import Public


def authenticate(request):
    try:
        assert request.authorization[0].lower() == 'basic'
        auth = b64decode(request.authorization[1].strip()).decode('utf-8')
        auth, _ = auth.split(':', 1)
        data = jwt_decode(request, auth)
        request.session.get(ApiKey, data['id'])
    except jwt.ExpiredSignatureError as exception:
        raise HTTPUnauthorized() from exception
    except NoResultFound as no_res:
        raise HTTPClientError() from no_res
    except Exception as e:
        raise ApiException() from e


def check_rate_limit(request):
    """ Checks if the rate limit for the current client.

    Raises an exception if the rate limit is reached. Returns response headers
    containing informations about the remaining rate limit.

    Logged in users don't have rate limits.

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


@ApiApp.json(
    model=ApiException,
    permission=Public
)
def handle_exception(self, request):

    @request.after
    def add_headers(response):
        response.status_code = self.status_code
        response.headers['Content-Type'] = 'application/vnd.collection+json'
        for header in self.headers.items():
            response.headers.add(*header)

    return {
        'collection': {
            'version': '1.0',
            'href': request.url,
            'error': {
                'message': self.message
            }
        }
    }


@ApiApp.json(
    model=ApiEndpointCollection,
    permission=Public
)
def view_api_endpoints(self, request):

    @request.after
    def add_headers(response):
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    return {
        'collection': {
            'version': '1.0',
            'href': request.link(self),
            'queries': [
                {
                    'href': request.link(endpoint(request.app)),
                    'rel': endpoint.endpoint,
                    'data': [
                        {'name': name}
                        for name in getattr(endpoint, 'filters', [])
                    ]
                }
                for endpoint in self.endpoints.values()
            ]
        }
    }


@ApiApp.json(
    model=ApiEndpoint,
    permission=Public
)
def view_api_endpoint(self, request):

    headers = check_rate_limit(request)

    @request.after
    def add_headers(response):
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    try:
        return {
            'collection': {
                'version': '1.0',
                'href': request.link(self.for_filter()),
                'links': [
                    {
                        'rel': rel,
                        'href': request.link(item) if item else item
                    }
                    for rel, item in self.links.items()
                ],
                'items': [
                    {
                        'href': request.link(target),
                        'data': [
                            {
                                'name': name,
                                'value': value
                            }
                            for name, value in self.item_data(item).items()
                        ],
                        'links': [
                            {
                                'rel': name,
                                'href': (
                                    link if not link or isinstance(link, str)
                                    else request.link(link)
                                ),
                            }
                            for name, link in self.item_links(item).items()
                        ]
                    }
                    for target, item in self.batch.items()
                ],
            }
        }

    except Exception as exception:
        raise ApiException(exception=exception, headers=headers) from exception


@ApiApp.json(
    model=ApiEndpointItem,
    permission=Public
)
def view_api_endpoint_item(self, request):

    headers = check_rate_limit(request)

    @request.after
    def add_headers(response):
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    try:
        return {
            'collection': {
                'version': '1.0',
                'href': request.link(self.api_endpoint),
                'items': [
                    {
                        'href': request.link(self),
                        'data': [
                            {
                                'name': name,
                                'value': value
                            }
                            for name, value in self.data.items()
                        ],
                        'links': [
                            {
                                'rel': rel,
                                'href': (
                                    link if not link or isinstance(link, str)
                                    else request.link(link)
                                ),
                            }
                            for rel, link in self.links.items()
                        ]
                    }
                ],
            }
        }

    except Exception as exception:
        raise ApiException(exception=exception, headers=headers) from exception


@ApiApp.json(model=AuthEndpoint, permission=Public)
def get_time_restricted_token(self, request):
    try:
        return get_token(request)
    except Exception as exception:
        raise ApiException() from exception
