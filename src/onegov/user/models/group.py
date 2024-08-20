from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4, UUID as UUIDType


from typing_extensions import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import AppenderQuery
    from onegov.user import RoleMapping
    from onegov.user import User


class UserGroup(Base, ContentMixin, TimestampMixin):
    """ Defines a generic user group. """

    __tablename__ = 'groups'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: 'Column[str]' = Column(
        Text, nullable=False, default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the id of the user group
    id: 'Column[UUIDType]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of this group
    name: 'Column[str | None]' = Column(Text, nullable=True)

    #: the members of this group
    users: 'relationship[AppenderQuery[User]]' = relationship(
        'User',
        back_populates='group',
        lazy='dynamic'
    )

    #: the role mappings associated with this group
    role_mappings: 'relationship[AppenderQuery[RoleMapping]]' = relationship(
        'RoleMapping',
        back_populates='group',
        lazy='dynamic'
    )
