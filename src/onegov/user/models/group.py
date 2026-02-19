from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import ContentMixin
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import UniqueConstraint
from sqlalchemy import UUID as UUIDType
from sqlalchemy.orm import mapped_column, relationship, DynamicMapped, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket import TicketPermission
    from onegov.user import RoleMapping
    from onegov.user import User


group_association_table = Table(
    'user_group_associations',
    Base.metadata,
    Column(
        'user_id',
        UUIDType(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    ),
    Column(
        'group_id',
        UUIDType(as_uuid=True),
        ForeignKey('groups.id', ondelete='CASCADE'),
        nullable=False
    ),
    UniqueConstraint(
        'user_id',
        'group_id',
        name='uq_assoc_user_group_associations'
    )
)


class UserGroup(Base, ContentMixin, TimestampMixin):
    """ Defines a generic user group. """

    __tablename__ = 'groups'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the id of the user group
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the name of this group
    name: Mapped[str | None]

    #: the members of this group
    users: DynamicMapped[User] = relationship(
        secondary=group_association_table,
        back_populates='groups',
        passive_deletes=True
    )

    #: the role mappings associated with this group
    role_mappings: DynamicMapped[RoleMapping] = relationship(
        back_populates='group'
    )

    ticket_permissions: Mapped[list[TicketPermission]] = relationship(
        cascade='all, delete-orphan',
        back_populates='user_group'
    )
