from _typeshed import StrOrBytesPath
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from typing_extensions import Self, TypeAlias

from dectate import Action
from webassets import Bundle, Environment

_Filter: TypeAlias = str | Collection[str] | None

class Asset:
    name: str
    assets: Sequence[str]
    filters: Mapping[str, _Filter] | None
    def __init__(self, name: str, assets: Sequence[str], filters: Mapping[str, _Filter]) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    @property
    def is_pure(self) -> bool: ...
    @property
    def is_single_file(self) -> bool: ...
    @property
    def path(self) -> str: ...
    @property
    def extension(self) -> str | None: ...

class WebassetRegistry:
    paths: list[str | bytes]
    filters: dict[str, _Filter]
    filter_product: dict[str, str]
    assets: dict[str, Asset]
    output_path: str
    cached_bundles: dict[str, Bundle]  # this appears to be unused
    url: str
    mapping: dict[str, str]
    def __init__(self) -> None: ...
    def register_path(self, path: StrOrBytesPath) -> None: ...
    def register_filter(self, name: str, filter: _Filter, produces: str | None = None) -> None: ...
    def register_asset(self, name: str, assets: Sequence[str], filters: Mapping[str, _Filter] | None = None) -> None: ...
    def find_file(self, name: str) -> str: ...
    def merge_filters(self, *filters: Mapping[str, _Filter]) -> dict[str, _Filter]: ...
    def get_bundles(self, name: str, filters: dict[str, str | None] | None = None) -> Iterator[Bundle]: ...
    def get_asset_filters(self, asset: Asset, filters: Mapping[str, _Filter]) -> list[str]: ...
    def get_environment(self) -> Environment: ...

class PathMixin:
    def absolute_path(self, path: str) -> str: ...

class WebassetPath(Action, PathMixin):
    def identifier(self, webasset_registry: WebassetRegistry) -> object: ...  # type:ignore[override]
    def perform(self, obj: Callable[[], str], webasset_registry: WebassetRegistry) -> None: ...  # type:ignore[override]

class WebassetOutput(Action, PathMixin):
    group_class = WebassetPath
    def identifier(self, webasset_registry: WebassetRegistry) -> type[Self]: ...  # type: ignore[override]
    def perform(self, obj: Callable[[], str], webasset_registry: WebassetRegistry) -> None: ...  # type: ignore[override]

class WebassetFilter(Action):
    group_class = WebassetPath
    name: str
    produces: str | None
    def __init__(self, name: str, produces: str | None = None) -> None: ...
    def identifier(self, webasset_registry: WebassetRegistry) -> str: ...  # type: ignore[override]
    def perform(self, obj: Callable[[], _Filter], webasset_registry: WebassetRegistry) -> None: ...  # type: ignore[override]

class WebassetMapping(Action):
    group_class = WebassetPath
    name: str
    def __init__(self, name: str) -> None: ...
    def identifier(self, webasset_registry: WebassetRegistry) -> str: ...  # type: ignore[override]
    def perform(self, obj: Callable[[], str], webasset_registry: WebassetRegistry) -> None: ...  # type: ignore[override]

class WebassetUrl(Action):
    group_class = WebassetPath
    def identifier(self, webasset_registry: WebassetRegistry) -> type[Self]: ...  # type: ignore[override]
    def perform(self, obj: Callable[[], str], webasset_registry: WebassetRegistry) -> None: ...  # type: ignore[override]

class Webasset(Action):
    group_class = WebassetPath
    name: str
    filters: Mapping[str, _Filter] | None
    def __init__(self, name: str, filters: Mapping[str, _Filter] | None = None) -> None: ...
    def identifier(self, webasset_registry: WebassetRegistry) -> str: ...  # type: ignore[override]
    def perform(self, obj: Callable[[], Iterator[str]], webasset_registry: WebassetRegistry) -> None: ...  # type: ignore[override]
