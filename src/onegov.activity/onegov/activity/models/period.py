import sedate

from datetime import date, datetime
from onegov.activity.models.booking import Booking
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID, JSON
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import column
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.orm import object_session, relationship, joinedload, defer
from uuid import uuid4


class Period(Base, TimestampMixin):

    __tablename__ = 'periods'

    # It's doubtful that the Ferienpass would ever run anywhere else but
    # in Switzerland ;)
    timezone = 'Europe/Zurich'

    #: The public id of this period
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The public title of this period
    title = Column(Text, nullable=False)

    #: Only one period is active at a time
    active = Column(Boolean, nullable=False, default=False)

    #: A confirmed period may not be automatically matched anymore and all
    #: booking changes to it are communicted to the customer
    confirmed = Column(Boolean, nullable=False, default=False)

    #: A finalized period may not have any change in bookings anymore
    finalized = Column(Boolean, nullable=False, default=False)

    #: Start of the wishlist-phase
    prebooking_start = Column(Date, nullable=False)

    #: End of the wishlist-phase
    prebooking_end = Column(Date, nullable=False)

    #: Date of the earliest possible occasion start of this period
    execution_start = Column(Date, nullable=False)

    #: Date of the latest possible occasion end of this period
    execution_end = Column(Date, nullable=False)

    #: Extra data stored on the period
    data = Column(JSON, nullable=False, default=dict)

    #: Maximum number of bookings per attendee
    max_bookings_per_attendee = Column(Integer, nullable=True)

    #: Base cost for one or many bookings
    booking_cost = Column(Numeric(precision=8, scale=2), nullable=True)

    #: True if the booking cost is meant for all bookings in a period
    #: or for each single booking
    all_inclusive = Column(Boolean, nullable=False, default=False)

    #: Time between bookings in minutes
    minutes_between = Column(Integer, nullable=True, default=0)

    #: Date after which no bookings are possible anymore
    deadline_date = Column(Date, nullable=True)

    #: Days between the occasion and the deadline (an alternative to
    #: the deadline_date)
    deadline_days = Column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint((
            '"prebooking_start" <= "prebooking_end" AND '
            '"prebooking_end" <= "execution_start" AND '
            '"execution_start" <= "execution_end"'
        ), name='period_date_order'),
        Index(
            'only_one_active_period', 'active',
            unique=True, postgresql_where=column('active') == True
        )
    )

    #: The occasions linked to this period
    occasions = relationship(
        'Occasion',
        order_by='Occasion.order',
        backref='period'
    )

    #: The bookings linked to this period
    bookings = relationship(
        'Booking',
        backref='period'
    )

    def activate(self):
        """ Activates the current period, causing all occasions and activites
        to update their status and book-keeping.

        It also makes sure no other period is active.

        """
        if self.active:
            return

        session = object_session(self)
        model = self.__class__

        active_period = session.query(model)\
            .filter(model.active == True).first()

        if active_period:
            active_period.deactivate()

        # avoid triggering the only_one_active_period index constraint
        session.flush()

        self.active = True

    def deactivate(self):
        """ Deactivates the current period, causing all occasions and activites
        to update their status and book-keeping.

        """

        if not self.active:
            return

        self.active = False

    def confirm(self):
        """ Confirms the current period. """

        self.confirmed = True

        # open bookings are marked as denied during completion
        # and the booking costs are copied over permanently (so they can't
        # change anymore)
        b = object_session(self).query(Booking)
        b = b.filter(Booking.period_id == self.id)
        b = b.options(joinedload(Booking.occasion))
        b = b.options(
            defer(Booking.group_code),
            defer(Booking.attendee_id),
            defer(Booking.priority),
            defer(Booking.username),
        )

        for booking in b:
            if booking.state == 'open':
                booking.state = 'denied'

            booking.cost = booking.provisional_booking_cost(period=self)

    @property
    def booking_limit(self):
        """ Returns the max_bookings_per_attendee limit if it applies. """
        return self.all_inclusive and self.max_bookings_per_attendee

    def as_local_datetime(self, day):
        return sedate.standardize_date(
            datetime(day.year, day.month, day.day, 0, 0),
            self.timezone
        )

    @property
    def phase(self):
        local = self.as_local_datetime
        today = local(date.today())

        if not self.active or today < local(self.prebooking_start):
            return 'inactive'

        if not self.confirmed:
            return 'wishlist'

        if not self.finalized:
            return 'booking'

        if today < local(self.execution_start):
            return 'payment'

        if local(self.execution_start) <= today <= local(self.execution_end):
            return 'execution'

        if today > local(self.execution_end):
            return 'archive'

    @property
    def wishlist_phase(self):
        return self.phase == 'wishlist'

    @property
    def booking_phase(self):
        return self.phase == 'booking'

    @property
    def payment_phase(self):
        return self.phase == 'payment'

    @property
    def execution_phase(self):
        return self.phase == 'execution'

    @property
    def archive_phase(self):
        return self.phase == 'archive'

    @property
    def is_prebooking_in_future(self):
        today = self.as_local_datetime(date.today())
        start = self.as_local_datetime(self.prebooking_start)

        return today < start

    @property
    def is_currently_prebooking(self):
        if not self.wishlist_phase:
            return False

        today = self.as_local_datetime(date.today())
        start = self.as_local_datetime(self.prebooking_start)
        end = self.as_local_datetime(self.prebooking_end)

        return start <= today <= end

    @property
    def is_prebooking_in_past(self):
        today = self.as_local_datetime(date.today())
        start = self.as_local_datetime(self.prebooking_start)
        end = self.as_local_datetime(self.prebooking_end)

        if today > end:
            return True

        return start <= today and not self.wishlist_phase

    @property
    def scoring(self):
        # circular import
        from onegov.activity.matching.score import Scoring

        return Scoring.from_settings(
            settings=self.data.get('match-settings', {}),
            session=object_session(self))

    @scoring.setter
    def scoring(self, scoring):
        self.data['match-settings'] = scoring.settings
