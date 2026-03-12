from __future__ import annotations

from dectate import Action
from morepath.directive import HtmlAction
from morepath.directive import ViewAction
from morepath.request import Response
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.custom import json
from onegov.core.directives import HtmlHandleFormAction
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.election_day.forms import EmptyForm
from webob.exc import HTTPAccepted


from typing import cast
from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath
    from collections.abc import Callable
    from collections.abc import Iterable
    from onegov.core.directives import _RequestT
    from onegov.core.request import CoreRequest
    from typing import Protocol
    from typing import TypeAlias
    from webob import Response as BaseResponse
    from wtforms import Form

    FormCallable: TypeAlias = Callable[[Any, _RequestT], type[Form]]

    class InputScreenWidget(Protocol):
        @property
        def tag(self) -> str: ...
        @property
        def template(self) -> str: ...
        @property
        def usage(self) -> str: ...

    class ScreenWidget(InputScreenWidget, Protocol):
        category: str


class ManageHtmlAction(HtmlAction):

    """ HTML directive for manage views which makes sure the permission is set
    to private.

    """

    def __init__(
        self,
        model: type | str,
        render: Callable[[Any, _RequestT], BaseResponse] | str | None = None,
        template: StrOrBytesPath | None = None,
        load: Callable[[_RequestT], Any] | str | None = None,
        permission: object | str | None = None,
        internal: bool = False,
        **predicates: Any,
    ) -> None:

        super().__init__(
            model,
            render,
            template,
            load,
            Secret if permission == Secret else Private,
            internal,
            **predicates
        )


class ManageFormAction(HtmlHandleFormAction):

    """ HTML directive for manage forms which makes sure the permission is set
    to private. Sets a valid default for the template and form class.

    """

    def __init__(
        self,
        model: type | str,
        form: type[Form] | FormCallable[_RequestT] = EmptyForm,
        render: Callable[[Any, _RequestT], BaseResponse] | str | None = None,
        template: StrOrBytesPath = 'form.pt',
        load: Callable[[_RequestT], Any] | str | None = None,
        permission: object | str | None = None,
        internal: bool = False,
        **predicates: Any,
    ) -> None:

        super().__init__(
            model,
            form,
            render,
            template,
            load,
            Secret if permission == Secret else Private,
            internal,
            **predicates
        )


def render_svg(content: dict[str, Any], request: CoreRequest) -> Response:
    path = content.get('path')
    name = content.get('name')
    if not path:
        raise HTTPAccepted()

    svg_content = None
    fs = request.app.filestorage
    assert fs is not None
    with fs.open(path, 'r') as f:
        svg_content = f.read()

    return Response(
        svg_content,
        content_type='application/svg; charset=utf-8',
        content_disposition=f'inline; filename={name}'
    )


def render_pdf(content: dict[str, Any], request: CoreRequest) -> Response:
    path = content.get('path')
    name = content.get('name')
    if not path:
        raise HTTPAccepted()

    pdf_content = None
    fs = request.app.filestorage
    assert fs is not None
    with fs.open(path, 'rb') as f:
        pdf_content = f.read()

    return Response(
        pdf_content,
        content_type='application/pdf',
        content_disposition=f'inline; filename={name}.pdf'
    )


def render_json(content: dict[str, Any], request: CoreRequest) -> Response:
    data = content.get('data', {})
    name = content.get('name', 'data')
    return Response(
        json.dumps_bytes(data, sort_keys=True, indent=2),
        content_type='application/json; charset=utf-8',
        content_disposition=f'inline; filename={name}.json')


def render_csv(content: dict[str, Any], request: CoreRequest) -> Response:
    data = content.get('data', {})
    name = content.get('name', 'data')
    return Response(
        convert_list_of_dicts_to_csv(data),
        content_type='text/csv',
        content_disposition=f'inline; filename={name}.csv'
    )


class SvgFileViewAction(ViewAction):

    """ View directive for viewing SVG files from filestorage. The SVGs
    are created using a cronjob and might not be available. """

    def __init__(
        self,
        model: type | str,
        load: Callable[[_RequestT], Any] | str | None = None,
        permission: object | str = Public,
        internal: bool = False,
        **predicates: Any,
    ) -> None:

        super().__init__(
            model,
            render_svg,
            None,
            load,
            permission,
            internal,
            **predicates
        )


class PdfFileViewAction(ViewAction):

    """ View directive for viewing PDF files from filestorage. The PDFs
    are created using a cronjob and might not be available. """

    def __init__(
        self,
        model: type | str,
        load: Callable[[_RequestT], Any] | str | None = None,
        permission: object | str = Public,
        internal: bool = False,
        **predicates: Any,
    ) -> None:

        super().__init__(
            model,
            render_pdf,
            None,
            load,
            permission,
            internal,
            **predicates
        )


class JsonFileAction(ViewAction):

    """ View directive for viewing JSON data as file. """

    def __init__(
        self,
        model: type | str,
        load: Callable[[_RequestT], Any] | str | None = None,
        permission: object | str = Public,
        internal: bool = False,
        **predicates: Any,
    ) -> None:

        super().__init__(
            model,
            render_json,
            None,
            load,
            permission,
            internal,
            **predicates
        )


class CsvFileAction(ViewAction):

    """ View directive for viewing CSV data as file. """

    def __init__(
        self,
        model: type | str,
        load: Callable[[_RequestT], Any] | str | None = None,
        permission: object | str = Public,
        internal: bool = False,
        **predicates: Any,
    ) -> None:

        super().__init__(
            model,
            render_csv,
            None,
            load,
            permission,
            internal,
            **predicates
        )


class ScreenWidgetRegistry(dict[str, dict[str, 'ScreenWidget']]):

    def by_categories(
        self,
        categories: Iterable[str]
    ) -> dict[str, ScreenWidget]:

        result: dict[str, ScreenWidget] = {}
        for category in categories:
            result.update(self.get(category, {}))
        return result


class ScreenWidgetAction(Action):
    """ Register a screen widget. """

    config = {
        'screen_widget_registry': ScreenWidgetRegistry
    }

    def __init__(self, tag: str, category: str):
        self.tag = tag
        self.category = category

    def identifier(  # type:ignore[override]
        self,
        screen_widget_registry: ScreenWidgetRegistry
    ) -> str:
        return self.tag

    def perform(  # type:ignore[override]
        self,
        func: Callable[[], InputScreenWidget],
        screen_widget_registry: ScreenWidgetRegistry
    ) -> None:

        widget = cast('ScreenWidget', func())
        assert widget.tag == self.tag
        widget.category = self.category
        screen_widget_registry.setdefault(self.category, {})
        screen_widget_registry[self.category][self.tag] = widget
