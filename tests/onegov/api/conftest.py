from __future__ import annotations

import pytest

from onegov.api import ApiApp
from onegov.api import ApiEndpoint
from onegov.core import Framework
from onegov.agency.api import PersonApiEndpoint
from onegov.core.utils import Bunch
from onegov.form import Form
from tests.shared.client import Client
from tests.shared.utils import create_app
from wtforms import StringField
from wtforms.validators import InputRequired


from typing import Any, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from collections.abc import Iterator


class App(Framework, ApiApp):
    def __init__(self) -> None:
        self.org = Bunch(hidden_people_fields=[])


class ItemForm(Form):
    title = StringField(validators=[InputRequired()])


class Collection:

    def __init__(self) -> None:
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

    def by_id(self, id_: int | str) -> Bunch | None:
        return self.items.get(str(id_))


class Endpoint(ApiEndpoint[Bunch]):  # type: ignore[type-var]
    endpoint = 'endpoint'
    form_class = ItemForm

    def __init__(
        self,
        app: App,
        extra_parameters: dict[str, str | None] | None = None,
        page: int | None = None
    ) -> None:

        self._collection = Collection()
        request: Any = Bunch(app=app)
        super().__init__(request, extra_parameters, page)

    @property
    def title(self) -> str:
        return 'Test Endpoint'

    @property
    def description(self) -> str:
        return 'This is just for testing'

    @property
    def collection(self) -> Collection:  # type: ignore[override]
        return self._collection

    def item_data(self, item: Bunch) -> dict[str, Any]:
        return {'title': item.title, 'a': item.a}

    def item_links(self, item: Bunch) -> dict[str, Any]:
        return {'b': item.b}

    def apply_changes(self, item: Bunch, form: object) -> None:
        return


@App.setting(section='api', name='endpoints')
def get_api_endpoints_handler(
) -> Callable[[pytest.FixtureRequest], Iterator[ApiEndpoint[Any]]]:

    def get_api_endpoints(
            request: pytest.FixtureRequest,
            page: int = 0,
            extra_parameters: dict[str, Any] | None = None
    ) -> Iterator[ApiEndpoint[Any]]:
        yield Endpoint(
            request, extra_parameters, page)  # type: ignore[arg-type]
        yield PersonApiEndpoint(
            request, extra_parameters, page)  # type: ignore[arg-type]

    return get_api_endpoints


@App.permission_rule(model=Bunch, permission=object)
@App.permission_rule(model=Bunch, permission=object, identity=None)
def has_item_permission(
    app: App,
    identity: object,
    model: Bunch,
    permission: object
) -> bool:
    return getattr(model, 'hidden', False) is False


@pytest.fixture(scope='function')
def app(request: pytest.FixtureRequest) -> Iterator[App]:
    app = create_app(App, request, use_maildir=False)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def endpoint_class(request: pytest.FixtureRequest) -> type[Endpoint]:
    return Endpoint


@pytest.fixture(scope='function')
def client(app: App) -> Iterator[Client]:
    yield Client(app)
