from __future__ import annotations

from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy_utils.operators import CaseInsensitiveComparator


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect
    _Base = TypeDecorator[str]
else:
    _Base = TypeDecorator


class LowercaseText(_Base):
    """ Text column that forces all text to be lowercase. """

    impl = TEXT
    # FIXME: This was spelled incorrectly, but fixing the spelling
    #        causes some issues with custom join conditions
    omparator_factory = CaseInsensitiveComparator
    cache_ok = True

    def process_bind_param(
        self,
        value: str | None,
        dialect: Dialect
    ) -> str | None:

        return None if value is None else value.lower()
