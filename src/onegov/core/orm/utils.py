from sqlalchemy.orm import attributes
from sqlalchemy.orm.session import _state_session  # type:ignore[attr-defined]
from sqlalchemy_utils import QueryChain as QueryChainBase


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from typing_extensions import Self

    from onegov.core.orm import Base

    _T = TypeVar('_T')

    # we have to forward declare the implementation, since QueryChainBase
    # is only generic in our stub and not at runtime
    class QueryChain(QueryChainBase[_T]):
        def slice(self, start: int | None, end: int | None) -> 'Self': ...
        def first(self) -> _T | None: ...
        def all(self) -> tuple[_T, ...]: ...


class QueryChain(QueryChainBase):  # type:ignore  # noqa:F811
    """ Extends SQLAlchemy Utils' QueryChain with some extra methods. """

    def slice(self, start: int | None, end: int | None) -> 'Self':
        return self[start:end]

    def first(self) -> '_T | None':
        return next((o for o in self), None)

    def all(self) -> tuple['_T', ...]:
        return tuple(self)


# TODO: This uses some sqlalchemy implementation details, so it's a little
#       fragile, so it would be good if we could accomplish the same with
#       a higher level API like sqlalchemy.inspect
def make_detached(instance: 'Base') -> None:
    """ This is kind of like make_transient and make_transient_to_detached
    without removing the instance's identity from the state, so mapped
    attributes can still be loaded again after a subsequent merge.

    """
    state = attributes.instance_state(instance)  # type:ignore[attr-defined]
    session = _state_session(state)
    if session:
        session._expunge_states([state])

    state.expired_attributes.clear()
    if state._deleted:
        del state._deleted

    state._commit_all(state.dict)
    state._expire_attributes(state.dict, state.unloaded_expirable)
