from __future__ import annotations

from onegov.core.orm import observes, Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import UserGroup
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Text
from sqlalchemy.orm import backref, object_session, relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid


class TicketPermission(Base, TimestampMixin):
    """ Defines a custom ticket permission.

    If a ticket permission is defined for ticket handler (and optionally a
    group), a user has to be in the given user group to access these tickets.

    """

    __tablename__ = 'ticket_permissions'

    #: the id
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the user group needed for accessing the tickets
    user_group_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(UserGroup.id),
        nullable=False
    )
    user_group: relationship[UserGroup] = relationship(
        UserGroup,
        backref=backref(
            'ticket_permissions',
            cascade='all, delete-orphan',
        )
    )

    #: the handler code this permission addresses
    handler_code: Column[str] = Column(Text, nullable=False)

    #: the group this permission addresses
    group: Column[str | None] = Column(Text, nullable=True)

    #: whether or not this permission is exclusive
    #: if a permission is exclusive, the same permission may not
    #: be given non-exclusively to another group, but multiple groups
    #: may have the same exclusive or non-exclusive permission
    exclusive: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    #: whether or not to immediately send notifications about new tickets
    immediate_notification: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )

    __table_args__ = (
        CheckConstraint(
            exclusive.isnot_distinct_from(True)
            | immediate_notification.isnot_distinct_from(True),
            name='no_redundant_ticket_permissions'
        ),
    )

    # NOTE: A unique constraint doesn't work here, since group is nullable
    @observes('handler_code', 'group')
    def ensure_uniqueness(
        self,
        handler_code: str,
        group: str | None
    ) -> None:

        # this should always be set
        assert self.handler_code
        if not (user_group_id := (
            self.user_group_id
            or (self.user_group and self.user_group.id)
        )):
            # this is an incomplete record that should fail in
            # a different way
            return

        session = object_session(self)
        query = session.query(TicketPermission)

        # we can't conflict with ourselves, only with other permissions
        if self.id is not None:
            query = query.filter(
                TicketPermission.id != self.id
            )

        # this defines whether or not two permissions target the same tickets
        query = query.filter(
            TicketPermission.handler_code == self.handler_code
        )
        query = query.filter(
            TicketPermission.group.isnot_distinct_from(self.group)
        )

        # the exact same permission may only exist once per user group
        constraint_violated = query.filter(
            TicketPermission.user_group_id == user_group_id
        ).exists()

        if session.query(constraint_violated).scalar():
            raise ValueError('Uniqueness violation in ticket permissions')
