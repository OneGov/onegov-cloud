from collections.abc import Callable, Iterator, Sequence
from typing import Any, TypeVar
from typing_extensions import Self

from reg.dispatch import _KeyLookup

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

class Cache(dict[_KT, _VT]):
    func: Callable[[_KT], _VT]
    def __init__(self: Cache[_KT, _VT], func: Callable[[_KT], _VT]) -> None: ...
    def __missing__(self, key: _KT) -> _VT: ...

class DictCachingKeyLookup(_KeyLookup):
    key_lookup: _KeyLookup
    component: Callable[[Self, Sequence[Any]], Callable[..., Any] | None]
    fallback: Callable[[Self, Sequence[Any]], Callable[..., Any] | None]
    all: Callable[[Self, Sequence[Any]], Iterator[Callable[..., Any]]]
    def __init__(self, key_lookup: _KeyLookup) -> None: ...

class LruCachingKeyLookup(_KeyLookup):
    key_lookup: _KeyLookup
    component: Callable[[Self, Sequence[Any]], Callable[..., Any] | None]
    fallback: Callable[[Self, Sequence[Any]], Callable[..., Any] | None]
    all: Callable[[Self, Sequence[Any]], Iterator[Callable[..., Any]]]
    def __init__(self, key_lookup: _KeyLookup, component_cache_size: int, all_cache_size: int, fallback_cache_size: int) -> None: ...
