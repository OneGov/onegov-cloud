from enum import IntEnum
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime, UUID
from psycopg2.extras import NumericRange
from sedate import to_timezone
from sqlalchemy import Boolean
from sqlalchemy import case
from sqlalchemy import CheckConstraint
from sqlalchemy import column
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session
from sqlalchemy_utils import aggregated
from uuid import uuid4


class DAYS(IntEnum):
    half = 2**1
    full = 2**2
    many = 2**3

    @staticmethod
    def has(value, mask):
        return value & mask > 0 if value else False


class Occasion(Base, TimestampMixin):
    """ Describes a single occurrence of an Activity. "Occurence" would have
    been a good word for it too, but that's used by onegov.event.

    So occasion it is.

    """

    __tablename__ = 'occasions'

    def __hash__(self):
        return hash(self.id)

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

    #: The cost of the occasion (max value is 100'000.00), the currency is
    #: assumed to be CHF as this system will probably never be used outside
    #: Switzerland
    cost = Column(Numeric(precision=8, scale=2), nullable=True)

    #: The activity this occasion belongs to
    activity_id = Column(
        UUID, ForeignKey("activities.id", use_alter=True), nullable=False)

    #: The period this occasion belongs to
    period_id = Column(
        UUID, ForeignKey("periods.id", use_alter=True), nullable=False)

    #: True if the occasion has been cancelled
    cancelled = Column(Boolean, nullable=False, default=False)

    @aggregated('period', Column(Boolean, default=False))
    def active(self):
        return column('active')

    @aggregated('accepted', Column(Integer, default=0))
    def attendee_count(self):
        return func.count('1')

    #: The bookings linked to this occasion
    bookings = relationship(
        'Booking',
        order_by='Booking.created',
        backref='occasion'
    )

    accepted = relationship(
        'Booking',
        primaryjoin=("""and_(
            Booking.occasion_id == Occasion.id,
            Booking.state == 'accepted'
        )"""),
        viewonly=True)

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
    def operable(self):
        return self.attendee_count >= self.spots.lower

    @hybrid_property
    def full(self):
        return self.attendee_count == self.spots.upper - 1

    @hybrid_property
    def available_spots(self):
        return self.spots.upper - 1 - self.attendee_count

    @property
    def max_spots(self):
        return self.spots.upper - 1

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
        from onegov.activity.collections import BookingCollection

        assert not self.cancelled
        period = self.period

        if not period.confirmed:
            def cancel(booking):
                booking.state = 'cancelled'
        else:
            bookings = BookingCollection(object_session(self))
            scoring = period.scoring

            def cancel(booking):
                bookings.cancel_booking(booking, scoring)

        for booking in self.bookings:
            assert booking.period_id == period.id
            cancel(booking)

        self.cancelled = True
