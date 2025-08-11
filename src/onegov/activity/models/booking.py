from __future__ import annotations

from onegov.activity.models.occasion import Occasion
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
from sqlalchemy.orm import object_session, relationship
from sqlalchemy_utils import aggregated
from uuid import uuid4


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Collection
    from decimal import Decimal
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
        tuple[BookingState, ...] | Collection[BookingState]
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
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the user owning the booking
    username: Column[str] = Column(
        Text,
        ForeignKey('users.username'),
        nullable=False
    )

    #: the priority of the booking, a higher number = a higher priority
    priority: Column[int] = Column(Integer, nullable=False, default=0)

    #: the group code of the booking, if missing the booking is not in a group
    group_code: Column[str | None] = Column(Text, nullable=True)

    #: the attendee behind this booking
    attendee_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('attendees.id'),
        nullable=False
    )

    #: the occasion this booking belongs to
    occasion_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('occasions.id'),
        nullable=False
    )

    #: the cost of the booking
    cost: Column[Decimal | None] = Column(
        Numeric(precision=8, scale=2),
        nullable=True
    )

    #: the calculated score of the booking
    score: Column[Decimal] = Column(
        Numeric(precision=14, scale=9),
        nullable=False,
        default=0
    )

    if TYPE_CHECKING:
        # FIXME: We should be able to get rid of this workaround in the future
        period_id: Column[uuid.UUID]

    #: the period this booking belongs to
    @aggregated('occasion', Column(  # type:ignore[no-redef]
        UUID, ForeignKey('periods.id'), nullable=False)
    )
    def period_id(self) -> ColumnElement[uuid.UUID]:
        return func.coalesce(Occasion.period_id, None)

    #: the state of the booking
    state: Column[BookingState] = Column(
        Enum(  # type:ignore[arg-type]
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

    __table_args__ = (
        Index(
            'one_booking_per_attendee', 'occasion_id', 'attendee_id',
            unique=True
        ),
        Index('bookings_by_state', 'state', 'username')
    )

    #: access the user linked to this booking
    user: relationship[User] = relationship('User')

    #: access the attendee linked to this booking
    attendee: relationship[Attendee] = relationship(
        'Attendee',
        back_populates='bookings'
    )

    #: access the occasion linked to this booking
    occasion: relationship[Occasion] = relationship(
        Occasion,
        back_populates='bookings'
    )

    #: access the period linked to this booking
    period: relationship[BookingPeriod] = relationship(
        'BookingPeriod',
        back_populates='bookings'
    )

    def group_code_count(
        self,
        states: BookingStates | Literal['*'] = ('open', 'accepted')
    ) -> int:
        """ Returns the number of bookings with the same group code. """
        query = object_session(self).query(Booking).with_entities(
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

    if TYPE_CHECKING:
        starred: Column[bool]
        nobbled: Column[bool]

    @hybrid_property  # type:ignore[no-redef]
    def starred(self) -> bool:
        return self.priority & 1 << 0 != 0

    @starred.expression  # type:ignore[no-redef]
    def starred(cls) -> ColumnElement[bool]:
        return cls.priority.op('&')(1 << 0) != 0

    @hybrid_property  # type:ignore[no-redef]
    def nobbled(self) -> bool:
        return self.priority & 1 << 1 != 0

    @nobbled.expression  # type:ignore[no-redef]
    def nobbled(cls) -> ColumnElement[bool]:
        return cls.priority.op('&')(1 << 1) != 0

    @property
    def dates(self) -> list[OccasionDate]:
        return self.occasion.dates

    @property
    def order(self) -> int | None:
        return self.occasion.order

    def overlaps(
        self,
        other: Booking,
        with_anti_affinity_check: bool = False
    ) -> bool:
        # XXX circular import
        from onegov.activity.matching import utils

        return utils.overlaps(
            self, other,
            minutes_between=self.period.minutes_between or 0,
            alignment=self.period.alignment,  # type:ignore[arg-type]
            with_anti_affinity_check=with_anti_affinity_check,
        )
