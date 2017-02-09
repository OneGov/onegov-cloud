import sedate

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from psycopg2.extras import NumericRange
from sqlalchemy import Boolean
from sqlalchemy import column
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, validates
from sqlalchemy_utils import aggregated, observes
from uuid import uuid4


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

    #: The durations defined by the associated dates
    durations = Column(Integer, default=0)

    #: The default order
    order = Column(Integer, default=0)

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

    #: The dates associated with this occasion (loaded eagerly)
    dates = relationship(
        'OccasionDate',
        cascade='all,delete',
        order_by='OccasionDate.start',
        backref='occasion',
        lazy='joined',
    )

    accepted = relationship(
        'Booking',
        primaryjoin=("""and_(
            Booking.occasion_id == Occasion.id,
            Booking.state == 'accepted'
        )"""),
        viewonly=True
    )

    def on_date_change(self):
        """ Date changes are not properly propagated to the observer for
        some reason, so we do this manually with a hook.

        It's a bit of a hack, but multiple dates per occasion had to be
        added at the last minute..

        """
        self.observe_dates(self.dates)

    @observes('dates')
    def observe_dates(self, dates):
        if dates:
            self.durations = sum(set(d.duration for d in dates))
            self.order = int(min(d.start for d in dates).timestamp())
        else:
            self.durations = 0
            self.order = -1

    @validates('dates')
    def validate_dates(self, key, date):
        for o in self.dates:
            if o.id != date.id:
                assert not sedate.overlaps(
                    date.start, date.end, o.start, o.end)

        return date

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
