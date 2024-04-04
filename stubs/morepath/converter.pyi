from collections.abc import Callable, Mapping
from typing import Any, Generic, TypeVar, overload

_T = TypeVar('_T')

class Converter(Generic[_T]):
    single_decode: Callable[[str], _T | None]
    single_encode: Callable[[_T | None], str]
    def __init__(self: Converter[_T], decode: Callable[[str], _T | None], encode: Callable[[_T | None], str] | None = None) -> None: ...
    def decode(self, strings: list[str]) -> _T | None: ...
    def encode(self, value: _T | None) -> list[str]: ...
    def is_missing(self, value: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

class ListConverter(Generic[_T]):
    converter: Converter[_T]
    def __init__(self: ListConverter[_T], converter: Converter[_T]) -> None: ...
    def decode(self, strings: list[str]) -> list[_T | None]: ...
    def encode(self, values: list[_T | None]) -> list[str]: ...
    def is_missing(self, value: object) -> bool: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

IDENTITY_CONVERTER: Converter[str]

def get_converter(type: type[_T]) -> Converter[_T]: ...

class ConverterRegistry:
    get_converter: Callable[[type[_T]], Converter[_T]]
    def __init__(self) -> None: ...
    def register_converter(self, type: type[_T], converter: Converter[_T]) -> None: ...
    @overload
    def actual_converter(self, spec: list[type[_T]]) -> ListConverter[_T]: ...  # type: ignore[overload-overlap]
    @overload
    def actual_converter(self, spec: type[_T] | Converter[_T]) -> Converter[_T]: ...
    # this is for the empty list case, pretty icky but nothing we can do
    @overload
    def actual_converter(self, spec: list[Any]) -> Converter[str]: ...
    def argument_and_explicit_converters(self, arguments: Mapping[str, Any], converters: Mapping[str, Converter[Any] | list[Any] | type[Any]]) -> dict[str, Converter[Any] | ListConverter[Any]]: ...
