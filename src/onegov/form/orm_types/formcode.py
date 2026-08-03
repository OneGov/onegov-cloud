from __future__ import annotations

from lazy_object_proxy import Proxy  # type: ignore[import-untyped]
from onegov.form.parser.form import ParsedForm
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect


class Formcode(TypeDecorator[ParsedForm]):
    """
    Stores `ParsedForm` instances as JSONB and directly uses `model_dump_json`
    and `model_validate_json` for serialization/deserialization.

    This also uses a `lazy_object_proxy.Proxy` to defer parsing the JSONB
    payload, until we first try to access it in some way. That way we have
    to be less careful about whether or not we include a column of this
    type in query results.
    """

    impl = JSONB
    cache_ok = True

    @property
    def python_type(self) -> type[ParsedForm]:
        return ParsedForm

    def process_bind_param(
        self,
        value: ParsedForm | None,
        dialect: Dialect
    ) -> str | None:

        return None if value is None else value.model_dump_json(
            # NOTE: keep the payload as small as possible
            # FIXME: We would also like to exclude defaults, but that
            #        doesn't work well with discriminated unions, since
            #        the discriminator will always be at its default, so
            #        pydantic will exclude it and then fail to deserialize
            #        See https://github.com/pydantic/pydantic/issues/6465
            exclude_none=True
        )

    def process_result_value(
        self,
        value: str | bytes | None,
        dialect: Dialect
    ) -> ParsedForm | None:

        if not value:
            return None

        return Proxy(lambda: ParsedForm.model_validate_json(value))
