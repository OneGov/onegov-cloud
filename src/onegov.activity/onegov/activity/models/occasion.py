import sedate

from datetime import timedelta
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.activity.models.occasion_date import DAYS
from psycopg2.extras import NumericRange
from sqlalchemy import Boolean
from sqlalchemy import case
from sqlalchemy import column
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY, INT4RANGE
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

    #: Describes the meeting point of the occasion
    meeting_point = Column(Text, nullable=True)

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

    #: The duration defined by the associated dates
    duration = Column(Integer, default=0)

    #: The default order
    order = Column(Integer, default=0)

    #: Pretend like this occasion doesn't use any time
    exclude_from_overlap_check = Column(Boolean, nullable=False, default=False)

    #: Days on which this occasion is active
    active_days = Column(ARRAY(Integer), nullable=False, default=list)

    #: Weekdays on which this occasion is active
    weekdays = Column(ARRAY(Integer), nullable=False, default=list)

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

    def compute_duration(self, dates):
        if not dates:
            return 0

        if len(dates) <= 1:
            return int(next(iter(dates)).duration)

        first = min((d for d in dates), key=lambda d: d.start)
        last = max((d for d in dates), key=lambda d: d.end)

        return int(DAYS.compute(
            first.localized_start,
            last.localized_end,
            (last.end - first.start).total_seconds()
        ))

    def compute_order(self, dates):
        if not dates:
            return -1

        return int(min(d.start for d in dates).timestamp())

    def compute_active_days(self, dates):
        return [day for date in (dates or ()) for day in date.active_days]

    def compute_weekdays(self, dates):
        return list({day for date in (dates or ()) for day in date.weekdays})

    @observes('dates')
    def observe_dates(self, dates):
        self.duration = self.compute_duration(dates)
        self.order = self.compute_order(dates)
        self.weekdays = self.compute_weekdays(dates)
        self.active_days = self.compute_active_days(dates)

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
        if self.cancelled:
            return 0
        return self.spots.upper - 1 - self.attendee_count

    @available_spots.expression
    def available_spots(cls):
        return case((
            (
                cls.cancelled == False,
                func.upper(cls.spots) - 1 - cls.attendee_count
            ),
        ), else_=0)

    @property
    def max_spots(self):
        return self.spots.upper - 1

    def is_past_deadline(self, date):
        return date > self.deadline

    @property
    def deadline(self):
        """ The date until which this occasion may be booked (inclusive). """
        period = self.period

        if period.deadline_date is not None:
            return period.deadline_date

        min_date = min(d.start for d in self.dates)

        if period.deadline_days is not None:
            return (min_date - timedelta(days=period.deadline_days + 1)).date()

        return min_date.date()

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

    def is_permitted_birth_date(self, birth_date, wiggle_room=365):
        """ Returns true if the given birth date is considered to be in
        the age range of this occasion.

        The date inspected is the date of the first occurrence. In addition
        there's a wiggle room of x days which is applied to the exact age.

        By default attendees may be one year too young or too old.

        """

        if self.is_too_young(birth_date, wiggle_room):
            return False

        if self.is_too_old(birth_date, wiggle_room):
            return False

        return True

    def is_too_old(self, birth_date, wiggle_room=365):
        age = (self.dates[0].start.date() - birth_date).days
        max_age = (self.age.upper - 1) * 365.25 + wiggle_room

        return age > max_age

    def is_too_young(self, birth_date, wiggle_room=365):
        age = (self.dates[0].start.date() - birth_date).days
        min_age = self.age.lower * 365.25 - wiggle_room

        return age < min_age
