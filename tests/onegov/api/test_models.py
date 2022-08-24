from onegov.api.models import ApiEndpoint
from onegov.api.models import ApiEndpointCollection
from onegov.api.models import ApiEndpointItem
from onegov.api.models import ApiExcpetion
from onegov.core.utils import Bunch


def test_api_exception():
    exception = ApiExcpetion(exception=ValueError('foo'))
    assert exception.message == 'Internal Server Error'
    assert exception.status_code == 500


def test_api_endpoint_collection(app, endpoint_class):
    collection = ApiEndpointCollection(app)
    assert collection.endpoints == {'endpoint': endpoint_class}


def test_api_endpoint_item(app, endpoint_class):
    item = ApiEndpointItem(app, 'endpoint', 1)
    assert item.api_endpoint.__class__ == endpoint_class
    assert item.item.id == 1
    assert item.data == {'a': 1}
    assert item.links == {'b': '2'}


def test_api_endpoint(app, endpoint_class):
    # ... for_page
    new = ApiEndpoint(app).for_page(None)
    assert new.page is None
    assert new.extra_parameters == {}

    new = ApiEndpoint(app).for_page(1)
    assert new.page == 1
    assert new.extra_parameters == {}

    new = ApiEndpoint(app).for_page('1')
    assert new.page == 1
    assert new.extra_parameters == {}

    new = ApiEndpoint(app, {'a': 1}, 4).for_page(5)
    assert new.page == 5
    assert new.extra_parameters == {'a': 1}

    new = ApiEndpoint(app).for_page(1).for_filter(a=1)
    assert new.page is None
    assert new.extra_parameters == {'a': 1}

    # ... for_filter
    new = ApiEndpoint(app).for_filter()
    assert new.page is None
    assert new.extra_parameters == {}

    new = ApiEndpoint(app).for_filter(a=1)
    assert new.page is None
    assert new.extra_parameters == {'a': 1}

    new = ApiEndpoint(app, {'a': 1}, 4).for_filter(b=2)
    assert new.page is None
    assert new.extra_parameters == {'b': 2}

    new = ApiEndpoint(app).for_filter(a=1).for_filter(b=2)
    assert new.page is None
    assert new.extra_parameters == {'b': 2}

    new = ApiEndpoint(app).for_filter(a=1).for_page(1)
    assert new.page == 1
    assert new.extra_parameters == {'a': 1}

    # ... for_item
    assert ApiEndpoint(app).for_item(None) is None
    assert endpoint_class(app).for_item(Bunch(id=1)).id == '1'
    assert endpoint_class(app).for_item(Bunch(id='1')).id == '1'
    assert endpoint_class(app).for_item(Bunch(id=Bunch(hex='1'))).id == '1'
    assert endpoint_class(app).for_item(Bunch(id=1)).endpoint == 'endpoint'

    # ... get_filter
    assert ApiEndpoint(app).get_filter('a') is None
    assert ApiEndpoint(app, {'a': 1}).get_filter('a') == 1

    # ... by_id
    assert endpoint_class(app).by_id(1).id == 1
    assert endpoint_class(app).by_id(2).id == 2
    assert endpoint_class(app).by_id(3) is None

    # ... item_title
    assert ApiEndpoint(app).item_title(None) == ''
    assert ApiEndpoint(app).item_title(Bunch(title='x')) == 'x'

    # .... item_data
    assert endpoint_class(app).item_data(Bunch(a=1)) == {'a': 1}

    # .... item_links
    assert endpoint_class(app).item_links(Bunch(b=2)) == {'b': 2}

    # ... links
    assert endpoint_class(app).links == {'next': None, 'prev': None}
    endpoint = endpoint_class(app)
    endpoint._collection.previous = Bunch(page=3)
    endpoint._collection.next = Bunch(page=5)
    assert endpoint.links['prev'].page == 3
    assert endpoint.links['next'].page == 5

    # ... batch
    batch = endpoint_class(app).batch
    assert [item.id for item in batch] == ['1', '2']
    assert list(batch.values()) == ['First item', 'Second item']
