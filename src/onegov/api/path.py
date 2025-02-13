from __future__ import annotations

from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint, AuthEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.models import ApiException


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core import Framework
    from onegov.core.request import CoreRequest


@ApiApp.path(
    model=ApiEndpointCollection,
    path='/api'
)
def get_api_endpoints(app: Framework) -> ApiEndpointCollection:
    return ApiEndpointCollection(app)


@ApiApp.path(
    model=ApiEndpoint,
    path='/api/{endpoint}',
    converters={'page': int}
)
def get_api_endpoint(
    request: CoreRequest,
    app: Framework,
    endpoint: str,
    page: int = 0,
    extra_parameters: dict[str, Any] | None = None,
) -> ApiEndpoint[Any] | AuthEndpoint:

    if endpoint == 'authenticate':
        return AuthEndpoint(app)

    cls = ApiEndpointCollection(app).endpoints.get(endpoint)
    if not cls:
        raise ApiException('Not found', status_code=404)
    return cls(request, extra_parameters=extra_parameters, page=page)


@ApiApp.path(
    model=ApiEndpointItem,
    path='/api/{endpoint}/{id}',
)
def get_api_endpoint_item(
    request: CoreRequest, app: Framework, endpoint: str, id: str
) -> ApiEndpointItem[Any]:
    item: ApiEndpointItem[Any] = ApiEndpointItem(request, endpoint, id)
    if not item.api_endpoint or not item.item:  # for ex. ExtendedAgency
        raise ApiException('Not found', status_code=404)
    return item
