from __future__ import annotations

from datetime import datetime
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from uuid import uuid4, UUID


class Subscriber(Base, TimestampMixin):
    """ Stores subscribers for the notifications """

    __tablename__ = 'subscribers'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    #: Identifies the subscriber
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The address of the subscriber, e.g. the phone number or the email
    #: address.
    address: Mapped[str]

    #: The locale used by the subscriber
    locale: Mapped[str]

    #: True, if the subscriber has been confirmed
    active: Mapped[bool | None]

    #: The domain of the election compound part.
    domain: Mapped[str | None]

    #: The domain segment of the election compound part.
    domain_segment: Mapped[str | None]

    #: When has this subscriber last been (explicitly) activated.
    active_since: Mapped[datetime | None]

    #: When has this subscriber last been (explicitly) deactivated.
    inactive_since: Mapped[datetime | None]


class SmsSubscriber(Subscriber):

    __mapper_args__ = {'polymorphic_identity': 'sms'}


class EmailSubscriber(Subscriber):

    __mapper_args__ = {'polymorphic_identity': 'email'}
