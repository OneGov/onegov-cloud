from __future__ import annotations

from onegov.activity import log
from onegov.activity.utils import dates_overlap
from sortedcontainers import SortedSet


from typing import overload, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Hashable, Iterable
    from decimal import Decimal
    from onegov.activity.models import Booking, Occasion
    from onegov.activity.matching.interfaces import MatchableBooking
    from onegov.activity.matching.interfaces import MatchableOccasion
    from sortedcontainers._typing import SupportsHashableAndRichComparison
    from sortedcontainers.sortedset import SortedKeySet
    from typing_extensions import TypeVar
    from uuid import UUID

    BookingT = TypeVar('BookingT', bound=MatchableBooking | Booking)
    OccasionT = TypeVar('OccasionT', bound=MatchableOccasion | Occasion)
    OrderT = TypeVar(
        'OrderT',
        bound=SupportsHashableAndRichComparison,
        default=tuple[Decimal, int, UUID]
    )


def overlaps(
    booking: Booking | MatchableBooking,
    other: Booking | Occasion | MatchableBooking | MatchableOccasion,
    minutes_between: float = 0,
    alignment: Literal['day', 'week', 'month'] | None = None,
    with_anti_affinity_check: bool = False
) -> bool:
    """ Returns true if the given booking overlaps with the given booking
    or occasion.

    """

    # even if exclude_from_overlap_check is active we consider a booking
    # to overlap itself (this protects against double bookings)
    if booking.id == other.id:
        return True

    if hasattr(other, 'occasion'):
        other_occasion = other.occasion
    else:
        other_occasion = other

    if with_anti_affinity_check:
        if other_occasion.anti_affinity_group is not None:
            if (
                booking.occasion.anti_affinity_group
                == other_occasion.anti_affinity_group
            ):
                return True

    if booking.occasion.exclude_from_overlap_check:
        return False

    if other_occasion.exclude_from_overlap_check:
        return False

    return dates_overlap(
        tuple((b.start, b.end) for b in booking.dates),
        tuple((o.start, o.end) for o in other.dates),
        minutes_between=minutes_between,
        alignment=alignment
    )


class LoopBudget:
    """ Helps ensure that a loop doesn't overreach its complexity budget.

    For example::

        budget = LoopBudget(max_ticks=10)

        while True:
            if budget.limit_reached():
                break
    """

    def __init__(self, max_ticks: int) -> None:
        self.ticks = 0
        self.max_ticks = max_ticks

    def limit_reached(self, as_exception: bool = False) -> bool | None:
        if self.ticks >= self.max_ticks:
            message = 'Loop limit of {} has been reached'.format(self.ticks)

            if as_exception:
                raise RuntimeError(message)
            else:
                log.warning(message)

            return True

        self.ticks += 1
        return False


class HashableID:

    id: Hashable

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id


@overload
def booking_order(booking: Booking) -> tuple[Decimal, int, UUID]: ...

@overload
def booking_order(
    booking: MatchableBooking
) -> tuple[Decimal, int, SupportsRichComparison]: ...


def booking_order(
    booking: Booking | MatchableBooking
) -> tuple[Decimal, int, SupportsRichComparison]:
    """ Keeps the bookings predictably sorted from highest to lowest priority.

    """

    return booking.score * - 1, booking.priority * -1, booking.id


def unblockable(
    accepted: Iterable[BookingT],
    blocked: Iterable[BookingT],
    # NOTE: value defaults don't yet have an exception for type params
    #       with a default type. So we need to ignore here, despite the
    #       types matching.
    key: Callable[[BookingT], OrderT] = booking_order,  # type:ignore
    with_anti_affinity_check: bool = False
) -> SortedKeySet[BookingT, OrderT]:
    """ Returns a set of items in the blocked set which do not block
    with anything. The set is ordered using :func:`booking_order`.

    """

    unblockable = SortedSet(blocked, key=key)

    for a in accepted:
        for b in blocked:
            if a.overlaps(
                    b, with_anti_affinity_check=with_anti_affinity_check):  # type: ignore[arg-type]
                unblockable.discard(b)

    return unblockable
