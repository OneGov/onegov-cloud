from __future__ import annotations

from sqlalchemy.sql.functions import ReturnTypeFromArgs


class unaccent[T](ReturnTypeFromArgs[T]):  # noqa: N801
    """ Produce an UNACCENT expression. """

    inherit_cache = True
