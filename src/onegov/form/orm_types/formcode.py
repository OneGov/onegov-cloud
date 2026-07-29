from __future__ import annotations

from lazy_object_proxy import Proxy  # type: ignore[import-untyped]
from onegov.form.parser.form import ParsedForm
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect
    from sqlalchemy.sql.type_api import _BindProcessorType
    from sqlalchemy.sql.type_api import _ResultProcessorType


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

    # HACK: In order to bypass the dialect's default serializer/deserializer
    #       we directly override the processors, instead of relying on the
    #       the default TypeDecorator way which applies our processing on
    #       top of the implementation's processing. This is a little less
    #       robust, since it depends on implementation details of the
    #       JSONB type adapter, which may change in the future and break
    #       these processors.

    def bind_processor(
        self,
        dialect: Dialect
    ) -> _BindProcessorType[ParsedForm]:

        return self._make_bind_processor(
            self._str_impl.bind_processor(dialect),
            ParsedForm.model_dump_json
        )

    def result_processor(
        self,
        dialect: Dialect,
        coltype: object
    ) -> _ResultProcessorType[ParsedForm]:
        string_process = self._str_impl.result_processor(dialect, coltype)

        def process(value: Any) -> ParsedForm | None:
            if value is None:
                return None
            if string_process:
                value = string_process(value)
            # NOTE: We defer parsing the JSON, until we actually need it.
            return Proxy(lambda: ParsedForm.model_validate_json(value))

        return process
