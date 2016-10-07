from enum import IntEnum
from onegov.core.orm import Base
from onegov.core.orm.types import UTCDateTime, UUID
from psycopg2.extras import NumericRange
from sedate import to_timezone
from sqlalchemy import Column, Enum, Text, ForeignKey, CheckConstraint
from sqlalchemy import case, func
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4


class DAYS(IntEnum):
    half = 2**1
    full = 2**2
    many = 2**3

    @staticmethod
    def has(value, mask):
        return value & mask > 0 if value else False


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
    activity_id = Column(
        UUID, ForeignKey("activities.id", use_alter=True), nullable=False)

    #: The bookings linked to this occasion
    bookings = relationship(
        'Booking',
        order_by='Booking.created',
        backref='occasion'
    )

    #: The state of the occasion
    state = Column(
        Enum('active', 'cancelled', 'archived', name='occasion_state'),
        nullable=False,
        default='active'
    )

    __table_args__ = (
        CheckConstraint('"start" <= "end"', name='start_before_end'),
    )

    @property
    def localized_start(self):
        """ The localized version of the start date/time. """

        return to_timezone(self.start, self.timezone)

    @property
    def localized_end(self):
        """ The localized version of the end date/time. """

        return to_timezone(self.end, self.timezone)

    @hybrid_property
    def duration(self):
        hours = self.duration_in_seconds / 3600

        # defined here and in the expression below!
        if hours <= 6:
            return DAYS.half
        elif hours <= 24:
            return DAYS.full
        else:
            return DAYS.many

    @duration.expression
    def duration(self):

        # defined here and in the property above!
        return case((
            (Occasion.duration_in_seconds <= (6 * 3600), int(DAYS.half)),
            (Occasion.duration_in_seconds <= (24 * 3600), int(DAYS.full)),
        ), else_=int(DAYS.many))

    @hybrid_property
    def duration_in_seconds(self):
        return (self.end - self.start).total_seconds()

    @duration_in_seconds.expression
    def duration_in_seconds(self):
        return func.extract('epoch', self.end - self.start)

    def cancel(self):
        assert self.state in ('active', 'cancelled')
        self.state == 'cancelled'

    def archive(self):
        assert self.state in ('active', 'cancelled', 'archived')
        self.state == 'archived'
