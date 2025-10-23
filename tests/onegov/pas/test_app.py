from __future__ import annotations

from onegov.pas.custom import get_global_tools
from onegov.pas.custom import get_top_navigation
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.utils import Bunch


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from .conftest import TestPasApp


class DummySession:
    def query(self, *args: object) -> Any:
        return self

    def filter(self, *args: object) -> Any:
        return self

    def first(self) -> None:
        return None

class DummyRequest():
    is_logged_in = False
    is_manager = False
    is_admin = False
    is_parliamentarian = False
    current_user = Bunch(id=Bunch(hex='abcd'))
    path = ''
    url = ''
    session = DummySession()
    identity = None

    def class_link(self, cls: type[object], name: str = '') -> str:
        return f'{cls.__name__}/{name}'

    def link(self, target: object, name: str | None = None) -> str:
        return f"{target.__class__.__name__}/{name}"

    def transform(self, url: str) -> str:
        return url

    def include(self, asset: object) -> None:
        pass

    def exclude_invisible(self, items: object) -> list[Any]:
        return []


def test_app_custom(pas_app: TestPasApp) -> None:
    def as_text(
        items: Iterable[Link | LinkGroup]
    ) -> list[Any]:
        result: list[Any] = []
        for item in items:
            if isinstance(item, Link):
                result.append(item.text)
            if isinstance(item, LinkGroup):
                result.append({item.title: as_text(item.links)})
        return result

    request: Any = DummyRequest()
    request.app = pas_app

    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == []

    request.is_logged_in = True
    request.current_username = 'Peter'
    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == [{'Peter': ['Logout']}]

    request.is_manager = True
    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == [{'Peter': ['Logout']}]

    request.is_admin = True
    assert as_text(get_top_navigation(request)) == []
