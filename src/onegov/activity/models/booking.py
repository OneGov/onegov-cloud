from __future__ import annotations

from decimal import Decimal
from onegov.activity.models.occasion import Occasion
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Index
from sqlalchemy import Numeric
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, object_session, relationship, Mapped
from sqlalchemy_utils import aggregated
from uuid import uuid4, UUID


from typing import Literal, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.activity.models import Attendee, OccasionDate, BookingPeriod
    from onegov.user import User
    from sqlalchemy.sql import ColumnElement
    from typing import TypeAlias

BookingState: TypeAlias = Literal[
    'open',
    'blocked',
    'accepted',
    'denied',
    'cancelled',
]

# NOTE: Workaround to help with inference in case of tuple arguments
BookingStates: TypeAlias = (
    'tuple[BookingState, ...] | Collection[BookingState]'
)


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

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    #: the public id of the booking
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the user owning the booking
    username: Mapped[str] = mapped_column(ForeignKey('users.username'))

    #: the priority of the booking, a higher number = a higher priority
    priority: Mapped[int] = mapped_column(default=0)

    #: the group code of the booking, if missing the booking is not in a group
    group_code: Mapped[str | None]

    #: the attendee behind this booking
    attendee_id: Mapped[UUID] = mapped_column(ForeignKey('attendees.id'))

    #: the occasion this booking belongs to
    occasion_id: Mapped[UUID] = mapped_column(ForeignKey('occasions.id'))

    #: the cost of the booking
    cost: Mapped[Decimal | None] = mapped_column(Numeric(precision=8, scale=2))

    #: the calculated score of the booking
    score: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=9),
        default=lambda: Decimal('0')
    )

    #: the period this booking belongs to
    @aggregated('occasion', mapped_column(ForeignKey('periods.id')))
    def period_id(self) -> ColumnElement[UUID]:
        return func.coalesce(Occasion.period_id, None)

    #: the state of the booking
    state: Mapped[BookingState] = mapped_column(
        Enum(
            'open',
            'blocked',
            'accepted',
            'denied',
            'cancelled',
            name='booking_state'
        ),
        default='open'
    )

    __table_args__ = (
        Index(
            'one_booking_per_attendee', 'occasion_id', 'attendee_id',
            unique=True
        ),
        Index('bookings_by_state', 'state', 'username')
    )

    #: access the user linked to this booking
    user: Mapped[User] = relationship()

    #: access the attendee linked to this booking
    attendee: Mapped[Attendee] = relationship(back_populates='bookings')

    #: access the occasion linked to this booking
    occasion: Mapped[Occasion] = relationship(back_populates='bookings')

    #: access the period linked to this booking
    period: Mapped[BookingPeriod] = relationship(back_populates='bookings')

    def group_code_count(
        self,
        states: BookingStates | Literal['*'] = ('open', 'accepted')
    ) -> int:
        """ Returns the number of bookings with the same group code. """
        session = object_session(self)
        assert session is not None
        query = session.query(Booking).with_entities(
            func.count(Booking.id)
        ).filter(Booking.group_code == self.group_code)

        if states != '*':
            query = query.filter(Booking.state.in_(states))

        return query.scalar()

    def period_bound_booking_state(
        self,
        period: BookingPeriod
    ) -> BookingState:
        """ During pre-booking we don't show the actual state of the booking,
        unless the occasion was cancelled, otherwise the user might see
        accepted bookings at a point where those states are not confirmed yet.

        This methods interprets the period/state accordingly.

        """
        if period.confirmed == True:
            return self.state

        return self.state == 'cancelled' and 'cancelled' or 'open'

    def set_priority_bit(self, index: int, bit: Literal[0, 1]) -> None:
        """ Changes the priority, setting the the nth bit from the right to
        the value of ``bit`` (index/n begins at 0).

        The first bit (index=0) is reserved for starring/unstarring.
        The second bit (index=1) is reserved for nobble/unnobble.

        As a result, starring is less influental than locking.

        To give some context: Starring is used by the attendees to select
        which bookings they favor. Nobbling is used by administrators to force
        certain bookings to be preferred.

        """

        assert bit in (0, 1)
        assert index in (0, 1)

        mask = 1 << index

        self.priority &= ~mask

        if bit:
            self.priority |= mask

    def star(self, max_stars: int = 3) -> bool:
        """ Stars the current booking, up to a limit per period and attendee.

        Starring sets the star-bit to 1.

        :return: True if successful (or already set), False if over limit.

        """

        if self.starred:
            return True

        session = object_session(self)
        assert session is not None

        q = session.query(Booking.id)
        q = q.filter(Booking.attendee_id == self.attendee_id)
        q = q.filter(Booking.username == self.username)
        q = q.filter(Booking.period_id == self.period_id)
        q = q.filter(Booking.id != self.id)
        q = q.filter(Booking.starred == True)
        q = q.limit(max_stars + 1)

        if q.count() < max_stars:
            self.set_priority_bit(0, 1)
            return True

        return False

    def unstar(self) -> None:
        self.set_priority_bit(0, 0)

    def nobble(self) -> None:
        self.set_priority_bit(1, 1)

    def unnobble(self) -> None:
        self.set_priority_bit(1, 0)

    @hybrid_property
    def starred(self) -> bool:
        return self.priority & 1 << 0 != 0

    @starred.inplace.expression
    @classmethod
    def _starred_expression(cls) -> ColumnElement[bool]:
        return cls.priority.op('&')(1 << 0) != 0

    @hybrid_property
    def nobbled(self) -> bool:
        return self.priority & 1 << 1 != 0

    @nobbled.inplace.expression
    @classmethod
    def _nobbled_expression(cls) -> ColumnElement[bool]:
        return cls.priority.op('&')(1 << 1) != 0

    @property
    def dates(self) -> list[OccasionDate]:
        return self.occasion.dates

    @property
    def order(self) -> int | None:
        return self.occasion.order

    def overlaps(
        self,
        other: Self,
        with_anti_affinity_check: bool = False
    ) -> bool:
        # XXX circular import
        from onegov.activity.matching import utils

        return utils.overlaps(
            self, other,
            minutes_between=self.period.minutes_between or 0,
            alignment=self.period.alignment,  # type: ignore[arg-type]
            with_anti_affinity_check=with_anti_affinity_check,
        )
