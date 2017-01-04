from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from sqlalchemy import Column, Enum, Text
from sqlalchemy_utils import observes
from uuid import uuid4


class GenericRecipient(Base, ContentMixin, TimestampMixin):
    """ A generic recipient class with polymorphic support. """

    __tablename__ = 'generic_recipients'

    #: the internal id of the recipient
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the recipient name
    name = Column(Text, nullable=False)

    #: the order of the records (set to the normalized name + medium)
    order = Column(Text, nullable=False, index=True)

    #: the medium over which notifications are sent
    medium = Column(Enum(
        'phone',
        'email',
        'http',
        name='recipient_medium'
    ), nullable=False)

    #: the phone number, e-mail, url, etc. of the recipient (matches medium)
    address = Column(Text, nullable=False)

    #: extra information associated with the address (say POST/GET for http)
    extra = Column(Text, nullable=True)

    #: the polymorphic recipient type
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'order_by': 'order'
    }

    @observes('name')
    def name_observer(self, name):
        self.order = normalize_for_url(name)
