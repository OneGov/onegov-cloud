from _typeshed import StrOrBytesPath
from collections.abc import Callable, Collection, Iterator, Mapping
from reg import KeyIndex
from reg.dispatch import Dispatch
from typing import Any, Literal, TypeVar
from typing_extensions import TypeAlias
from webob import Response as BaseResponse

import dectate
from .authentication import Identity
from .converter import Converter, ConverterRegistry
from .path import PathRegistry
from .predicate import PredicateRegistry
from .request import Request
from .settings import SettingRegistry
from .sentinel import Sentinel
from .template import TemplateEngineRegistry
from .tween import TweenRegistry

_T = TypeVar('_T')
_Type: TypeAlias = type

def isbaseclass(a: type, b: type) -> bool: ...

class SettingAction(dectate.Action):
    section: str
    name: str
    def __init__(self, section: str, name: str) -> None: ...
    def identifier(self, setting_registry: SettingRegistry) -> tuple[str, str]: ...  # type:ignore[override]
    def perform(self, obj: Any, setting_registry: SettingRegistry) -> None: ...  # type:ignore[override]

class SettingValue:
    value: Any
    def __init__(self, value: Any) -> None: ...
    def __call__(self) -> Any: ...

class SettingSectionAction(dectate.Composite):
    section: str
    def __init__(self, section: str) -> None: ...
    def actions(self, obj: Callable[[], Mapping[str, Any]]) -> Iterator[tuple[SettingAction, SettingValue]]: ...

class PredicateFallbackAction(dectate.Action):
    dispatch: Callable | str
    func: Callable | str
    def __init__(self, dispatch: Callable | str, func: Callable | str) -> None: ...
    def identifier(self, predicate_registry: PredicateRegistry) -> tuple[Callable, Callable]: ...  # type:ignore[override]
    def perform(self, obj: Any, predicate_registry: PredicateRegistry) -> None: ...  # type:ignore[override]

class PredicateAction(dectate.Action):
    dispatch: Callable | str
    name: str
    default: Any
    index: KeyIndex | str
    _after: Callable | str
    _before: Callable | str
    def __init__(
        self, dispatch: Callable | str, name: str, default: Any, index: KeyIndex | str, before: Callable | str | None = None, after: Callable | str | None = None
    ) -> None: ...
    def identifier(self, predicate_registry: PredicateRegistry) -> tuple[Callable, Callable, Callable]: ...  # type:ignore[override]
    def perform(self, obj: Any, predicate_registry: PredicateRegistry) -> None: ...  # type:ignore[override]
    @staticmethod
    def after(predicate_registry: PredicateRegistry) -> None: ...  # type:ignore[override]

class MethodAction(dectate.Action):
    dispatch_method: Dispatch | str
    key_dict: dict[str, Any]
    def __init__(self, dispatch_method: Dispatch | str, **kw: Any) -> None: ...
    def identifier(self, app_class: type[dectate.App]) -> tuple[Dispatch, tuple[Any, ...]]: ...  # type:ignore[override]
    def perform(self, obj: Callable, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]

class ConverterAction(dectate.Action):
    type: _Type | str
    def __init__(self, type: _Type | str) -> None: ...
    def identifier(self, converter_registry: ConverterRegistry) -> tuple[Literal['converter'], _Type]: ...  # type:ignore[override]
    def perform(self, obj: Callable, converter_registry: ConverterRegistry) -> None: ...  # type:ignore[override]

class PathAction(dectate.Action):
    model: type | None
    path: StrOrBytesPath
    variables: Callable[[Any], dict[str, Any]] | None
    converters: dict[str, Any] | None
    required: Collection[str] | None
    get_converters: Callable[[], dict[str, Any]] | None
    absorb: bool
    def __init__(
        self,
        path: StrOrBytesPath,
        model: type[_T] | None = None,
        variables: Callable[[_T], dict[str, Any]] | None = None,
        converters: dict[str, Any] | None = None,
        required: Collection[str] | None = None,
        get_converters: Callable[[], dict[str, Any]] | None = None,
        absorb: bool = False,
    ) -> None: ...
    def identifier(self, path_registry: PathRegistry) -> tuple[Literal['path'], type]: ...  # type:ignore[override]
    def discriminators(self, path_registry: PathRegistry) -> list[tuple[Literal['path'], type]]: ...  # type:ignore[override]
    def perform(self, obj: Callable, path_registry: PathRegistry) -> None: ...  # type:ignore[override]

class PathCompositeAction(dectate.Composite):
    model: type | str | None
    path: StrOrBytesPath
    variables: Callable[[Any], dict[str, Any]] | str | None
    converters: dict[str, Any] | None
    required: Collection[str] | None
    get_converters: Callable[[], dict[str, Any]] | str | None
    absorb: bool | str
    def __init__(
        self,
        path: StrOrBytesPath,
        model: type | None = None,
        variables: Callable[[Any], dict[str, Any]] | str | None = None,
        converters: dict[str, Any] | None = None,
        required: Collection[str] | None = None,
        get_converters: Callable[[], dict[str, Any]] | str | None = None,
        absorb: bool | str = False,
    ) -> None: ...
    def actions(self, obj: _T) -> Iterator[tuple[PathAction, _T]]: ...

class PermissionRuleAction(dectate.Action):
    model: type | str
    permission: object | str
    identity: Identity | Sentinel | str
    def __init__(self, model: type | str, permission: object | str, identity: Identity | Sentinel | str = ...) -> None: ...
    def identifier(self, app_class: type[dectate.App]) -> tuple[type | str, object | str, Identity | Sentinel | str]: ...  # type:ignore[override]
    def perform(self, obj: Callable, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]

template_directory_id: int

class TemplateDirectoryAction(dectate.Action):
    name: str
    def __init__(
        self, after: Callable | str | None = None, before: Callable | str | None = None, name: str | None = None
    ) -> None: ...
    def identifier(self, template_engine_registry: TemplateEngineRegistry) -> str: ...  # type:ignore[override]
    def perform(self, obj: Callable[[], StrOrBytesPath], template_engine_registry: TemplateEngineRegistry) -> None: ...  # type:ignore[override]

class TemplateLoaderAction(dectate.Action):
    extension: str
    def __init__(self, extension: str) -> None: ...
    def identifier(self, template_engine_registry: TemplateEngineRegistry) -> str: ...  # type:ignore[override]
    def perform(self, obj: Callable, template_engine_registry: TemplateEngineRegistry) -> None: ...  # type:ignore[override]

class TemplateRenderAction(dectate.Action):
    extension: str
    def __init__(self, extension) -> None: ...
    def identifier(self, template_engine_registry: TemplateEngineRegistry) -> str: ...  # type:ignore[override]
    def perform(self, obj: Callable, template_engine_registry: TemplateEngineRegistry) -> None: ...  # type:ignore[override]

def issubclass_or_none(a: type | None, b: type | None) -> bool: ...

class ViewAction(dectate.Action):
    model: type | str
    render: Callable[[Any, Request], BaseResponse] | str
    load: Callable[[Request], Any] | str | None
    template: StrOrBytesPath | None
    permission: object | str | None
    internal: bool
    predicates: dict[str, Any]
    def __init__(
        self,
        model,
        render: Callable[[Any, Request], BaseResponse] | str | None = None,
        template: StrOrBytesPath | None = None,
        load: Callable[[Request], Any] | str | None = None,
        permission: object | str | None = None,
        internal: bool = False,
        **predicates: Any,
    ) -> None: ...
    def key_dict(self) -> dict[str, Any]: ...
    def identifier(self, template_engine_registry: TemplateEngineRegistry, app_class: type[dectate.App]) -> tuple[Any, ...]: ...  # type:ignore[override]
    def perform(self, obj: Callable, template_engine_registry: TemplateEngineRegistry, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]

class JsonAction(ViewAction):
    group_class = ViewAction

class HtmlAction(ViewAction):
    group_class = ViewAction

class DummyModel: ...

class MountAction(PathAction):
    group_class: type[PathAction]
    name: str
    model: type[DummyModel]
    app: dectate.App
    variables: Callable[[Any], dict[str, Any]] | str | None  # type:ignore[assignment]
    converters: dict[str, Any] | None
    required: Collection[str] | None
    get_converters: Callable[[], dict[str, Any]] | str | None  # type:ignore[assignment]
    def __init__(
        self,
        path: StrOrBytesPath,
        app: type[dectate.App],
        variables: Callable[[Any], dict[str, Any]] | str | None = None,
        converters: dict[str, Any] | None = None,
        required: Collection[str] | None = None,
        get_converters: Callable[[], dict[str, Any]] | str | None = None,
        name: str | None = None,
    ) -> None: ...
    def discriminators(self, path_registry: PathRegistry) -> list[tuple[Literal['mount'], dectate.App]]: ...  # type:ignore[override]
    def perform(self, obj: Callable, path_registry: PathRegistry) -> None: ...  # type:ignore[override]

class DeferLinksAction(dectate.Action):
    group_class: type[PathAction]
    model: type | str
    def __init__(self, model: type | str) -> None: ...
    def identifier(self, path_registry: PathRegistry) -> tuple[Literal['defer_links'], type | str]: ...  # type:ignore[override]
    def discriminators(self, path_registry: PathRegistry) -> list[tuple[Literal['model'], type | str]]: ...  # type:ignore[override]
    def perform(self, obj: Any, path_registry: PathRegistry) -> None: ...  # type:ignore[override]

class DeferClassLinksAction(dectate.Action):
    group_class: type[PathAction]
    model: type | str
    variables: Callable[[Any], dict[str, Any]] | str
    def __init__(self, model: type | str, variables: Callable[[Any], dict[str, Any]] | str) -> None: ...
    def identifier(self, path_registry: PathRegistry) -> tuple[Literal['defer_links'], type | str]: ...  # type:ignore[override]
    def discriminators(self, path_registry: PathRegistry) -> list[tuple[Literal['model'], type | str]]: ...  # type:ignore[override]
    def perform(self, obj: Any, path_registry: PathRegistry) -> None: ...  # type:ignore[override]

tween_factory_id: int

class TweenFactoryAction(dectate.Action):
    under: Callable | str
    over: Callable | str
    name: str
    def __init__(
        self, under: Callable | None = None, over: Callable | None = None, name: str | None = None
    ) -> None: ...
    def identifier(self, tween_registry: TweenRegistry) -> str: ...  # type:ignore[override]
    def perform(self, obj, tween_registry: TweenRegistry) -> None: ...  # type:ignore[override]

class IdentityPolicyAction(dectate.Action):
    def __init__(self) -> None: ...
    def identifier(self, setting_registry: SettingRegistry, app_class: type[dectate.App]) -> tuple[()]: ...  # type:ignore[override]
    def perform(self, obj: Callable, setting_registry: SettingRegistry, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]

class VerifyIdentityAction(dectate.Action):
    identity: type | str
    def __init__(self, identity: type | str = ...) -> None: ...
    def identifier(self, app_class: type[dectate.App]) -> object | str: ...  # type:ignore[override]
    def perform(self, obj: Callable, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]

class DumpJsonAction(dectate.Action):
    model: type | str
    def __init__(self, model: type | str = ...) -> None: ...
    def identifier(self, app_class: type[dectate.App]) -> type | str: ...  # type:ignore[override]
    def perform(self, obj: Callable, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]

class LinkPrefixAction(dectate.Action):
    def __init__(self) -> None: ...
    def identifier(self, app_class: type[dectate.App]) -> tuple[()]: ...  # type:ignore[override]
    def perform(self, obj: Callable, app_class: type[dectate.App]) -> None: ...  # type:ignore[override]
