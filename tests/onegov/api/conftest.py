from onegov.api import ApiApp
from onegov.api import ApiEndpoint
from onegov.core import Framework
from onegov.agency.api import PersonApiEndpoint
from onegov.core.utils import Bunch
from onegov.form import Form
from pytest import fixture
from tests.shared.client import Client
from tests.shared.utils import create_app
from wtforms import StringField
from wtforms.validators import InputRequired


class App(Framework, ApiApp):
    def __init__(self):
        self.org = Bunch(hidden_people_fields=[])


class ItemForm(Form):
    title = StringField(validators=[InputRequired()])


class Collection:

    def __init__(self):
        self.items = {
            '1': Bunch(id=1, title='First item', a=1, b='2'),
            '2': Bunch(id=2, title='Second item', a=5, b='6'),
            '3': Bunch(id=3, title='Hidden item', a=2, b='3', hidden=True),
        }
        self.batch = [
            item
            for item in self.items.values()
            if getattr(item, 'hidden', False) is False
        ]
        self.next = None
        self.previous = None

    def by_id(self, id_):
        return self.items.get(str(id_))


class Endpoint(ApiEndpoint):
    endpoint = 'endpoint'
    form_class = ItemForm
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

    def apply_changes(self, item, form):
        return


@App.setting(section='api', name='endpoints')
def api_endpoints():
    return [Endpoint, PersonApiEndpoint]

@App.permission_rule(model=Bunch, permission=object)
@App.permission_rule(model=Bunch, permission=object, identity=None)
def has_item_permission(app, identity, model, permission):
    return getattr(model, 'hidden', False) is False


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
