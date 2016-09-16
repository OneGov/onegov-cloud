from onegov.core.orm import Base
from onegov.core.orm.types import UTCDateTime, UUID
from onegov.activity.models.activity import Activity
from sedate import to_timezone
from sqlalchemy import Column, Enum, Integer, Text, ForeignKey
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

    #: The date when the occasion becomes bookable
    booking_start = Column(UTCDateTime, nullable=False)

    #: Describes the location of the activity
    location = Column(Text, nullable=False)

    #: The minimal age of participants
    min_age = Column(Integer, nullable=False, default=6)

    #: The maximal age of participants
    max_age = Column(Integer, nullable=False, default=16)

    #: The number of available spots
    spots = Column(Integer, nullable=False)

    #: The activity this occasion belongs to
    activity_id = Column(UUID, ForeignKey(Activity.id))

    #: The bookings linked to this occasion
    occasions = relationship(
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
