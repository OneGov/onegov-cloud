from __future__ import annotations

from onegov.activity import Activity, Occasion
from onegov.feriennet.const import VISIBLE_ACTIVITY_STATES
from morepath.authentication import NO_IDENTITY
from sqlalchemy import and_, or_


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity, NoIdentity
    from sqlalchemy.orm import Query
    from typing import TypeVar
    from typing import Self

    T = TypeVar('T')


class ActivityQueryPolicy:
    """ Limits activity queries depending on the current user. """

    def __init__(self, username: str | None, role: str | None) -> None:
        self.username = username
        self.role = role

    @classmethod
    def for_identity(cls, identity: Identity | NoIdentity | None) -> Self:
        if identity is None or identity is NO_IDENTITY:
            return cls(None, None)
        else:
            assert hasattr(identity, 'role')
            return cls(identity.userid, identity.role)

    def granted_subset(self, query: Query[T]) -> Query[T]:
        """ Limits the given activites query for the given user. """

        if self.username is None or self.role not in ('admin', 'editor'):
            return self.public_subset(query)
        else:
            return self.private_subset(query)

    def public_subset(self, query: Query[T]) -> Query[T]:
        """ Limits the given query to activites meant for the public. """
        return query.filter(and_(
            Activity.state.in_(VISIBLE_ACTIVITY_STATES['anonymous']),

            # excludes activites without any occasion
            query.session.query(Occasion.activity_id).filter(
                Occasion.activity_id == Activity.id
            ).exists()
        ))

    def private_subset(self, query: Query[T]) -> Query[T]:
        """ Limits the given query to activites meant for admins/owners.

        Admins see all the states and owners see the states of their own.
        """

        assert self.role and self.username

        return query.filter(or_(
            Activity.state.in_(VISIBLE_ACTIVITY_STATES[self.role]),
            Activity.username == self.username
        ))
