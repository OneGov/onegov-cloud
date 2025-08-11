""" Implements the matching algorithm used to match attendees to occasions.

The algorithm used is based on Deferred Acceptance. The algorithm has a
quadratic runtime.

"""
from __future__ import annotations

from onegov.activity import Attendee, Booking, Occasion, BookingPeriod
from onegov.activity.matching.score import Scoring
from onegov.activity.matching.utils import overlaps, LoopBudget, HashableID
from onegov.activity.matching.utils import booking_order, unblockable
from onegov.core.utils import Bunch
from itertools import groupby, product
from sortedcontainers import SortedSet
from sqlalchemy.orm import joinedload, defer


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Sequence
    from decimal import Decimal
    from onegov.activity.models.booking import BookingState
    from sqlalchemy.orm import Session
    from typing import TypeAlias
    from uuid import UUID

    ScoreFunction: TypeAlias = Callable[[Booking], Decimal]


class AttendeeAgent(HashableID):
    """ Acts on behalf of the attendee with the goal to get a stable booking
    with an occasion.

    A booking/occasion pair is considered stable if there exists no other
    such pair which is preferred by both the attendee and the occasion.

    In other words, if there's no other occasion that would accept the
    attendee over another attendee.

    """

    __slots__ = ('id', 'wishlist', 'accepted', 'blocked')

    accepted: set[Booking]
    blocked: set[Booking]

    def __init__(
        self,
        id: UUID,
        bookings: Iterable[Booking],
        limit: int | None = None,
        minutes_between: float = 0,
        alignment: Literal['day', 'week', 'month'] | None = None
    ):
        self.id = id
        self.limit = limit
        self.wishlist = SortedSet(bookings, key=booking_order)
        self.accepted = set()
        self.blocked = set()
        self.minutes_between = minutes_between
        self.alignment = alignment

    def blocks(self, subject: Booking, other: Booking | Occasion) -> bool:
        return overlaps(
            subject, other, self.minutes_between, self.alignment,
            with_anti_affinity_check=True)

    def accept(self, booking: Booking) -> None:
        """ Accepts the given booking. """

        self.wishlist.remove(booking)
        self.accepted.add(booking)

        if self.limit and len(self.accepted) >= self.limit:
            self.blocked |= self.wishlist
        else:
            self.blocked |= {
                b for b in self.wishlist if self.blocks(booking, b)
            }

        self.wishlist -= self.blocked

    def deny(self, booking: Booking) -> None:
        """ Removes the given booking from the accepted bookings. """

        self.wishlist.add(booking)
        self.accepted.remove(booking)

        # remove bookings from the blocked list which are not blocked anymore
        for booking in unblockable(
                self.accepted, self.blocked, with_anti_affinity_check=True):

            self.blocked.remove(booking)
            self.wishlist.add(booking)

    @property
    def is_valid(self) -> bool:
        """ Returns True if the results of this agent are valid.

        The algorithm should never get to this stage, so this is an extra
        security measure to make sure there's no bug.

        """
        for a, b in product(self.accepted, self.accepted):
            if a != b and self.blocks(a, b):
                return False

        return True


class OccasionAgent(HashableID):
    """ Represents the other side of the Attendee/Occasion pair.

    While the attende agent will try to get the best possible occasion
    according to the wishses of the attendee, the occasion agent will
    try to get the best attendee according to the wishes of the occasion.

    These wishes may include hard-coded rules or peferences defined by the
    organiser/admin, who may manually prefer certain attendees over others.

    """

    __slots__ = ('occasion', 'bookings', 'attendees', 'score_function')

    bookings: set[Booking]
    attendees: dict[Booking, AttendeeAgent]
    score_function: ScoreFunction

    def __init__(
        self,
        occasion: Occasion,
        score_function: ScoreFunction | None = None
    ) -> None:

        self.id = occasion.id
        self.occasion = occasion
        self.bookings = set()
        self.attendees = {}
        self.score_function = score_function or (lambda b: b.score)

    @property
    def full(self) -> bool:
        return len(self.bookings) >= (self.occasion.max_spots)

    def preferred(self, booking: Booking) -> Booking | None:
        """ Returns the first booking with a lower score than the given
        booking (which indicates that the given booking is preferred over
        the returned item).

        If there's no preferred booking, None is returned.

        """
        return next(
            (
                b for b in self.bookings
                if self.score_function(b) < self.score_function(booking)
            ),
            None
        )

    def accept(self, attendee: AttendeeAgent, booking: Booking) -> None:
        self.attendees[booking] = attendee
        self.bookings.add(booking)
        attendee.accept(booking)

    def deny(self, booking: Booking) -> None:
        self.attendees[booking].deny(booking)
        self.bookings.remove(booking)
        del self.attendees[booking]

    def match(self, attendee: AttendeeAgent, booking: Booking) -> bool:

        # as long as there are spots, automatically accept new requests
        if not self.full:
            self.accept(attendee, booking)

            return True

        # if the occasion is already full, accept the booking by throwing
        # another one out, if there exists a better fit
        over = self.preferred(booking)

        if over:
            self.deny(over)
            self.accept(attendee, booking)

            return True

        return False


def deferred_acceptance(
    bookings: Sequence[Booking],
    occasions: Iterable[Occasion],
    score_function: ScoreFunction | None = None,
    validity_check: bool = True,
    stability_check: bool = False,
    hard_budget: bool = True,
    default_limit: int | None = None,
    attendee_limits: dict[UUID, int] | None = None,
    minutes_between: float = 0,
    alignment: Literal['day'] | None = None,
    sort_bookings: bool = True
) -> Bunch:  # FIXME: Return NamedTuple
    """ Matches bookings with occasions.

    :score_function:
        A function accepting a booking and returning a score. Occasions prefer
        bookings with a higher score over bookings with a lower score, if and
        only if the occasion is not yet full.

        The score function is meant to return a constant value for each
        booking during the run of the algorithm. If this is not the case,
        the algorithm might not halt.

    :validity_check:
        Ensures that the algorithm doesn't lead to any overlapping bookings.
        Runs in O(b) time, where b is the number of bookings per period.

    :stability_check:
        Ensures that the result does not contain any blocking pairs, that is
        it checks that the result is stable. This runs in O(b^3) time, so
        do not run this in production (it's more of a testing tool).

    :hard_budget:
        Makes sure that the algorithm halts eventually by raising an exception
        if the runtime budget of O(a*b) is reached (number of attendees
        times the number of bookings).

        Feel free to proof that this can't happen and then remove the check ;)

    :default_limit:
        The maximum number of bookings which should be accepted for each
        attendee.

    :attendee_limits:
        The maximum number of bookings which should be accepted for each
        attendee. Keyed by the attendee id, this dictionary contains
        per-attendee limits. Those fall back to the default_limit.

    :minutes_between:
        The minutes between each booking that should be considered
        transfer-time. That is the time it takes to get from one booking
        to another. Basically acts as a suffix to each booking, extending
        it's end time by n minutes.

    :alignment:
        Align the date range to the given value. Currently only 'day' is
        supported. When an alignment is active, all bookings are internally
        stretched to at least cover the alignment.

        For example, if 'day' is given, a booking that lasts 4 hours is
        considered to last the whole day and it will block out bookings
        on the same day.

        Note that the ``minutes_between`` parameter is independent of this.
        That is if there's 90 minutes between bookigns and the bookings are
        aligned to the day, there can only be a booking every other day::

            10:00 - 19:00 becomes 00:00 - 24:00 + 90mins.

        Usually you probably do not want minutes_between combined with
        an alignment.

    """
    assert alignment in (None, 'day')

    if sort_bookings:
        bookings = sorted(bookings, key=lambda b: b.attendee_id)

    attendee_limits = attendee_limits or {}

    # pre-calculate the booking scores
    score_function = score_function or Scoring()

    for booking in bookings:
        booking.score = score_function(booking)

    # after the booking score has been calculated, the scoring function
    # should no longer be used for performance reasons
    score_function = None

    occasions_ = {o.id: OccasionAgent(o) for o in occasions}

    attendees = {
        aid: AttendeeAgent(
            aid,
            limit=attendee_limits.get(aid, default_limit),
            bookings=bookings,
            minutes_between=minutes_between,
            alignment=alignment
        )
        for aid, bookings in groupby(bookings, key=lambda b: b.attendee_id)
    }

    # I haven't proven yet that the following loop will always end. Until I
    # do there's a fallback check to make sure that we'll stop at some point
    budget = LoopBudget(max_ticks=len(bookings) * len(attendees))

    # while there are attendees with entries in a wishlist
    while next((a for a in attendees.values() if a.wishlist), None):

        if budget.limit_reached(as_exception=hard_budget):
            break

        candidates = [a for a in attendees.values() if a.wishlist]
        matched = 0

        # match attendees to courses
        while candidates:
            candidate = candidates.pop()

            for booking in candidate.wishlist:
                if occasions_[booking.occasion_id].match(candidate, booking):
                    matched += 1
                    break  # required because the wishlist has been changed

        # if no matches were possible the situation can't be improved
        if not matched:
            break

    # make sure the algorithm didn't make any mistakes
    if validity_check:
        for a in attendees.values():
            assert a.is_valid

    # make sure the result is stable
    if stability_check:
        assert is_stable(attendees.values(), occasions_.values())

    return Bunch(
        open={b for a in attendees.values() for b in a.wishlist},
        accepted={b for a in attendees.values() for b in a.accepted},
        blocked={b for a in attendees.values() for b in a.blocked},
    )


def deferred_acceptance_from_database(
    session: Session,
    period_id: UUID,
    *,
    score_function: ScoreFunction | None = None,
    validity_check: bool = True,
    stability_check: bool = False,
    hard_budget: bool = True,
) -> None:

    period = session.query(BookingPeriod).filter(
        BookingPeriod.id == period_id
    ).one()

    b = session.query(Booking)
    b = b.options(joinedload(Booking.occasion))
    b = b.filter(Booking.period_id == period_id)
    b = b.filter(Booking.state != 'cancelled')
    b = b.filter(Booking.created >= period.created)
    b = b.order_by(Booking.attendee_id)

    o = session.query(Occasion)
    o = o.filter(Occasion.period_id == period_id)
    o = o.options(
        defer('meeting_point'),
        defer('note'),
        defer('cost')
    )

    if period.max_bookings_per_attendee:
        default_limit = period.max_bookings_per_attendee
        attendee_limits = None
    else:
        default_limit = None
        attendee_limits = {
            a.id: a.limit for a in
            session.query(Attendee.id, Attendee.limit)
        }

    # fetch it here as it'll be reused multiple times
    bookings = list(b)

    results = deferred_acceptance(
        bookings=bookings,
        occasions=o,
        default_limit=default_limit,
        attendee_limits=attendee_limits,
        minutes_between=period.minutes_between or 0,
        alignment=period.alignment,  # type:ignore[arg-type]
        sort_bookings=False,
        score_function=score_function,
        validity_check=validity_check,
        hard_budget=hard_budget
    )

    # write the changes to the database
    def update_bookings(targets: set[Booking], state: BookingState) -> None:
        q = session.query(Booking)
        q = q.filter(Booking.state != state)
        q = q.filter(Booking.state != 'cancelled')
        q = q.filter(Booking.period_id == period_id)
        q = q.filter(Booking.id.in_(t.id for t in targets))

        for booking in q:
            booking.state = state

    with session.no_autoflush:
        update_bookings(results.open, 'open')
        update_bookings(results.accepted, 'accepted')
        update_bookings(results.blocked, 'blocked')


def is_stable(
    attendees: Iterable[AttendeeAgent],
    occasions: Collection[OccasionAgent]
) -> bool:
    """ Returns true if the matching between attendees and occasions is
    stable.

    This runs in O(n^4) time, where n is the combination of
    bookings and occasions. So this is a testing tool, not something to
    run in production.

    """

    for attendee in attendees:
        for booking in attendee.accepted:
            for occasion in occasions:

                # the booking was actually accepted, skip
                if booking in occasion.bookings:
                    continue

                # if the current occasion prefers the given booking..
                over = occasion.preferred(booking)

                if over:
                    for o in occasions:
                        if o == occasion:
                            continue

                        # ..and another occasion prefers the loser..
                        switch = o.preferred(over)

                        # .. we have an unstable matching
                        if switch and occasion.preferred(switch):
                            return False

    return True
