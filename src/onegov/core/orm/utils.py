from sqlalchemy_utils import QueryChain as QueryChainBase


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from typing_extensions import Self

    _T = TypeVar('_T')

    class QueryChain(QueryChainBase[_T]):
        def slice(self, start: int | None, end: int | None) -> 'Self': ...
        def first(self) -> _T | None: ...
        def all(self) -> tuple[_T, ...]: ...
else:

    class QueryChain(QueryChainBase):
        """ Extends SQLAlchemy Utils' QueryChain with some extra methods. """

        def slice(self, start: int | None, end: int | None) -> 'Self':
            return self[start:end]

        def first(self) -> _T | None:
            return next((o for o in self), None)

        def all(self) -> tuple[_T, ...]:
            return tuple(self)
