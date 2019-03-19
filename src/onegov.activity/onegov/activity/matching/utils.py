from onegov.activity import log
from onegov.activity.utils import dates_overlap
from sortedcontainers import SortedSet


def overlaps(booking, other, minutes_between=0, alignment=None):
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

    if other_occasion.anti_affinity_group is not None:
        if booking.occasion.anti_affinity_group \
                == other_occasion.anti_affinity_group:
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


class LoopBudget(object):
    """ Helps ensure that a loop doesn't overreach its complexity budget.

    For example::

        budget = LoopBudget(max_ticks=10)

        while True:
            if budget.limit_reached():
                break
    """

    def __init__(self, max_ticks):
        self.ticks = 0
        self.max_ticks = max_ticks

    def limit_reached(self, as_exception=False):
        if self.ticks >= self.max_ticks:
            message = "Loop limit of {} has been reached".format(self.ticks)

            if as_exception:
                raise RuntimeError(message)
            else:
                log.warning(message)

            return True

        self.ticks += 1


def hashable(attribute):

    class Hashable(object):

        def __hash__(self):
            return hash(getattr(self, attribute))

        def __eq__(self, other):
            return getattr(self, attribute) == getattr(other, attribute)

    return Hashable


def booking_order(booking):
    """ Keeps the bookings predictably sorted from highest to lowest priority.

    """

    return booking.score * - 1, booking.priority * -1, booking.id


def unblockable(accepted, blocked, key=booking_order):
    """ Returns a set of items in the blocked set which do not block
    with anything. The set is ordered using :func:`booking_order`.

    """

    unblockable = SortedSet(blocked, key=key)

    for a in accepted:
        for b in blocked:
            if a.overlaps(b):
                unblockable.discard(b)

    return unblockable
