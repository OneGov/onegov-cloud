from dectate import Action


from typing import cast, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.elements import LinkGroup
    from onegov.directory.models import DirectoryEntry
    from onegov.event.models import Occurrence
    from onegov.org.models import Boardlet as _Boardlet
    from onegov.org.request import OrgRequest
    from onegov.user import User
    from sqlalchemy.orm import Query
    from typing import Protocol, TypeVar, TypedDict
    from typing_extensions import TypeAlias

    DirectoryEntryT = TypeVar('DirectoryEntryT', bound=DirectoryEntry)
    DirectorySearchWidgetRegistry: TypeAlias = dict[
        str,
        type['RegisteredDirectorySearchWidget[Any]']
    ]
    EventSearchWidgetRegistry: TypeAlias = dict[
        str,
        type['RegisteredEventSearchWidget']
    ]
    LinkGroupFactory: TypeAlias = Callable[[OrgRequest, User], LinkGroup]

    class HomepageWidget(Protocol):
        @property
        def template(self) -> str: ...

    class RegisteredHomepageWidget(HomepageWidget, Protocol):
        tag: str

    class DirectorySearchWidget(Protocol[DirectoryEntryT]):
        @property
        def search_query(self) -> Query[DirectoryEntryT]: ...

        def adapt(
            self,
            query: Query[DirectoryEntryT]
        ) -> Query[DirectoryEntryT]: ...

    class RegisteredDirectorySearchWidget(
        DirectorySearchWidget[DirectoryEntryT],
        Protocol[DirectoryEntryT]
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

    class BoardletConfig(TypedDict):
        cls: type[_Boardlet]
        order: tuple[int, int]


class HomepageWidgetAction(Action):
    """ Register a cronjob. """

    config = {
        'homepage_widget_registry': dict
    }

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def identifier(  # type:ignore[override]
        self,
        homepage_widget_registry: dict[str, 'RegisteredHomepageWidget']
    ) -> str:
        return self.tag

    def perform(  # type:ignore[override]
        self,
        func: 'Callable[[], HomepageWidget]',
        homepage_widget_registry: dict[str, 'RegisteredHomepageWidget']
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
        cls: 'Callable[..., Any]',
        export_registry: dict[str, Any]
    ) -> None:
        export_registry[self.id] = cls(**self.kwargs)


class UserlinkAction(Action):
    """ Registers a user link group. """

    config = {
        'linkgroup_registry': list
    }

    # FIXME: Use itertools.count
    counter = iter(range(1, 123456789))

    def __init__(self) -> None:
        self.name = next(self.counter)

    def identifier(  # type:ignore[override]
        self,
        linkgroup_registry: list['LinkGroupFactory']
    ) -> int:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: 'LinkGroupFactory',
        linkgroup_registry: list['LinkGroupFactory']
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
        directory_search_widget_registry: 'DirectorySearchWidgetRegistry'
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        cls: type['DirectorySearchWidget[Any]'],
        directory_search_widget_registry: 'DirectorySearchWidgetRegistry'
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
        event_search_widget_registry: 'EventSearchWidgetRegistry'
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        cls: type['EventSearchWidget'],
        event_search_widget_registry: 'EventSearchWidgetRegistry'
    ) -> None:

        cls = cast('type[RegisteredEventSearchWidget]', cls)
        cls.name = self.name

        assert hasattr(cls, 'html')
        assert hasattr(cls, 'adapt')

        event_search_widget_registry[self.name] = cls


class SettingsView(Action):
    """ Registers a settings view. """

    config = {
        'settings_view_registry': dict
    }

    def __init__(
        self,
        name: str,
        title: str,
        order: int = 0,
        icon: str =
        'fa-cogs'
    ) -> None:

        self.name = name
        self.setting: 'SettingsDict' = {
            'name': name,
            'title': title,
            'order': order,
            'icon': icon
        }

    def identifier(  # type:ignore[override]
        self,
        settings_view_registry: dict[str, 'SettingsDict']
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: Any,
        settings_view_registry: dict[str, 'SettingsDict']
    ) -> None:
        settings_view_registry[self.name] = self.setting


class Boardlet(Action):
    """ Registers a boardlet on the Dashboard. """

    config = {
        'boardlets_registry': dict
    }

    def __init__(self, name: str, order: tuple[int, int]):
        assert isinstance(order, tuple) and len(order) == 2, """
            The order should consist of two values, a group and an order
            within the group.
        """

        self.name = name
        self.order = order

    def identifier(  # type:ignore[override]
        self,
        boardlets_registry: dict[str, 'BoardletConfig']
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: type['_Boardlet'],
        boardlets_registry: dict[str, 'BoardletConfig']
    ) -> None:
        boardlets_registry[self.name] = {
            'cls': func,
            'order': self.order
        }
