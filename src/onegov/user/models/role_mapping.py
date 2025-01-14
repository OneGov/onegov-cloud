from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user.models.group import UserGroup
from onegov.user.models.user import User
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4, UUID as UUIDType


class RoleMapping(Base, ContentMixin, TimestampMixin):
    """ Defines a generic role mapping between user and/or group and any
    other model (content).

    The model does not define the relationship to the content. Instead, the
    realtionship should be defined in the content model when needed::

        role_mappings = relationship(
            RoleMapping,
            primaryjoin=(
                "and_("
                "foreign(RoleMapping.content_id) == cast(MyModel.id, TEXT),"
                "RoleMapping.content_type == 'my_models'"
                ")"
            ),
            viewonly=True
        )

    """

    __tablename__ = 'role_mappings'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the id of the role mapping
    id: Column[UUIDType] = Column(
        UUID,  # type:ignore[arg-type]
        nullable=False,
        primary_key=True,
        default=uuid4
    )

    #: the role is relevant for security in onegov.core
    role: Column[str] = Column(Text, nullable=False)

    #: the id of the group this mapping belongs to
    group_id: Column[UUIDType | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(UserGroup.id),
        nullable=True
    )

    #: the group this mapping belongs to
    group: relationship[UserGroup | None] = relationship(
        UserGroup,
        back_populates='role_mappings'
    )

    #: the username of the user this mapping belongs to
    username: Column[str | None] = Column(
        Text,
        ForeignKey(User.username),
        nullable=True
    )

    #: the user this mapping belongs to
    user: relationship[User | None] = relationship(
        User,
        back_populates='role_mappings'
    )

    #: the content this mapping belongs to
    content_id: Column[str] = Column(Text, nullable=False)

    #: the content type (table name) this mapping belongs to
    content_type: Column[str] = Column(Text, nullable=False)
