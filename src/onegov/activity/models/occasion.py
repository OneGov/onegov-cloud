import sedate

from datetime import datetime, timedelta
from onegov.activity.models.occasion_date import DAYS
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from psycopg2.extras import NumericRange
from sqlalchemy import Boolean
from sqlalchemy import case
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY, INT4RANGE
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.functions import coalesce
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

    #: The administrative cost of the occasion, this shadows the same column
    #: on the period. If given, it overrides that column, if left to None, it
    #: means that the period's booking cost is taken.
    #:
    #: In all-inclusive periods, this value is ignored.
    booking_cost = Column(Numeric(precision=8, scale=2), nullable=True)

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

    #: This occasion can be booked, even if the booking limit has been reached
    #: (does not currently apply to the matching, only to confirmed periods)
    exempt_from_booking_limit = Column(Boolean, nullable=False, default=False)

    #: Days on which this occasion is active
    active_days = Column(ARRAY(Integer), nullable=False, default=list)

    #: Weekdays on which this occasion is active
    weekdays = Column(ARRAY(Integer), nullable=False, default=list)

    #: Indicates if an occasion needs volunteers or not
    seeking_volunteers = Column(Boolean, nullable=False, default=False)

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

    #: The needs associated with this occasion
    needs = relationship(
        'OccasionNeed',
        cascade='all,delete',
        order_by='OccasionNeed.name',
        backref='occasion',
    )

    def on_date_change(self):
        """ Date changes are not properly propagated to the observer for
        some reason, so we do this manually with a hook.

        It's a bit of a hack, but multiple dates per occasion had to be
        added at the last minute..

        """
        self.observe_dates(self.dates)

    @property
    def anti_affinity_group(self):
        """ Uses the activity_id/period_id as an anti-affinity group to ensure
        that an attendee is never given two occasions of the same activity
        in a single period.

        If that is wanted, the attendee is meant to do this after the
        matching has been done, with a direct booking.

        """

        return (self.activity_id.hex, self.period_id.hex)

    @hybrid_property
    def total_cost(self):
        """ Calculates the cost of booking a single occasion, including all
        costs only relevant to this occasion (i.e. excluding the all-inclusive
        subscription cost).

        """

        base = self.cost or 0

        if self.period.all_inclusive:
            return base

        if self.booking_cost:
            return base + self.booking_cost

        if self.period.booking_cost:
            return base + self.period.booking_cost

        return base

    @total_cost.expression
    def total_cost(self):
        from onegov.activity.models.period import Period

        return coalesce(Occasion.cost, 0) + case([
            (Period.all_inclusive == True, 0),
            (Period.all_inclusive == False, func.coalesce(
                Occasion.booking_cost, Period.booking_cost, 0
            )),
        ])

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

    @observes('needs')
    def observe_needs(self, needs):
        for need in (needs or ()):
            if need.accept_signups:
                self.seeking_volunteers = True
                break
        else:
            self.seeking_volunteers = False

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

    def is_past_deadline(self, now):
        return now > self.period.as_local_datetime(self.deadline)

    def is_past_cancellation(self, date):
        cancellation = self.cancellation_deadline
        return cancellation is None or date > cancellation

    @property
    def deadline(self):
        """ The date until which this occasion may be booked (inclusive). """
        period = self.period

        if period.deadline_days is None:
            if isinstance(self.period.booking_end, datetime):
                return self.period.booking_end.date()

            return self.period.booking_end

        min_date = min(d.start for d in self.dates)
        return (min_date - timedelta(days=period.deadline_days + 1)).date()

    @property
    def cancellation_deadline(self):
        """ The date until which bookings of this occasion may be cancelled
        by a mere member (inclusive).

        If mere members are not allowed to do that, the deadline returns None.

        """
        period = self.period

        if period.cancellation_date is not None:
            return period.cancellation_date

        if period.cancellation_days is None:
            return None

        min_date = min(d.start for d in self.dates)
        return (min_date - timedelta(days=period.cancellation_days + 1)).date()

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

    def is_too_young(self, birth_date):
        return self.period.age_barrier.is_too_young(
            birth_date=birth_date,
            start_date=self.dates[0].start.date(),
            min_age=self.age.lower)

    def is_too_old(self, birth_date):
        return self.period.age_barrier.is_too_old(
            birth_date=birth_date,
            start_date=self.dates[0].start.date(),
            max_age=self.age.upper - 1)
