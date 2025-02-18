from collections.abc import Callable, Mapping
from typing import Any, Any as Incomplete
from typing_extensions import TypeAlias

from babel import Locale
from sqlalchemy import Column

_TranslatableColumn: TypeAlias = Column[Mapping[str, str]] | Column[Mapping[str, str] | None]
_Locale: TypeAlias = Callable[[Any, str], Locale | str] | Callable[[Any], Locale | str] | Callable[[], Locale | str] | Locale | str

class TranslationHybrid:
    default_value: str | None
    def __init__(self, current_locale: Callable[[], _Locale | None], default_locale: Callable[[], _Locale | None], default_value: str | None = None) -> None: ...
    def getter_factory(self, attr: _TranslatableColumn) -> Incomplete: ...
    def setter_factory(self, attr: _TranslatableColumn) -> Incomplete: ...
    def expr_factory(self, attr: _TranslatableColumn) -> Incomplete: ...
    # FIXME: In SQLAlchemy 2.0 this should return a hybrid_property
    def __call__(self, attr: _TranslatableColumn) -> Column[str | None]: ...
