from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.models import ApiExcpetion
from onegov.api.utils import check_rate_limit
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
                    for item, title in self.batch.items()
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
