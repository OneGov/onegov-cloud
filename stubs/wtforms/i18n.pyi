from collections.abc import Callable, Iterable
from gettext import GNUTranslations
from typing import Protocol, TypeVar, overload

_T = TypeVar("_T")

class _SupportsUgettextAndUngettext(Protocol):
    def ugettext(self, __string: str, /) -> str: ...
    def ungettext(self, __singular: str, __plural: str, __n: int, /) -> str:
        ...

def messages_path() -> str: ...
def get_builtin_gnu_translations(languages: Iterable[str] | None = None) -> GNUTranslations: ...
@overload
def get_translations(
    languages: Iterable[str] | None = None, getter: Callable[[Iterable[str]], GNUTranslations] = ...
) -> GNUTranslations: ...
@overload
def get_translations(languages: Iterable[str] | None = None, *, getter: Callable[[Iterable[str]], _T]) -> _T: ...
@overload
def get_translations(languages: Iterable[str] | None, getter: Callable[[Iterable[str]], _T]) -> _T: ...

class DefaultTranslations:
    translations: _SupportsUgettextAndUngettext
    def __init__(self, translations: _SupportsUgettextAndUngettext) -> None: ...
    def gettext(self, string: str) -> str: ...
    def ngettext(self, singular: str, plural: str, n: int) -> str: ...

class DummyTranslations:
    def gettext(self, string: str) -> str: ...
    def ngettext(self, singular: str, plural: str, n: int) -> str: ...
