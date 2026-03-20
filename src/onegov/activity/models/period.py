from __future__ import annotations

import sedate

from datetime import date, datetime
from decimal import Decimal
from onegov.activity.models.age_barrier import AgeBarrier
from onegov.activity.models.booking import Booking
from onegov.activity.models.occasion import Occasion
from onegov.core.custom import msgpack
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import desc, not_, distinct
from sqlalchemy import CheckConstraint
from sqlalchemy import column
from sqlalchemy import Index
from sqlalchemy import Numeric
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.orm import defer, joinedload, object_session, validates
from uuid import uuid4, UUID


from typing import Any, ClassVar, NamedTuple, NoReturn, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.matching.score import Scoring
    from onegov.activity.models import BookingPeriodInvoice, PublicationRequest
    from sqlalchemy.orm import Session


class BookingPeriodMixin:

    # It's doubtful that the Ferienpass would ever run anywhere else but
    # in Switzerland ;)
    timezone: ClassVar[str] = 'Europe/Zurich'

    if TYPE_CHECKING:
        # forward declare required attributes
        @property
        def active(self) -> Mapped[bool] | bool: ...
        @property
        def confirmed(self) -> Mapped[bool] | bool: ...
        @property
        def finalized(self) -> Mapped[bool] | bool: ...
        @property
        def prebooking_start(self) -> Mapped[date] | date: ...
        @property
        def prebooking_end(self) -> Mapped[date] | date: ...
        @property
        def booking_start(self) -> Mapped[date] | date: ...
        @property
        def booking_end(self) -> Mapped[date] | date: ...
        @property
        def execution_start(self) -> Mapped[date] | date: ...
        @property
        def execution_end(self) -> Mapped[date] | date: ...
        @property
        def book_finalized(self) -> Mapped[bool] | bool: ...
        @property
        def max_bookings_per_attendee(
            self
        ) -> Mapped[int | None] | int | None: ...

    def as_local_datetime(
        self,
        day: date | datetime,
        end_of_day: bool = False
    ) -> datetime:
        """ Returns the moment of midnight in terms of the timezone it UTC """
        return sedate.standardize_date(
            datetime(
                day.year,
                day.month,
                day.day,
                23 if end_of_day else 0,
                59 if end_of_day else 0,
                59 if end_of_day else 0
            ),
            self.timezone
        )

    @property
    def phase(self) -> str | None:
        local = self.as_local_datetime
        now = sedate.utcnow()

        if not self.active or now < local(self.prebooking_start):
            return 'inactive'

        if not self.confirmed:
            return 'wishlist'

        if now < local(self.booking_start):
            return 'inactive'

        if not self.finalized and local(self.booking_end, True) < now:
            return 'inactive'

        if not self.finalized:
            return 'booking'

        local_execution_start = local(self.execution_start)
        if now < local_execution_start:
            return 'payment'

        local_execution_end = local(self.execution_end, end_of_day=True)
        if local_execution_start <= now <= local_execution_end:
            return 'execution'

        if now > local_execution_end:
            return 'archive'

        # FIXME: Is this allowed?
        return None

    @property
    def wishlist_phase(self) -> bool:
        return self.phase == 'wishlist'

    @property
    def booking_phase(self) -> bool:
        return self.phase == 'booking'

    @property
    def payment_phase(self) -> bool:
        return self.phase == 'payment'

    @property
    def execution_phase(self) -> bool:
        return self.phase == 'execution'

    @property
    def archive_phase(self) -> bool:
        return self.phase == 'archive'

    @property
    def is_prebooking_in_future(self) -> bool:
        now = sedate.utcnow()
        start = self.as_local_datetime(self.prebooking_start)

        return now < start

    @property
    def is_currently_prebooking(self) -> bool:
        if not self.wishlist_phase:
            return False

        now = sedate.utcnow()
        start = self.as_local_datetime(self.prebooking_start)
        end = self.as_local_datetime(self.prebooking_end, end_of_day=True)

        return start <= now <= end

    @property
    def is_prebooking_in_past(self) -> bool:
        """Returns true if current date is after start of booking phase or if
        current date is after prebooking end. """
        now = sedate.utcnow()
        start = self.as_local_datetime(self.prebooking_start)
        end = self.as_local_datetime(self.prebooking_end, end_of_day=True)

        if now > end:
            return True

        return start <= now and not self.wishlist_phase

    @property
    def is_booking_in_future(self) -> bool:
        now = sedate.utcnow()
        start = self.as_local_datetime(self.booking_start)

        return now < start

    @property
    def is_currently_booking(self) -> bool:
        if not self.booking_phase:
            return False

        now = sedate.utcnow()
        start = self.as_local_datetime(self.booking_start)
        end = self.as_local_datetime(self.booking_end, end_of_day=True)

        return start <= now <= end

    @property
    def is_booking_in_past(self) -> bool:
        now = sedate.utcnow()
        start = self.as_local_datetime(self.booking_start)
        end = self.as_local_datetime(self.booking_end, end_of_day=True)

        if now > end:
            return True

        return start <= now and not (
            self.booking_phase
            or self.book_finalized)

    @property
    def is_execution_in_past(self) -> bool:
        now = sedate.utcnow()
        end = self.as_local_datetime(self.execution_end, end_of_day=True)

        return now > end

    @property
    def booking_limit(self) -> int | None:
        """ Returns the max_bookings_per_attendee limit if it applies. """
        return self.max_bookings_per_attendee


class _BookinPeriodMeta(NamedTuple):
    id: UUID
    title: str
    active: bool
    confirmed: bool
    confirmable: bool
    finalized: bool
    finalizable: bool
    archived: bool
    prebooking_start: date
    prebooking_end: date
    booking_start: date
    booking_end: date
    execution_start: date
    execution_end: date
    max_bookings_per_attendee: int | None
    booking_cost: Decimal | None
    all_inclusive: bool
    pay_organiser_directly: bool
    minutes_between: int | None
    alignment: str | None
    deadline_days: int | None
    book_finalized: bool
    cancellation_date: date | None
    cancellation_days: int | None
    age_barrier_type: str


@msgpack.make_serializable(tag=30)
class BookingPeriodMeta(_BookinPeriodMeta, BookingPeriodMixin):
    # TODO: We would like to add a request scoped cache to
    #       all the properties on PeriodMixin, since they would
    #       likely not change within the time span of a single
    #       request, but we can't use `cached_property`, since
    #       that would risk staying around across multiple requests
    #       alternatively we could add a time-based cache with
    #       a short TTL like 60 seconds. That would already avoid
    #       the many redundant calls to `phase`.

    def materialize(self, session: Session) -> BookingPeriod:
        period = session.get(BookingPeriod, self.id)
        assert period is not None
        return period

    def __setattr__(self, name: str, value: object) -> NoReturn:
        # NOTE: This is a guard against people setting attributes
        #       that exist on Period but not on PeriodMeta and
        #       getting silently dropped because of it.
        raise ValueError(
            'You are not allowed to set attributes on PeriodMeta.'
        )


class BookingPeriod(Base, BookingPeriodMixin, TimestampMixin):

    __tablename__ = 'periods'

    #: The public id of this period
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The public title of this period
    title: Mapped[str]

    #: Only one period is active at a time
    active: Mapped[bool] = mapped_column(default=False)

    #: A confirmed period may not be automatically matched anymore and all
    #: booking changes to it are communicated to the customer
    confirmed: Mapped[bool] = mapped_column(default=False)

    #: A confirmable period has a prebooking phase, while an unconfirmable
    # booking does not. An unconfirmable booking starts as `confirmed` for
    # legacy reasons (even though it doesn't sound sane to have an
    # unconfirmable period that is confirmed).
    confirmable: Mapped[bool] = mapped_column(default=True)

    #: A finalized period may not have any change in bookings anymore
    finalized: Mapped[bool] = mapped_column(default=False)

    #: A finalizable period may have invoices associated with it, an
    #: unfinalizable period may not
    finalizable: Mapped[bool] = mapped_column(default=True)

    #: An archived period has been entirely completed
    archived: Mapped[bool] = mapped_column(default=False)

    #: Start of the wishlist-phase
    prebooking_start: Mapped[date]

    #: End of the wishlist-phase
    prebooking_end: Mapped[date]

    #: Start of the booking-phase
    booking_start: Mapped[date]

    #: End of the booking-phase
    booking_end: Mapped[date]

    #: Date of the earliest possible occasion start of this period
    execution_start: Mapped[date]

    #: Date of the latest possible occasion end of this period
    execution_end: Mapped[date]

    #: Extra data stored on the period
    data: Mapped[dict[str, Any]] = mapped_column(default=dict)

    #: Maximum number of bookings per attendee
    max_bookings_per_attendee: Mapped[int | None]

    #: Base cost for one or many bookings
    booking_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=2)
    )

    #: True if the booking cost is meant for all bookings in a period
    #: or for each single booking
    all_inclusive: Mapped[bool] = mapped_column(default=False)

    #: True if the costs of an occasions need to be paid to the organiser
    pay_organiser_directly: Mapped[bool] = mapped_column(default=False)

    #: Time between bookings in minutes
    minutes_between: Mapped[int | None] = mapped_column(default=0)

    #: The alignment of bookings in the matching
    # FIXME: Restrict this to what is actually allowed i.e. Literal['day', ...]
    alignment: Mapped[str | None]

    #: Deadline for booking occasions. A deadline of 3 means that 3 days before
    #: an occasion is set to start, bookings are disabled.
    #:
    #: Note, unless book_finalized is set to True, this setting has no effect
    #: in a finalized period.
    #:
    #: Also, if deadline_days is None, bookings can't be created in a
    #: finalized period either, as deadline_days is a prerequisite for the
    #: book_finalized setting.
    deadline_days: Mapped[int | None]

    #: True if bookings can be created by normal users in finalized periods.
    #: The deadline_days are still applied for these normal users.
    #: Admins can always create bookings during any time, deadline_days and
    #: book_finalized are ignored.
    book_finalized: Mapped[bool] = mapped_column(default=False)

    #: Date after which no bookings can be canceled by a mere member
    cancellation_date: Mapped[date | None]

    #: Days between the occasion and the cancellation (an alternative to
    #: the cancellation_date)
    cancellation_days: Mapped[int | None]

    #: The age barrier implementation in use
    age_barrier_type: Mapped[str] = mapped_column(default='exact')

    __table_args__ = (
        CheckConstraint((
            # ranges should be valid
            'prebooking_start <= prebooking_end AND '
            'booking_start <= booking_end AND '
            'execution_start <= execution_end AND '

            # pre-booking must happen before booking and execution
            'prebooking_end <= booking_start AND '
            'prebooking_end <= execution_start AND '

            # booking and execution may overlap, but the execution cannot
            # start before booking begins
            'booking_start <= execution_start AND '
            'booking_end <= execution_end'
        ), name='period_date_order'),
        Index(
            'only_one_active_period',
            'active',
            unique=True,
            postgresql_where=column('active') == True
        )
    )

    #: The occasions linked to this period
    occasions: Mapped[list[Occasion]] = relationship(
        order_by='Occasion.order',
        back_populates='period'
    )

    #: The bookings linked to this period
    bookings: Mapped[list[Booking]] = relationship(
        back_populates='period'
    )

    invoices: Mapped[list[BookingPeriodInvoice]] = relationship(
        back_populates='period'
    )

    publication_requests: Mapped[list[PublicationRequest]] = relationship(
        back_populates='period'
    )

    @validates('age_barrier_type')
    def validate_age_barrier_type(
        self,
        key: str,
        age_barrier_type: str
    ) -> str:
        assert age_barrier_type in AgeBarrier.registry
        return age_barrier_type

    @property
    def age_barrier(self) -> AgeBarrier:
        return AgeBarrier.from_name(self.age_barrier_type)

    def activate(self) -> None:
        """ Activates the current period, causing all occasions and activites
        to update their status and book-keeping.

        It also makes sure no other period is active.

        """
        if self.active:
            return

        session = object_session(self)
        assert session is not None
        model = self.__class__

        active_period = (
            session.query(model)
            .filter(model.active == True).first()
        )

        if active_period:
            active_period.deactivate()

        # avoid triggering the only_one_active_period index constraint
        session.flush()

        self.active = True

    def deactivate(self) -> None:
        """ Deactivates the current period, causing all occasions and activites
        to update their status and book-keeping.

        """

        if not self.active:
            return

        self.active = False

    def confirm(self) -> None:
        """ Confirms the current period. """

        self.confirmed = True

        session = object_session(self)
        assert session is not None

        # open bookings are marked as denied during completion
        # and the booking costs are copied over permanently (so they can't
        # change anymore)
        b = session.query(Booking)
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

            booking.cost = booking.occasion.total_cost

    def archive(self) -> None:
        """ Moves all accepted activities with an occasion in this period
        into the archived state, unless there's already another occasion
        in a period newer than the current period.

        """
        assert self.confirmed and self.finalized or not self.finalizable

        self.archived = True
        self.active = False

        session = object_session(self)
        assert session is not None

        def future_periods() -> Iterator[UUID]:
            p = session.query(BookingPeriod)
            p = p.order_by(desc(BookingPeriod.execution_start))
            p = p.with_entities(BookingPeriod.id)

            for period in p:
                if period.id == self.id:
                    break
                yield period.id

        # get the activities which have an occasion in a future period
        f = session.query(Occasion)
        f = f.with_entities(Occasion.activity_id)
        f = f.filter(Occasion.period_id.in_(tuple(future_periods())))

        # get the activities which have an occasion in the given period but
        # no occasion in any future period
        o = session.query(Occasion)
        o = o.filter(Occasion.period_id == self.id)
        o = o.filter(not_(Occasion.activity_id.in_(f.scalar_subquery())))
        o = o.options(joinedload(Occasion.activity))

        # archive those
        for occasion in o:
            if occasion.activity.state == 'accepted':
                occasion.activity.archive()

        # also archive all activities without an occasion
        w = session.query(Occasion)
        w = w.with_entities(distinct(Occasion.activity_id))

        # XXX circular import
        from onegov.activity.models.activity import Activity

        a = session.query(Activity)
        a = a.filter(not_(Activity.id.in_(w.scalar_subquery())))
        a = a.filter(Activity.state == 'accepted')

        for activity in a:
            activity.archive()

    def confirm_and_start_booking_phase(self) -> None:
        """ Confirms the period and sets the booking phase to now.

        This is mainly an internal convenience function to activate the
        previous behaviour before a specific booking phase date was introduced.

        """

        self.confirmed = True
        self.prebooking_end = date.today()
        self.booking_start = date.today()

    @property
    def scoring(self) -> Scoring:
        # circular import
        from onegov.activity.matching.score import Scoring

        session = object_session(self)
        assert session is not None
        return Scoring.from_settings(
            settings=self.data.get('match-settings', {}),
            session=session
        )

    @scoring.setter
    def scoring(self, scoring: Scoring) -> None:
        self.data['match-settings'] = scoring.settings

    def materialize(self, session: Session) -> BookingPeriod:
        return self
