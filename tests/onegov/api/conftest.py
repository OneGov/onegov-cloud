from onegov.api import ApiApp
from onegov.api import ApiEndpoint
from onegov.core import Framework
from onegov.core.utils import Bunch
from pytest import fixture
from tests.shared.client import Client
from tests.shared.utils import create_app


class App(Framework, ApiApp):
    pass


class Collection:

    def __init__(self):
        self.batch = [
            Bunch(id=1, title='First item', a=1, b='2'),
            Bunch(id=2, title='Second item', a=5, b='6')
        ]
        self.next = None
        self.previous = None

    def by_id(self, id_):
        return {str(x.id): x for x in self.batch}.get(str(id_))


class Endpoint(ApiEndpoint):
    endpoint = 'endpoint'
    filter = []

    def __init__(self, app, extra_parameters=None, page=None):
        self._collection = Collection()
        super().__init__(app, extra_parameters, page)

    @property
    def collection(self):
        return self._collection

    def item_data(self, item):
        return {'title': item.title, 'a': item.a}

    def item_links(self, item):
        return {'b': item.b}


@App.setting(section='api', name='endpoints')
def api_endpoints():
    return [Endpoint]


@fixture(scope='function')
def app(request):
    app = create_app(App, request, use_maildir=False)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def endpoint_class(request):
    return Endpoint


@fixture(scope='function')
def client(app):
    yield Client(app)
