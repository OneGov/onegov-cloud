from onegov.activity.models.occasion import Occasion
from onegov.activity.utils import random_group_code, dates_overlap
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session
from sqlalchemy_utils import aggregated
from uuid import uuid4


class Booking(Base, TimestampMixin):
    """ Bookings are created by users for occasions.

    Initially, bookings are open. In this state they represent a "wish" rather
    than booking.

    Because bookings are wishes initially, they get a priority as well as
    a group code which links multiple bookings by multiple users together.

    They system will try to figure out the best booking using the priority
    as well as the group code.

    """

    __tablename__ = 'bookings'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    #: the public id of the booking
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user owning the booking
    username = Column(Text, ForeignKey('users.username'), nullable=False)

    #: the priority of the booking, a higher number = a higher priority
    priority = Column(Integer, nullable=False, default=0)

    #: the group code of the booking
    group_code = Column(Text, nullable=False, default=random_group_code)

    #: the attendee behind this booking
    attendee_id = Column(UUID, ForeignKey("attendees.id"), nullable=False)

    #: the occasion this booking belongs to
    occasion_id = Column(UUID, ForeignKey("occasions.id"), nullable=False)

    #: the cost of the booking
    cost = Column(Numeric(precision=8, scale=2), nullable=True)

    #: the period this booking belongs to
    @aggregated('occasion', Column(
        UUID, ForeignKey("periods.id"), nullable=False)
    )
    def period_id(self):
        return func.coalesce(Occasion.period_id, None)

    #: the state of the booking
    state = Column(
        Enum(
            'open',
            'blocked',
            'accepted',
            'denied',
            'cancelled',
            name='booking_state'
        ),
        nullable=False,
        default='open'
    )

    __mapper_args__ = {
        'order_by': priority
    }

    __table_args__ = (
        Index(
            'one_booking_per_attendee', 'occasion_id', 'attendee_id',
            unique=True
        ),
        Index('bookings_by_state', 'state', 'username')
    )

    @hybrid_property
    def starred(self):
        return self.priority != 0

    def provisional_booking_cost(self, period=None):
        """ The costs of the final booking, including the booking costs
        of the period (if not all-inclusive).

        This cost is written to the booking.cost when the period is
        confirmed.

        """

        period = period or self.period
        cost = self.occasion.cost or 0

        if not period.all_inclusive and period.booking_cost:
            cost += period.booking_cost

        return cost or 0

    def star(self, max_stars=3):
        """ Stars the current booking (giving it a priority of 1), up to
        a limit per period and attendee.

        :return: True if successful (or already set), False if over limit.

        """

        if self.starred:
            return True

        session = object_session(self)

        q = session.query(Booking.id)
        q = q.filter(Booking.attendee_id == self.attendee_id)
        q = q.filter(Booking.username == self.username)
        q = q.filter(Booking.period_id == self.period_id)
        q = q.filter(Booking.id != self.id)
        q = q.filter(Booking.priority != 0)
        q = q.limit(4)

        if q.count() < max_stars:
            self.priority = 1
            return True

        return False

    def unstar(self):
        self.priority = 0

    @property
    def dates(self):
        return self.occasion.dates

    @property
    def order(self):
        return self.occasion.order

    def overlaps(self, other):

        # even if exclude_from_overlap_check is active we consider a booking
        # to overlap itself (this protects against double bookings)
        if self.id == other.id:
            return True

        if self.occasion.exclude_from_overlap_check:
            return False

        # in some places 'other' only contains a start/end, so we can't
        # check for the overlap exclusion (those places are supposed to
        # do this on their own)
        if hasattr(other, 'occasion'):
            if other.occasion.exclude_from_overlap_check:
                return False

        return dates_overlap(
            tuple((d.start, d.end) for d in self.dates),
            tuple((o.start, o.end) for o in other.dates),
            minutes_between=self.period.minutes_between
        )
