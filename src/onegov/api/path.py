from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem


@ApiApp.path(
    model=ApiEndpointCollection,
    path='/api'
)
def get_api_endpoints(app):
    return ApiEndpointCollection(app)


@ApiApp.path(
    model=ApiEndpoint,
    path='/api/{endpoint}',
    converters=dict(page=int)
)
def get_api_endpoint(app, endpoint, page=0, extra_parameters=None):
    cls = ApiEndpointCollection(app).endpoints.get(endpoint)
    if cls:
        return cls(app, extra_parameters=extra_parameters, page=page)


@ApiApp.path(
    model=ApiEndpointItem,
    path='/api/{endpoint}/{id}',
)
def get_api_endpoint_item(app, endpoint, id):
    return ApiEndpointItem(app, endpoint, id)
