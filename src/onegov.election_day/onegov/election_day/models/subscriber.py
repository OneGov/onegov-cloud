from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Text
from uuid import uuid4


class Subscriber(Base, TimestampMixin):
    """ Stores subscribers for the notifications """

    __tablename__ = 'subscribers'

    #: Identifies the subscriber
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The phone number of the subscriber
    phone_number = Column(Text, nullable=False)

    #: The locale used by the subscriber
    locale = Column(Text, nullable=False)
