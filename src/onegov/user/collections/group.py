from __future__ import annotations

from onegov.user.models import UserGroup
from onegov.core.collection import GenericCollection


from typing import overload, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

_G = TypeVar('_G', bound=UserGroup)


class UserGroupCollection(GenericCollection[_G]):
    """ Manages a list of user groups.

    Use it like this::

        from onegov.user import UserGroupCollection
        groups = UserGroupCollection(session)

    """

    @overload
    def __init__(
        self: UserGroupCollection[UserGroup],
        session: Session,
        type: Literal['*', 'generic'] = ...
    ): ...

    @overload
    def __init__(self, session: Session, type: str): ...

    def __init__(self, session: Session, type: str = '*'):
        self.session = session
        self.type = type

    @property
    def model_class(self) -> type[_G]:
        return UserGroup.get_polymorphic_class(  # type:ignore[return-value]
            self.type, default=UserGroup)  # type:ignore[arg-type]

    def query(self) -> Query[_G]:
        query = super().query()
        return query.order_by(self.model_class.name)
