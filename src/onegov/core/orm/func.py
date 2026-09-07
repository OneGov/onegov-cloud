from __future__ import annotations

from sqlalchemy.sql.functions import ReturnTypeFromArgs


class unaccent[T](ReturnTypeFromArgs[T]):  # ruff:ignore[invalid-class-name]
    """ Produce an UNACCENT expression. """

    inherit_cache = True
