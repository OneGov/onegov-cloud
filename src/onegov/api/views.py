from onegov.api import ApiApp
from onegov.api.models import ApiEndpoint, ApiException, AuthEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.token import get_token
from onegov.api.utils import authenticate, check_rate_limit
from onegov.core.security import Public
from webob.exc import HTTPMethodNotAllowed, HTTPUnauthorized
from wtforms import HiddenField


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from onegov.core.request import CoreRequest
    from morepath.request import Response
    from wtforms.form import _FormErrors


@ApiApp.json(model=ApiException, permission=Public)
def handle_exception(
    self: ApiException, request: 'CoreRequest'
) -> dict[str, dict[str, dict[str, Any] | str]]:

    @request.after
    def add_headers(response: 'Response') -> None:
        response.status_code = self.status_code
        response.headers['Content-Type'] = 'application/vnd.collection+json'
        for name, value in self.headers.items():
            response.headers.add(name, value)

    return {
        'collection': {
            'version': '1.0',
            'href': request.url,
            'error': {'message': self.message}
        }
    }


@ApiApp.json(
    model=ApiEndpointCollection,
    permission=Public
)
def view_api_endpoints(
    self: ApiEndpointCollection, request: 'CoreRequest'
) -> dict[str, Any]:
    @request.after
    def add_headers(response: 'Response') -> None:
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
def view_api_endpoint(
    self: 'ApiEndpoint[Any]', request: 'CoreRequest'
) -> dict[str, Any]:

    headers = check_rate_limit(request)

    @request.after
    def add_headers(response: 'Response') -> None:
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    try:
        payload = {
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
        if form := self.form(None, request):
            payload['template'] = {
                'data': [
                    {
                        'name': field.name,
                        'prompt': field.gettext(field.label.text)
                    }
                    for field in form
                    if not isinstance(field, HiddenField)
                ]
            }
        return payload

    except Exception as exception:
        raise ApiException(exception=exception, headers=headers) from exception


@ApiApp.json(
    model=ApiEndpointItem,
    permission=Public
)
def view_api_endpoint_item(
    self: ApiEndpointItem[Any], request: 'CoreRequest'
) -> dict[str, Any]:
    headers = check_rate_limit(request)

    @request.after
    def add_headers(response: 'Response') -> None:
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    try:
        endpoint = self.api_endpoint
        assert endpoint is not None
        links = self.links or {}
        data = self.data or {}
        payload = {
            'collection': {
                'version': '1.0',
                'href': request.link(endpoint),
                'items': [
                    {
                        'href': request.link(self),
                        'data': [
                            {
                                'name': name,
                                'value': value
                            }
                            for name, value in data.items()
                        ],
                        'links': [
                            {
                                'rel': rel,
                                'href': (
                                    link if not link or isinstance(link, str)
                                    else request.link(link)
                                ),
                            }
                            for rel, link in links.items()
                        ]
                    }
                ],
            }
        }
        if form := self.form(request):
            payload['template'] = {
                'data': [
                    {
                        'name': field.name,
                        'prompt': field.gettext(field.label.text)
                    }
                    for field in form
                    if not isinstance(field, HiddenField)
                ]
            }
        return payload

    except Exception as exception:
        raise ApiException(exception=exception, headers=headers) from exception


@ApiApp.json(
    model=ApiEndpointItem,
    permission=Public,
    request_method='PUT'
)
def edit_api_endpoint_item(
    self: ApiEndpointItem[Any], request: 'CoreRequest'
) -> None:

    endpoint = self.api_endpoint
    assert endpoint is not None
    try:
        form = self.form(request)
        if form is None:
            raise HTTPMethodNotAllowed()

        api_key = authenticate(request)
        if api_key.read_only:
            raise HTTPUnauthorized()

        def walk_errors(
            errors: 'Sequence[str] | _FormErrors',
            prefix: str | None
        ) -> 'Generator[tuple[str | None, str]]':

            if isinstance(errors, dict):
                for suffix, errs in errors.items():
                    yield from walk_errors(
                        errs,
                        suffix if prefix is None else f'{prefix}.{suffix}'
                    )
            else:
                for error in errors:
                    yield prefix, error

        if not form.validate():
            raise ApiException(
                ', '.join(
                    f'{field_name}: {error}' if field_name else error
                    for prefix, errors in form.errors.items()
                    for field_name, error in walk_errors(errors, prefix)
                ),
                status_code=400
            )

        endpoint.apply_changes(self.item, form)

    except Exception as exception:
        raise ApiException(exception=exception) from exception


@ApiApp.json(model=AuthEndpoint, permission=Public)
def get_time_restricted_token(
    self: AuthEndpoint, request: 'CoreRequest'
) -> dict[str, str]:
    try:
        return get_token(request)
    except Exception as exception:
        raise ApiException(exception=exception) from exception
