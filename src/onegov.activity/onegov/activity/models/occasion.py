from onegov.activity.models.activity import Activity
from onegov.core.orm import Base
from onegov.core.orm.types import UTCDateTime, UUID
from psycopg2.extras import NumericRange
from sedate import to_timezone
from sqlalchemy import Column, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.orm import relationship
from uuid import uuid4


class Occasion(Base):
    """ Describes a single occurrence of an Activity. "Occurence" would have
    been a good word for it too, but that's used by onegov.event.

    So occasion it is.

    """

    __tablename__ = 'occasions'

    #: the public id of this occasion
    id = Column(UUID, primary_key=True, default=uuid4)

    #: Timezone of the occasion
    timezone = Column(Text, nullable=False)

    #: Start date and time of the occasion
    start = Column(UTCDateTime, nullable=False)

    #: End date and time of the event (of the first event if recurring)
    end = Column(UTCDateTime, nullable=False)

    #: Describes the location of the activity
    location = Column(Text, nullable=True)

    #: The expected age of participants
    age = Column(
        INT4RANGE, nullable=False, default=NumericRange(6, 17, bounds='[]'))

    #: The expected number of participants
    spots = Column(
        INT4RANGE, nullable=False, default=NumericRange(0, 10, bounds='[]'))

    #: A note about the occurrence
    note = Column(Text, nullable=True)

    #: The activity this occasion belongs to
    activity_id = Column(UUID, ForeignKey(Activity.id), nullable=False)

    #: The bookings linked to this occasion
    bookings = relationship(
        'Booking',
        order_by='Booking.created',
        backref='occasion'
    )

    #: The state of the occasion
    state = Column(
        Enum('active', 'cancelled', name='occasion_state'),
        nullable=False,
        default='active'
    )

    @property
    def localized_start(self):
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    @property
    def localized_end(self):
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)

    def cancel(self):
        assert self.state == 'active'
        self.state == 'cancelled'
