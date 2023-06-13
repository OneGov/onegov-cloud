from collections.abc import Callable
from typing import overload, Generic, TypeVar
from typing_extensions import Self

_T = TypeVar('_T')
_RT = TypeVar('_RT')

class reify(Generic[_T, _RT]):
    wrapped: Callable[[_T], _RT]
    def __init__(self: 'reify[_T, _RT]', wrapped: Callable[[_T], _RT]) -> None: ...
    @overload
    def __get__(self, inst: None, objtype: type[_T] | None = None) -> Self: ...
    @overload
    def __get__(self, inst: _T, objtype: type[_T] | None = None) -> _RT: ...
