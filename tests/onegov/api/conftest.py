from __future__ import annotations

import pytest

from onegov.agency.collections import ExtendedPersonCollection
from onegov.api import ApiApp
from onegov.api import ApiEndpoint
from onegov.core import Framework
from onegov.agency.api import PersonApiEndpoint
from onegov.agency.models import ExtendedPerson
from onegov.core.utils import Bunch
from onegov.form import Form
from tests.shared.client import Client
from tests.shared.utils import create_app
from uuid import UUID
from wtforms import StringField
from wtforms.validators import InputRequired


from typing import Any, TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest


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
        request: CoreRequest,
        extra_parameters: dict[str, list[str]] | None = None,
        page: int | None = None
    ) -> None:

        self._collection = Collection()
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
) -> Callable[[CoreRequest], Iterator[ApiEndpoint[Any]]]:

    def get_api_endpoints(
            request: CoreRequest,
            page: int = 0,
            extra_parameters: dict[str, list[str]] | None = None
    ) -> Iterator[ApiEndpoint[Any]]:
        yield Endpoint(request, extra_parameters, page)
        yield PersonApiEndpoint(request, extra_parameters, page)

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


@App.path(model=ExtendedPerson, path='/person/{id}', converters={'id': UUID})
def get_person(app: App, id: UUID) -> ExtendedPerson | None:
    return ExtendedPersonCollection(app.session()).by_id(id)


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
