from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime


class Subscriber(Base, TimestampMixin):
    """ Stores subscribers for the notifications """

    __tablename__ = 'subscribers'

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
        'polymorphic_identity': 'generic'
    }

    #: Identifies the subscriber
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The address of the subscriber, e.g. the phone number or the email
    #: address.
    address: Column[str] = Column(Text, nullable=False)

    #: The locale used by the subscriber
    locale: Column[str] = Column(Text, nullable=False)

    #: True, if the subscriber has been confirmed
    active: Column[bool | None] = Column(Boolean, nullable=True)

    #: The domain of the election compound part.
    domain: Column[str | None] = Column(Text, nullable=True)

    #: The domain segment of the election compound part.
    domain_segment: Column[str | None] = Column(Text, nullable=True)

    #: When has this subscriber last been (explicitly) activated.
    active_since: Column[datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )

    #: When has this subscriber last been (explicitly) deactivated.
    inactive_since: Column[datetime | None] = Column(
        UTCDateTime,
        nullable=True
    )


class SmsSubscriber(Subscriber):

    __mapper_args__ = {'polymorphic_identity': 'sms'}


class EmailSubscriber(Subscriber):

    __mapper_args__ = {'polymorphic_identity': 'email'}
