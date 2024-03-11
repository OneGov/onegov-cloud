import _typeshed
from collections.abc import Callable, Collection, Iterator
from typing import Any, Protocol, TypeVar, overload
from typing_extensions import ParamSpec, Self

from dectate.config import Action, Composite, Configurable, Directive

_ActionT = TypeVar('_ActionT', bound=Action | Composite)
_AppT = TypeVar('_AppT', bound=App)
_P = ParamSpec('_P')

class _DirectiveCallable(Protocol[_P]):
    action_factory: type[Action | Composite]
    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> Directive: ...

class _DirectiveMethod(classmethod[_AppT, _P, Directive]):
    action_factory: type[Action | Composite]
    @overload
    def __get__(self, instance: _AppT, owner: type[_AppT] | None = None, /) -> _DirectiveCallable[_P]: ...
    @overload
    def __get__(self, instance: None, owner: type[_AppT], /) -> _DirectiveCallable[_P]: ...

class Config:
    def __getattr__(self, name: str) -> Any: ...

class AppMeta(type):
    def __new__(cls: type[_typeshed.Self], name: str, bases: tuple[type[Any], ...], d: dict[str, Any]) -> _typeshed.Self: ...

class App(metaclass=AppMeta):
    logger_name: str
    dectate: Configurable
    config: Config
    @classmethod
    def get_directive_methods(cls) -> Iterator[tuple[str, _DirectiveMethod[Self, ...]]]: ...
    @classmethod
    def commit(cls) -> Collection[type[App]]: ...
    @classmethod
    def is_committed(cls) -> bool: ...
    @classmethod
    def clean(cls) -> None: ...

def directive(action_factory: Callable[_P, _ActionT]) -> _DirectiveMethod[Any, _P]: ...
