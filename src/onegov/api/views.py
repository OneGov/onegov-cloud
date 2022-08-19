from onegov.api import ApiApp
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpoint
from onegov.core.security import Public


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
    return self.query(request)
