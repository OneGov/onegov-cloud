from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import User
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4


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
    user_id = Column(UUID, ForeignKey('users.id'), nullable=True)
    user = relationship(User)

    customer_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    topic = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    chat_history = Column(JSONB, nullable=False, default=list)
