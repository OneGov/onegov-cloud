from datetime import datetime
from datetime import timedelta
from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.models import ApiExcpetion
from onegov.core.security import Public


@ApiApp.json(
    model=ApiExcpetion,
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


def check_rate_limit(request):
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
        raise ApiExcpetion(
            'Rate limit exceeded', status_code=429, headers=headers
        )

    return headers


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
                'href': request.link(self),
                'links': [
                    {
                        'rel': name,
                        'href': request.link(item)
                    }
                    for name, item in self.links.items()
                ],
                'items': [
                    {
                        'href': request.link(item),
                        'data': [{'title': title}]
                    }
                    for title, item in self.batch.items()
                ],
            }
        }

    except Exception as exception:
        raise ApiExcpetion(exception=exception, headers=headers)


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
                                'rel': name,
                                'href': (
                                    item if not item or isinstance(item, str)
                                    else request.link(item)
                                ),
                            }
                            for name, item in self.links.items()
                        ]
                    }
                ],
            }
        }

    except Exception as exception:
        raise ApiExcpetion(exception=exception, headers=headers)
