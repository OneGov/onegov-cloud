from __future__ import annotations

from dataclasses import dataclass
from dectate import Action
from dectate import Composite
from itertools import count
from onegov.core.directives import HtmlHandleFormAction

from typing import cast, Any, ClassVar, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath
    from collections.abc import Callable
    from collections.abc import Iterator
    from onegov.core.elements import LinkGroup
    from onegov.directory.models import DirectoryEntry
    from onegov.event.models import Occurrence
    from onegov.form import Form
    from onegov.org.models import Boardlet as _Boardlet
    from onegov.org.request import OrgRequest
    from onegov.user import User
    from sqlalchemy.orm import Query
    from typing import Protocol, TypedDict
    from webob import Response

    type FormFactory = type[Form] | Callable[..., type[Form]]
    type SettingViewRegistry = dict[
        tuple[type, str],
        SettingViewMeta,
    ]

    type DirectorySearchWidgetRegistry = dict[
        str,
        type[RegisteredDirectorySearchWidget[Any]]
    ]
    type EventSearchWidgetRegistry = dict[
        str,
        type[RegisteredEventSearchWidget]
    ]
    type LinkGroupFactory = Callable[[OrgRequest, User], LinkGroup]
    type BoardletKind = Literal['user', 'citizen']

    class HomepageWidget(Protocol):
        @property
        def template(self) -> str: ...

    class RegisteredHomepageWidget(HomepageWidget, Protocol):
        tag: str

    class DirectorySearchWidget[EntryT: DirectoryEntry](Protocol):
        @property
        def search_query(self) -> Query[EntryT]: ...

        def adapt(
            self,
            query: Query[EntryT]
        ) -> Query[EntryT]: ...

    class RegisteredDirectorySearchWidget[EntryT: DirectoryEntry](
        DirectorySearchWidget[EntryT],
        Protocol
    ):
        name: str

    class EventSearchWidget(Protocol):
        @property
        def search_query(self) -> Query[Occurrence]: ...

        def adapt(
            self,
            query: Query[Occurrence]
        ) -> Query[Occurrence]: ...

    class RegisteredEventSearchWidget(EventSearchWidget, Protocol):
        name: str

    class SettingsDict(TypedDict):
        name: str
        title: str
        order: int
        icon: str
        category: str

    class BoardletConfig(TypedDict):
        cls: type[_Boardlet]
        order: tuple[int, int]
        icon: str


@dataclass(frozen=True)
class SettingViewMeta:
    model: type
    name: str
    form: FormFactory
    setting: str
    icon: str
    order: int
    category: str | None


class SettingViewMetaAction(Action):
    config = {
        'setting_view_registry': dict,
    }

    def __init__(
        self,
        model: type,
        name: str,
        form: FormFactory,
        setting: str | None,
        icon: str | None,
        order: int,
        category: str | None,
    ) -> None:
        self.model = model
        self.name = name
        self.form = form
        self.setting = setting
        self.icon = icon
        self.order = order
        self.category = category

    def identifier(  # type:ignore[override]
        self,
        setting_view_registry: SettingViewRegistry,
    ) -> tuple[type, str]:
        return self.model, self.name

    def perform(  # type:ignore[override]
        self,
        obj: Callable[..., Any],
        setting_view_registry: SettingViewRegistry,
    ) -> None:
        key = self.model, self.name
        if self.setting is None or self.icon is None:
            setting_view_registry.pop(key, None)
            return

        setting_view_registry[key] = SettingViewMeta(
            model=self.model,
            name=self.name,
            form=self.form,
            setting=self.setting,
            icon=self.icon,
            order=self.order,
            category=self.category,
        )


class SettingViewAction(Composite):
    query_classes = [HtmlHandleFormAction, SettingViewMetaAction]

    def __init__(
        self,
        model: type,
        name: str,
        form: FormFactory,
        setting: str | None = None,
        icon: str | None = None,
        order: int = 0,
        category: str | None = None,
        listed: bool = True,
        render: Callable[..., Response] | str | None = None,
        template: StrOrBytesPath | None = None,
        load: Callable[..., Any] | str | None = None,
        permission: object | str | None = None,
        internal: bool = False,
        pass_model: bool = False,
        **predicates: Any,
    ) -> None:
        if listed and (setting is None or icon is None):
            raise TypeError(
                'Listed setting views require setting and icon metadata'
            )
        if not listed and (setting is not None or icon is not None):
            raise TypeError(
                'Unlisted setting views cannot define setting or icon'
            )

        self.model = model
        self.name = name
        self.form = form
        self.setting = setting
        self.icon = icon
        self.order = order
        self.category = category
        self.listed = listed
        self.render = render
        self.template = template
        self.load = load
        self.permission = permission
        self.internal = internal
        self.pass_model = pass_model
        self.predicates = predicates

    def actions(
        self,
        obj: Callable[..., Any],
    ) -> Iterator[tuple[Action, Callable[..., Any]]]:
        yield HtmlHandleFormAction(
            model=self.model,
            form=self.form,
            render=self.render,
            template=self.template,
            load=self.load,
            permission=self.permission,
            internal=self.internal,
            pass_model=self.pass_model,
            name=self.name,
            **self.predicates,
        ), obj
        yield SettingViewMetaAction(
            model=self.model,
            name=self.name,
            form=self.form,
            setting=self.setting if self.listed else None,
            icon=self.icon if self.listed else None,
            order=self.order,
            category=self.category,
        ), obj


class HomepageWidgetAction(Action):
    """ Register a cronjob. """

    config = {
        'homepage_widget_registry': dict
    }

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def identifier(  # type:ignore[override]
        self,
        homepage_widget_registry: dict[str, RegisteredHomepageWidget]
    ) -> str:
        return self.tag

    def perform(  # type:ignore[override]
        self,
        func: Callable[[], HomepageWidget],
        homepage_widget_registry: dict[str, RegisteredHomepageWidget]
    ) -> None:
        widget = cast('RegisteredHomepageWidget', func())
        widget.tag = self.tag  # keep redundantly for ease of access

        homepage_widget_registry[self.tag] = widget


class ExportAction(Action):
    """ Register an export. """

    config = {
        'export_registry': dict
    }

    def __init__(self, id: str, **kwargs: Any) -> None:
        self.id = id
        self.kwargs = kwargs
        self.kwargs['id'] = id

    def identifier(  # type:ignore[override]
        self,
        export_registry: dict[str, Any]
    ) -> str:
        return self.id

    def perform(  # type:ignore[override]
        self,
        cls: Callable[..., Any],
        export_registry: dict[str, Any]
    ) -> None:
        export_registry[self.id] = cls(**self.kwargs)


class UserlinkAction(Action):
    """ Registers a user link group. """

    config = {
        'linkgroup_registry': list
    }

    counter: ClassVar = count(1)

    def __init__(self) -> None:
        self.name = next(self.counter)

    def identifier(  # type:ignore[override]
        self,
        linkgroup_registry: list[LinkGroupFactory]
    ) -> int:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: LinkGroupFactory,
        linkgroup_registry: list[LinkGroupFactory]
    ) -> None:
        linkgroup_registry.append(func)


class DirectorySearchWidgetAction(Action):
    """ Registers a directory search widget. """

    config = {
        'directory_search_widget_registry': dict
    }

    def __init__(self, name: str) -> None:
        self.name = name

    def identifier(  # type:ignore[override]
        self,
        directory_search_widget_registry: DirectorySearchWidgetRegistry
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        cls: type[DirectorySearchWidget[Any]],
        directory_search_widget_registry: DirectorySearchWidgetRegistry
    ) -> None:

        cls = cast('type[RegisteredDirectorySearchWidget[Any]]', cls)
        cls.name = self.name

        assert hasattr(cls, 'html')
        assert hasattr(cls, 'adapt')

        directory_search_widget_registry[self.name] = cls


class EventSearchWidgetAction(Action):
    """ Registers a text search widget. """

    config = {
        'event_search_widget_registry': dict
    }

    def __init__(self, name: str) -> None:
        self.name = name

    def identifier(  # type:ignore[override]
        self,
        event_search_widget_registry: EventSearchWidgetRegistry
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        cls: type[EventSearchWidget],
        event_search_widget_registry: EventSearchWidgetRegistry
    ) -> None:

        cls = cast('type[RegisteredEventSearchWidget]', cls)
        cls.name = self.name

        assert hasattr(cls, 'html')
        assert hasattr(cls, 'adapt')

        event_search_widget_registry[self.name] = cls


class Boardlet(Action):
    """ Registers a boardlet on the Dashboard. """

    config = {
        'boardlets_registry': lambda: {'user': {}, 'citizen': {}}
    }

    def __init__(
        self,
        name: str,
        order: tuple[int, int],
        icon: str = '',
        kind: Literal['user', 'citizen'] = 'user'
    ) -> None:

        assert isinstance(order, tuple) and len(order) == 2, """
            The order should consist of two values, a group and an order
            within the group.
        """

        self.name = name
        self.order = order
        self.icon = icon
        self.kind = kind

    def identifier(  # type:ignore[override]
        self,
        boardlets_registry: dict[BoardletKind, dict[str, BoardletConfig]]
    ) -> str:
        return f'{self.kind}-{self.name}'

    def perform(  # type:ignore[override]
        self,
        func: type[_Boardlet],
        boardlets_registry: dict[BoardletKind, dict[str, BoardletConfig]]
    ) -> None:
        boardlets_registry[self.kind][self.name] = {
            'cls': func,
            'order': self.order,
            'icon': self.icon,
        }
