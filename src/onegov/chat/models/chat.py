from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4
# from sqlalchemy.orm import relationship


class Chat(Base, TimestampMixin):
    """ A chat. """

    __tablename__ = 'chats'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=False, default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    customer_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    messages = Column(JSONB, nullable=False, default=list)
