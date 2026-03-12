from __future__ import annotations

import sqlalchemy

from sqlalchemy_utils import QueryChain as QueryChainBase


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from typing import Self

    _T = TypeVar('_T')

    # we have to forward declare the implementation, since QueryChainBase
    # is only generic in our stub and not at runtime
    class QueryChain(QueryChainBase[_T]):
        def slice(self, start: int | None, end: int | None) -> Self: ...
        def first(self) -> _T | None: ...
        def all(self) -> tuple[_T, ...]: ...


class QueryChain(QueryChainBase):  # type:ignore
    """ Extends SQLAlchemy Utils' QueryChain with some extra methods. """

    def slice(self, start: int | None, end: int | None) -> Self:
        return self[start:end]

    def first(self) -> _T | None:
        return next((o for o in self), None)

    def all(self) -> tuple[_T, ...]:
        return tuple(self)


def maybe_merge(session: Session, obj: _T) -> _T:
    """ Merges the given obj into the given session, *if* this is possible.
    That is it acts like more forgiving session.merge().
    """
    if requires_merge(obj):
        obj = session.merge(obj, load=False)
        obj.is_cached = True  # type:ignore[attr-defined]

    return obj


def requires_merge(obj: object) -> bool:
    """ Returns true if the given object requires a merge, which is the
    case if the object is detached.


    """

    # no need for an expensive sqlalchemy.inspect call for these
    if isinstance(obj, (int, str, bool, float, tuple, list, dict, set)):
        return False

    info = sqlalchemy.inspect(obj, raiseerr=False)

    if not info:
        return False

    return info.detached
