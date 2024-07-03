from collections.abc import Callable
from typing import Any, Generic, TypeVar, overload
from typing_extensions import Concatenate, ParamSpec

from reg.dispatch import Dispatch, dispatch, _GetKeyLookup
from reg.predicate import Predicate

_T = TypeVar('_T')
_T1 = TypeVar('_T1')
_R_co = TypeVar('_R_co', covariant=True)
_R_co1 = TypeVar('_R_co1', covariant=True)
_P = ParamSpec('_P')
_P1 = ParamSpec('_P1')

class dispatch_method(dispatch, Generic[_P, _T, _R_co]):
    callable: Callable[Concatenate[_T, _P], _R_co]
    first_invocation_hook: Callable[[Any], object]
    def __init__(self: dispatch_method[Any, Any, Any], *predicates: str | Predicate, get_key_lookup: _GetKeyLookup = ..., first_invocation_hook: Callable[[Any], object] = ...) -> None: ...
    # this needs to be able to override the bound type vars
    def __call__(self, callable: Callable[Concatenate[_T1, _P1], _R_co1]) -> dispatch_method[_P1, _T1, _R_co1]: ...  # type:ignore[override]
    @overload
    def __get__(self, obj: _T, type: type[_T] | None = None) -> Callable[_P, _R_co]: ...
    @overload
    def __get__(self, obj: None, type: type[_T] | None = None) -> Callable[Concatenate[_T, _P], _R_co]: ...

class DispatchMethod(Dispatch[_P, _T]): ...

def methodify(func: Callable[_P, _T], selfname: str | None = ...) -> Callable[Concatenate[Any, _P], _T]: ...
def clean_dispatch_methods(cls: type[object]) -> None: ...
