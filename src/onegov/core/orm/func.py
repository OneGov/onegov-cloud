from __future__ import annotations

from sqlalchemy.sql.functions import ReturnTypeFromArgs

from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    # FIXME: Once we upgrade to SQLAlchemy 2.0 we no longer have to do
    #        this since the base class will be generic at runtime too
    #        and will support cls.__getitem__
    _T = TypeVar('_T')

    class unaccent(ReturnTypeFromArgs[_T]):  # noqa: N801
        ...
else:

    class unaccent(ReturnTypeFromArgs):  # noqa: N801
        """ Produce an UNACCENT expression. """

        inherit_cache = True
