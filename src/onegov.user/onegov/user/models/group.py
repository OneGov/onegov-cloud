from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4


class UserGroup(Base, ContentMixin, TimestampMixin):
    """ Defines a generic user group. """

    __tablename__ = 'groups'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    #: the id of the user group
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the name of this group
    name = Column(Text, nullable=True)
