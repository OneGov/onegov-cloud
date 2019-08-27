from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4


class Subscriber(Base, TimestampMixin):
    """ Stores subscribers for the notifications """

    __tablename__ = 'subscribers'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': None
    }

    #: Identifies the subscriber
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The address of the subscriber, e.g. the phone number or the email
    #: address.
    address = Column(Text, nullable=False)

    #: The locale used by the subscriber
    locale = Column(Text, nullable=False)


class SmsSubscriber(Subscriber):

    __mapper_args__ = {'polymorphic_identity': 'sms'}


class EmailSubscriber(Subscriber):

    __mapper_args__ = {'polymorphic_identity': 'email'}
