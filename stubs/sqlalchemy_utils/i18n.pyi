from collections.abc import Callable
from typing import Any, TypeVar
from typing_extensions import TypeAlias

from babel import Locale
from sqlalchemy import Column

_ColumnT = TypeVar('_ColumnT', bound=Column[Any])
_Locale: TypeAlias = Callable[[Any, str], Locale | str] | Callable[[Any], Locale | str] | Callable[[], Locale | str] | Locale | str


class TranslationHybrid:
    def __init__(self, current_locale: Callable[[], _Locale | None], default_locale: Callable[[], _Locale | None], default_value: str | None = None) -> None: ...
    def getter_factory(self, attr): ...
    def setter_factory(self, attr): ...
    def expr_factory(self, attr): ...
    # FIXME: In SQLAlchemy 2.0 this should return a hybrid_property
    def __call__(self, attr: _ColumnT) -> _ColumnT: ...
