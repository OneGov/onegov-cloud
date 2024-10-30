from collections.abc import Callable, Iterator, Sequence
from inspect import FullArgSpec
from typing import Any, Generic, NamedTuple, TypeVar
from typing_extensions import ParamSpec, TypeAlias

from reg.predicate import Predicate, PredicateRegistry

_T = TypeVar('_T')
_F = TypeVar('_F', bound=Callable[..., Any])
_P = ParamSpec('_P')
_GetKeyLookup: TypeAlias = Callable[[PredicateRegistry], _KeyLookup]

class _KeyLookup:
    def component(self, key: Sequence[Any], /) -> Callable[..., Any] | None: ...
    def fallback(self, key: Sequence[Any], /) -> Callable[..., Any] | None: ...
    def all(self, key: Sequence[Any], /) -> Iterator[Callable[..., Any]]: ...

class dispatch:
    predicates: list[Predicate]
    get_key_lookup: _GetKeyLookup
    def __init__(self, *predicates: str | Predicate, get_key_lookup: _GetKeyLookup = ...) -> None: ...
    def __call__(self, callable: Callable[_P, _T]) -> Callable[_P, _T]: ...

def identity(registry: PredicateRegistry) -> PredicateRegistry: ...

class LookupEntry(NamedTuple, Generic[_F]):
    lookup: _GetKeyLookup
    key: tuple[Any, ...]

    @property
    def component(self) -> _F | None: ...
    @property
    def fallback(self) -> _F | None: ...
    @property
    def matches(self) -> Iterator[_F]: ...
    @property
    def all_matches(self) -> list[_F]: ...

class Dispatch(Generic[_P, _T]):
    wrapped_func: Callable[_P, _T]
    get_key_lookup: _GetKeyLookup
    def __init__(self: Dispatch[_P, _T], predicates: list[Predicate], callable: Callable[_P, _T], get_key_lookup: _GetKeyLookup) -> None: ...
    def clean(self) -> None: ...
    def add_predicates(self, predicates: list[Predicate]) -> None: ...
    def register(self, func: Callable[_P, _T] | None = ..., **key_dict: dict[str, Any]) -> Callable[_P, _T]: ...
    def by_args(self, *args: _P.args, **kw: _P.kwargs) -> LookupEntry[Callable[_P, _T]]: ...
    def by_predicates(self, **predicate_values: Any) -> LookupEntry[Callable[_P, _T]]: ...
    # auto-generated by _define_call in the constructor
    def call(self, *args: _P.args, **kwargs: _P.kwargs) -> _T: ...

def validate_signature(f: Callable[..., Any], dispatch: Dispatch[..., Any]) -> None: ...
def format_signature(args: FullArgSpec) -> str: ...
def same_signature(a: FullArgSpec, b: FullArgSpec) -> bool: ...
def execute(code_source: str, **namespace: Any) -> dict[str, Any]: ...
