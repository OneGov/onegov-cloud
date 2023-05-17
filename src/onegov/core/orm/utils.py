from sqlalchemy_utils import QueryChain as QueryChainBase


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from typing_extensions import Self


# FIXME: We should create stubs for QueryChainBase
class QueryChain(QueryChainBase):
    """ Extends SQLAlchemy Utils' QueryChain with some extra methods. """

    def slice(self, start: int | None, end: int | None) -> 'Self':
        return self[start:end]

    def first(self) -> Any | None:
        return next((o for o in self), None)

    def all(self) -> tuple[Any, ...]:
        return tuple(self)
