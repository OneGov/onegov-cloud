from __future__ import annotations

from onegov.api.models import ApiEndpoint
from onegov.api.models import ApiEndpointItem
from onegov.api.models import ApiException, ApiInvalidParamException
from onegov.core.utils import Bunch
from tests.onegov.agency.test_app import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import App, Endpoint


def test_api_exceptions() -> None:
    # small helper to reduce boiler-plate
    def as_captured_exception(
        exception: Exception,
        default_status_code: int = 500
    ) -> ApiException:
        try:
            with ApiException.capture_exceptions(
                default_status_code=default_status_code
            ):
                raise exception
        except ApiException as api_exception:
            return api_exception

    exception = ApiException()
    assert exception.message == 'Internal Server Error'
    assert exception.status_code == 500

    exception = as_captured_exception(ValueError('foo'))
    assert exception.message == 'Internal Server Error'
    assert exception.status_code == 500

    exception = as_captured_exception(ApiInvalidParamException('foo'))
    assert exception.message == 'foo'
    assert exception.status_code == 400

    exception = as_captured_exception(
        ApiInvalidParamException('foo'),
        default_status_code=299
    )
    assert exception.message == 'foo'
    assert exception.status_code == 400

    exception = as_captured_exception(
        ApiInvalidParamException('foo', status_code=300)
    )
    assert exception.message == 'foo'
    assert exception.status_code == 300

    exception = ApiInvalidParamException()
    assert exception.message == 'Invalid Parameter'
    assert exception.status_code == 400

    exception = ApiInvalidParamException('Invalid Param x', status_code=99)
    assert exception.message == 'Invalid Param x'
    assert exception.status_code == 99


def test_api_endpoint_item(app: App, endpoint_class: type[Endpoint]) -> None:
    request: Any = DummyRequest()
    request.app = app
    item: ApiEndpointItem[Any]
    item = ApiEndpointItem(request, 'endpoint', 1)  # type: ignore[arg-type]
    assert item.api_endpoint.__class__ == endpoint_class
    assert item.item is not None
    assert item.item.id == 1
    assert item.data == {'a': 1, 'title': 'First item'}
    assert item.links == {'b': '2'}


def test_api_endpoint(app: App, endpoint_class: type[Endpoint]) -> None:
    request: Any = DummyRequest()
    request.app = app
    # ... for_page
    new: ApiEndpoint[Any] | None
    new = ApiEndpoint(request).for_page(None)
    assert new is not None
    assert new.page is None
    assert new.extra_parameters == {}

    new = ApiEndpoint(request).for_page(1)
    assert new is not None
    assert new.page == 1
    assert new.extra_parameters == {}

    new = ApiEndpoint(request).for_page('1')  # type: ignore[arg-type]
    assert new is not None
    assert new.page == 1
    assert new.extra_parameters == {}

    new = ApiEndpoint(request, {'a': '1'}, 4).for_page(5)
    assert new is not None
    assert new.page == 5
    assert new.extra_parameters == {'a': '1'}

    new = ApiEndpoint(request).for_page(1)
    assert new is not None
    new = new.for_filter(a='1')
    assert new.page is None
    assert new.extra_parameters == {'a': '1'}

    # ... for_filter
    new = ApiEndpoint(request).for_filter()
    assert new.page is None
    assert new.extra_parameters == {}

    new = ApiEndpoint(request).for_filter(a='1')
    assert new.page is None
    assert new.extra_parameters == {'a': '1'}

    new = ApiEndpoint(request, {'a': '1'}, 4).for_filter(b='2')
    assert new.page is None
    assert new.extra_parameters == {'b': '2'}

    new = ApiEndpoint(request).for_filter(a='1').for_filter(b='2')
    assert new.page is None
    assert new.extra_parameters == {'b': '2'}

    new = ApiEndpoint(request).for_filter(a='1').for_page(1)
    assert new is not None
    assert new.page == 1
    assert new.extra_parameters == {'a': '1'}

    # ... for_item
    assert ApiEndpoint(request).for_item(None) is None
    assert endpoint_class(request).for_item(Bunch(id=1)).id == '1'
    assert endpoint_class(request).for_item(Bunch(id='1')).id == '1'
    assert endpoint_class(request).for_item(Bunch(id=Bunch(hex='1'))).id == '1'
    assert endpoint_class(request).for_item(Bunch(id=1)).endpoint == 'endpoint'

    # ... get_filter
    assert ApiEndpoint(request).get_filter('a') is None
    assert ApiEndpoint(request, {'a': '1'}).get_filter('a') == '1'

    # ... by_id
    assert endpoint_class(request).by_id(1).id == 1  # type: ignore[union-attr]
    assert endpoint_class(request).by_id(2).id == 2  # type: ignore[union-attr]
    assert endpoint_class(request).by_id(3).id == 3  # type: ignore[union-attr]
    assert endpoint_class(request).by_id(4) is None

    # .... item_data
    assert endpoint_class(request).item_data(Bunch(title=1, a=2)) == {
        'title': 1,
        'a': 2
    }

    # .... item_links
    assert endpoint_class(request).item_links(Bunch(b=2)) == {'b': 2}

    # ... links
    assert endpoint_class(request).links == {'next': None, 'prev': None}
    endpoint = endpoint_class(request)
    endpoint._collection.previous = Bunch(page=3)  # type: ignore[assignment]
    endpoint._collection.next = Bunch(page=5)  # type: ignore[assignment]
    assert endpoint.links['prev'].page == 3  # type: ignore[union-attr]
    assert endpoint.links['next'].page == 5  # type: ignore[union-attr]

    # ... batch
    batch = endpoint_class(request).batch
    assert {endpoint.id: item.title for endpoint, item in batch.items()} == {
        '1': 'First item', '2': 'Second item'
    }
