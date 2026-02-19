from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.user.models.group import UserGroup
from onegov.user.models.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4, UUID


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
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the id of the role mapping
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the role is relevant for security in onegov.core
    role: Mapped[str]

    #: the id of the group this mapping belongs to
    group_id: Mapped[UUID | None] = mapped_column(ForeignKey(UserGroup.id))

    #: the group this mapping belongs to
    group: Mapped[UserGroup | None] = relationship(
        back_populates='role_mappings'
    )

    #: the username of the user this mapping belongs to
    username: Mapped[str | None] = mapped_column(ForeignKey(User.username))

    #: the user this mapping belongs to
    user: Mapped[User | None] = relationship(back_populates='role_mappings')

    #: the content this mapping belongs to
    content_id: Mapped[str]

    #: the content type (table name) this mapping belongs to
    content_type: Mapped[str]
