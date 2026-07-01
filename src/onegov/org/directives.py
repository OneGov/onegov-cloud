from __future__ import annotations

from dectate import Action
from itertools import count

from typing import cast, Any, ClassVar, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.elements import LinkGroup
    from onegov.directory.models import DirectoryEntry
    from onegov.event.models import Occurrence
    from onegov.org.models import Boardlet as _Boardlet
    from onegov.org.request import OrgRequest
    from onegov.user import User
    from sqlalchemy.orm import Query
    from typing import Protocol, TypedDict

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


class HomepageWidgetAction(Action):
    """ Register a cronjob. """

    config = {
        'homepage_widget_registry': dict
    }

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def identifier(
        self,
        homepage_widget_registry: dict[str, RegisteredHomepageWidget]
    ) -> str:
        return self.tag

    def perform(
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

    def identifier(
        self,
        export_registry: dict[str, Any]
    ) -> str:
        return self.id

    def perform(
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

    def identifier(
        self,
        linkgroup_registry: list[LinkGroupFactory]
    ) -> int:
        return self.name

    def perform(
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

    def identifier(
        self,
        directory_search_widget_registry: DirectorySearchWidgetRegistry
    ) -> str:
        return self.name

    def perform(
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

    def identifier(
        self,
        event_search_widget_registry: EventSearchWidgetRegistry
    ) -> str:
        return self.name

    def perform(
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
        self.boardlet_order = order
        self.icon = icon
        self.kind = kind

    def identifier(
        self,
        boardlets_registry: dict[BoardletKind, dict[str, BoardletConfig]]
    ) -> str:
        return f'{self.kind}-{self.name}'

    def perform(
        self,
        func: type[_Boardlet],
        boardlets_registry: dict[BoardletKind, dict[str, BoardletConfig]]
    ) -> None:
        boardlets_registry[self.kind][self.name] = {
            'cls': func,
            'order': self.boardlet_order,
            'icon': self.icon,
        }
