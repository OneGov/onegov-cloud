from datetime import datetime
from onegov.api import ApiApp
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpoint
from onegov.core.security import Public
from webob.exc import HTTPTooManyRequests


@ApiApp.json(
    model=ApiEndpointCollection,
    permission=Public
)
def view_api_endpoints(self, request):
    return [
        request.link(endpoint(request.app))
        for endpoint in self.endpoints.values()
    ]


@ApiApp.json(
    model=ApiEndpoint,
    permission=Public
)
def view_api_endpoint(self, request):

    # todo: add some headers
    #  https://stackoverflow.com/questions/16022624/examples-of-http-api-
    # rate-limiting-http-response-headers
    limit, expiration = request.app.rate_limit
    requests, timestamp = request.app.rate_limit_cache.get_or_create(
        request.client_addr,
        creator=lambda: (0, datetime.now()),
    )
    if (datetime.now() - timestamp).seconds < expiration:
        requests += 1
    else:
        timestamp = datetime.now()
        requests = 1
    request.app.rate_limit_cache.set(
        request.client_addr, (requests, timestamp)
    )
    if requests > limit:
        raise HTTPTooManyRequests()

    return self.query(request)
