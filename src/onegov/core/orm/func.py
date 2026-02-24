from __future__ import annotations

from sqlalchemy.sql.functions import ReturnTypeFromArgs


from typing import TypeVar


_T = TypeVar('_T')


class unaccent(ReturnTypeFromArgs[_T]):  # noqa: N801
    """ Produce an UNACCENT expression. """

    inherit_cache = True
