from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint, AuthEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.models import ApiException


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
    if endpoint == 'authenticate':
        return AuthEndpoint(app)

    cls = ApiEndpointCollection(app).endpoints.get(endpoint)
    if not cls:
        raise ApiException('Not found', status_code=404)
    return cls(app, extra_parameters=extra_parameters, page=page)


@ApiApp.path(
    model=ApiEndpointItem,
    path='/api/{endpoint}/{id}',
)
def get_api_endpoint_item(app, endpoint, id):
    item = ApiEndpointItem(app, endpoint, id)
    if not item.api_endpoint or not item.item:
        raise ApiException('Not found', status_code=404)
    return item
