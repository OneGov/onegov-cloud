from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from uuid import uuid4, UUID as UUIDType


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import AppenderQuery
    from onegov.user import RoleMapping
    from onegov.user import User


group_association_table = Table(
    'user_group_associations',
    Base.metadata,
    Column(
        'user_id',
        UUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    ),
    Column(
        'group_id',
        UUID,
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
    type: Column[str] = Column(
        Text, nullable=False, default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the id of the user group
    id: Column[UUIDType] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of this group
    name: Column[str | None] = Column(Text, nullable=True)

    #: the members of this group
    users: relationship[AppenderQuery[User]] = relationship(
        'User',
        secondary=group_association_table,
        back_populates='groups',
        passive_deletes=True,
        lazy='dynamic'
    )

    #: the role mappings associated with this group
    role_mappings: relationship[AppenderQuery[RoleMapping]] = relationship(
        'RoleMapping',
        back_populates='group',
        lazy='dynamic'
    )
