# We use our own custom json implementation. In the libres library we made this
# configurable. Since onegov.core is a framework we don't do that though, we
# want all onegov.core applications with the same framework version to be able
# to read each others json.
#
# Therefore we use a common denominator kind of json encoder/decoder.
from __future__ import annotations

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect


class JSON(TypeDecorator[dict[str, Any]]):
    """ A JSONB based type that coerces None's to empty dictionaries.

    That is, this JSONB column does not have NULL values, it only has
    falsy values (an empty dict).

    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(
        self,
        value: dict[str, Any] | None,
        dialect: Dialect
    ) -> dict[str, Any]:

        return {} if value is None else value

    def process_result_value(
        self,
        value: dict[str, Any] | None,
        dialect: Dialect
    ) -> dict[str, Any]:

        return {} if value is None else value


MutableDict.associate_with(JSON)
