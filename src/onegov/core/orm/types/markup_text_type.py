from __future__ import annotations

from markupsafe import escape, Markup
from sqlalchemy.types import TypeDecorator, TEXT


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect
    _Base = TypeDecorator[Markup]
else:
    _Base = TypeDecorator


class MarkupText(_Base):
    """ Text column that contains HTML/XML markup. """

    impl = TEXT

    cache_ok = True

    def process_bind_param(
        self,
        value: str | None,
        dialect: Dialect
    ) -> Markup | None:

        return None if value is None else escape(value)

    def process_literal_param(
        self,
        value: str | None,
        dialect: Dialect
    ) -> Markup | None:

        return None if value is None else escape(value)

    def process_result_value(
        self,
        value: str | None,
        dialect: Dialect
    ) -> Markup | None:

        # NOTE: It would be safer to sanitize the text, in case someone
        #       managed to bypass `process_bind_param` and inserted
        #       unsanitized markup into the database. However, this would
        #       also add a ton of static overhead. If we decide we want
        #       the additional safety, we should use an approach like
        #       OCQMS' lazy Sanitized text type.
        return None if value is None else Markup(value)  # nosec: B704
