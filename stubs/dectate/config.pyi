import abc
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from types import FrameType, TracebackType
from typing import Any, ClassVar, TypeVar
from typing_extensions import ParamSpec

from .app import App, Config
from .sentinel import Sentinel

_T = TypeVar('_T')
_F = TypeVar('_F', bound=Callable[..., Any])
_P = ParamSpec('_P')

order_count: int

class Configurable:
    _directives: list[tuple[Directive, object]]
    app_class: type[App] | None
    extends: list[Configurable]
    config: Config
    committed: bool
    def __init__(self, extends: list[Configurable], config: Config): ...
    def register_directive(self, directive: Directive, obj: Any) -> None: ...
    def get_action_classes(self) -> dict[type[Action], str]: ...
    def setup(self) -> None: ...
    def setup_config(self, action_class: type[Action]) -> None: ...
    def delete_config(self, action_class: type[Action]) -> None: ...
    def group_actions(self) -> None: ...
    def get_action_group(self, action_class: type[Action]) -> ActionGroup | None: ...
    def action_extends(self, action_class: type[Action]) -> list[ActionGroup]: ...
    def execute(self) -> None: ...

class ActionGroup:
    action_class: type[Action]
    extends: list[ActionGroup]
    def __init__(self, action_class: type[Action], extends: list[ActionGroup]) -> None: ...
    def add(self, action: Action, obj: Any) -> None: ...
    def prepare(self, configurable: Configurable) -> None: ...
    def get_actions(self) -> list[Action]: ...
    def combine(self, actions: list[ActionGroup]) -> None: ...
    def execute(self, configurable: Configurable) -> None: ...

class Action(metaclass=abc.ABCMeta):
    config: ClassVar[dict[str, Callable[..., Any]]]
    app_class_arg: bool
    depends: list[type[Action]]
    group_class: type[Action] | None
    filter_name: dict[str, str]
    def filter_get_value(self, name: str) -> Any | Sentinel: ...
    filter_compare: dict[str, Callable[[Any, Any], bool]]
    filter_convert: dict[str, Callable[[str], Any]]
    directive: Directive | None
    def __init__(self) -> None: ...
    @property
    def code_info(self) -> CodeInfo | None: ...
    def get_value_for_filter(self, name: str) -> Any | Sentinel: ...
    @abc.abstractmethod
    def identifier(self, **kw: Any) -> Any: ...
    def discriminators(self, **kw: Any) -> Iterable[Any]: ...
    @abc.abstractmethod
    def perform(self, obj: Any, **kw: Any) -> None: ...
    @staticmethod
    def before(**kw: Any) -> None: ...
    @staticmethod
    def after(**kw: Any) -> None: ...

class Composite(metaclass=abc.ABCMeta):
    query_classes: list[type[Action]]
    filter_convert: dict[str, Callable[[str], Any]]
    def __init__(self) -> None: ...
    @property
    def code_info(self) -> CodeInfo | None: ...
    @abc.abstractmethod
    def actions(self, obj: Any) -> Iterable[tuple[Action, Any]]: ...

class Directive:
    action_factory: Callable[..., Action]
    code_info: CodeInfo
    app_class: type[App]
    configurable: Configurable
    args: tuple[Any, ...]
    kw: dict[str, Any]
    argument_info: tuple[tuple[Any, ...], dict[str, Any]]
    # FIXME: ParamSpec might be too strict for optional parameters
    def __init__(self, action_factory: Callable[_P, Action], code_info: CodeInfo, app_class: type[App], args: _P.args, kw: _P.kwargs) -> None: ...
    @property
    def directive_name(self) -> str: ...
    def action(self) -> Action: ...
    def __enter__(self) -> DirectiveAbbreviation: ...
    def __exit__(self, type: type[BaseException] | None, value: BaseException | None, tb: TracebackType | None) -> None: ...
    def __call__(self, wrapped: _T) -> _T: ...
    def log(self, configurable: Configurable, obj: Any) -> None: ...

class DirectiveAbbreviation:
    directive: Directive
    def __init__(self, directive: Directive) -> None: ...
    def __call__(self, *args: Any, **kw: Any) -> Directive: ...

def commit(*apps: type[App]) -> None: ...
def sort_configurables(configurables: Iterable[Configurable]) -> list[Configurable]: ...
def sort_action_classes(action_classes: Iterable[type[Action]]) -> list[type[Action]]: ...
def group_action_classes(action_classes: Iterable[type[Action]]) -> set[type[Action]]: ...
def expand_actions(actions: Iterable[Action | Composite]) -> Iterator[Action]: ...

class CodeInfo:
    path: str
    lineno: int
    sourceline: str
    def __init__(self, path: str, lineno: int, sourceline: str) -> None: ...
    def filelineno(self) -> str: ...

def create_code_info(frame: FrameType) -> CodeInfo: ...
def factory_key(item: tuple[str, _F]) -> Iterable[tuple[str, _F]]: ...
def get_factory_arguments(action_class: type[Action], config: Config, factory: Callable[..., Any], app_class: type[App]) -> dict[str, Any]: ...
def dotted_name(cls: type) -> str: ...
