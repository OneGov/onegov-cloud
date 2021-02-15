from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user.models.group import UserGroup
from onegov.user.models.user import User
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class RoleMapping(Base, ContentMixin, TimestampMixin):
    """ Defines a generic role mapping between user and/or group and any
    other model (content).

    The model does not define the relationship to the content. Instead, the
    realtionship should be defined in the content model when needed:

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
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    #: the id of the role mapping
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the role is relevant for security in onegov.core
    role = Column(Text, nullable=False)

    #: the group this mapping belongs to
    group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=True)
    group = relationship(
        UserGroup, backref=backref('role_mappings', lazy='dynamic')
    )

    #: the user this mapping belongs to
    username = Column(Text, ForeignKey(User.username), nullable=True)
    user = relationship(
        User, backref=backref('role_mappings', lazy='dynamic')
    )

    #: the content this mapping belongs to
    content_id = Column(Text, nullable=False)

    #: the content type (table name) this mapping belongs to
    content_type = Column(Text, nullable=False)
