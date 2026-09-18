from __future__ import annotations
from typing import TYPE_CHECKING, Any

from onegov.api import ApiApp
from onegov.api.form import model_from_form
from onegov.api.models import ApiEndpoint, ApiException, AuthEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.token import get_token
from onegov.api.utils import authenticate, check_rate_limit
from onegov.core.security import Public
from onegov.form.fields import HoneyPotField
from webob.exc import HTTPMethodNotAllowed, HTTPNotFound, HTTPUnauthorized
from wtforms import HiddenField


if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from onegov.core.request import CoreRequest
    from onegov.core.types import JSONObject
    from onegov.form import Form
    from morepath.request import Response
    from wtforms.form import _FormErrors


@ApiApp.json(model=ApiException, permission=Public, open_data=True)
def handle_exception(
    self: ApiException, request: CoreRequest
) -> dict[str, dict[str, dict[str, Any] | str]]:

    @request.after
    def add_headers(response: Response) -> None:
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
    permission=Public,
    open_data=True
)
def view_api_endpoints(
    self: ApiEndpointCollection, request: CoreRequest
) -> dict[str, Any]:
    @request.after
    def add_headers(response: Response) -> None:
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    return {
        'collection': {
            'version': '1.0',
            'href': request.link(self),
            'queries': [
                {
                    'href': request.link(endpoint),
                    'rel': endpoint.endpoint,
                    'title': endpoint.title,
                    'description': endpoint.description,
                    'data': [
                        {'name': name} if not prompt else {
                            'name': name,
                            'prompt': prompt
                        } if isinstance(prompt, str) else {
                            'name': name,
                            'prompt': 'One of the given values '
                                      '(Can be specified multiple '
                                      'times or left unspecified)',
                            # NOTE: This is a custom extension of
                            #       Collection+JSON, that is a little
                            #       bit more machine-readable.
                            'values': list(prompt)
                        }
                        for name, prompt in endpoint.filters.items()
                    ]
                }
                for endpoint in self.endpoints.values()
            ]
        }
    }


def resolve_json_schema_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    assert ref.startswith('#/')
    resolved = root
    for key in ref[2:].split('/'):
        resolved = resolved[key]
    return resolved


def replace_json_schema_refs[T](
    data: T,
    json_schema: dict[str, Any]
) -> T:
    if isinstance(data, list):
        return [  # type: ignore[return-value]
            replace_json_schema_refs(value, json_schema)
            for value in data
        ]

    if not isinstance(data, dict):
        return data

    if '$ref' in data:
        return replace_json_schema_refs(  # type: ignore[return-value]
            resolve_json_schema_ref(json_schema, data['$ref']),
            json_schema
        )

    return {  # type: ignore[return-value]
        key: replace_json_schema_refs(value, json_schema)
        for key, value in data.items()
    }


def template_from_form(form: Form) -> dict[str, Any]:
    model_class = model_from_form(form)
    json_schema = model_class.model_json_schema() if model_class else {}
    properties = json_schema.get('properties', {})
    required_names = json_schema.get('required', ())
    return {
        'data': [
            {
                'name': field.name,
                'prompt': field.gettext(field.label.text),
                'required': field.name in required_names,
                'fieldset': fieldset.label,
                **({
                    'depends_on': [
                        {
                            'name': form[dependency['field_id']].name,
                            'value': dependency['raw_choice']
                        }
                        for dependency in field.depends_on.dependencies
                    ]
                } if hasattr(field, 'depends_on') else {}),
                **({
                    'value_json_schema': replace_json_schema_refs(
                        properties[field.name],
                        json_schema
                    )
                } if field.name in properties else {})
            }
            for fieldset in form.fieldsets
            for field in fieldset.fields.values()
            if not isinstance(field, (HiddenField, HoneyPotField))
        ]
    }


@ApiApp.json(
    model=ApiEndpoint,
    permission=Public,
    open_data=True
)
def view_api_endpoint(
    self: ApiEndpoint[Any, Any], request: CoreRequest
) -> dict[str, Any]:

    headers = check_rate_limit(request)

    @request.after
    def add_headers(response: Response) -> None:
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    with ApiException.capture_exceptions(headers=headers):
        payload: dict[str, JSONObject] = {
            'collection': {
                'version': '1.0',
                'href': request.link(self.for_filter()),
                'title': self.title,
                'description': self.description,
                'links': [
                    {
                        'rel': rel,
                        'href': request.link(item) if item else None
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
            payload['collection']['template'] = template_from_form(form)
        return payload


@ApiApp.json(
    model=ApiEndpointItem,
    permission=Public,
    open_data=True
)
def view_api_endpoint_item(
    self: ApiEndpointItem[Any, Any], request: CoreRequest
) -> dict[str, Any]:
    headers = check_rate_limit(request)

    @request.after
    def add_headers(response: Response) -> None:
        response.headers['Content-Type'] = 'application/vnd.collection+json'

    with ApiException.capture_exceptions(headers=headers):
        endpoint = self.api_endpoint
        assert endpoint is not None
        links = self.links or {}
        data = self.data or {}

        # make sure we are actually supposed to be able to see this
        # the API shouldn't include invisible items either (for now)
        if (item := self.item) and not request.is_visible(item):
            raise HTTPNotFound()

        payload: dict[str, JSONObject] = {
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
            payload['collection']['template'] = template_from_form(form)
        return payload


@ApiApp.json(
    model=ApiEndpointItem,
    permission=Public,
    request_method='PUT',
    open_data=False
)
def edit_api_endpoint_item(
    self: ApiEndpointItem[Any, Any], request: CoreRequest
) -> dict[str, Any] | None:

    with ApiException.capture_exceptions():
        endpoint = self.api_endpoint
        assert endpoint is not None
        form = self.form(request)
        if form is None:
            raise HTTPMethodNotAllowed()

        if not request.is_logged_in:
            api_key = authenticate(request)
            if api_key.read_only:
                raise HTTPUnauthorized()

        # make sure we are actually supposed to be able to see this
        # the API shouldn't include invisible items either (for now)
        if (item := self.item) and not request.is_visible(item):
            raise HTTPNotFound()

        def walk_errors(
            errors: Sequence[str] | _FormErrors,
            prefix: str | None
        ) -> Generator[tuple[str | None, str]]:

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

        return endpoint.apply_changes(self.item, form)


@ApiApp.json(model=AuthEndpoint, permission=Public, open_data=False)
def get_time_restricted_token(
    self: AuthEndpoint, request: CoreRequest
) -> dict[str, str]:
    with ApiException.capture_exceptions():
        if request.authorization is None:
            raise HTTPUnauthorized()

        return get_token(request)
