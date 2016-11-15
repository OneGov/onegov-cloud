""" Implements the matching algorithm used to match attendees to occasions.

The algorithm used is based on Deferred Acceptance. The algorithm has a
quadratic runtime.

"""

from onegov.activity import Booking, Occasion
from onegov.activity.matching.utils import overlaps, LoopBudget, hashable
from onegov.core.utils import Bunch
from itertools import groupby, product
from sortedcontainers import SortedSet
from sqlalchemy.orm import joinedload


class AttendeeAgent(hashable('id')):
    """ Acts on behalf of the attendee with the goal to get a stable booking
    with an occasion.

    A booking/occasion pair is considered stable if there exists no other
    such pair which is preferred by both the attendee and the occasion.

    In other words, if there's no other occasion that would accept the
    attendee over another attendee.

    """

    __slots__ = ('id', 'wishlist', 'accepted', 'blocked')

    def __init__(self, id, bookings):
        self.id = id

        # keep the wishlist sorted from highest to lowest priority, ignoring
        # the current state of the booking as we will assign them anew
        # each time we run the algorithm
        def booking_order(booking):
            return booking.priority * -1, booking.id

        self.wishlist = SortedSet(bookings, key=booking_order)
        self.accepted = set()
        self.blocked = set()

    def accept(self, booking):
        """ Accepts the given booking. """

        self.wishlist.remove(booking)
        self.accepted.add(booking)

        self.blocked |= {b for b in self.wishlist if overlaps(booking, b)}
        self.wishlist -= self.blocked

    def deny(self, booking):
        """ Removes the given booking from the accepted bookings. """

        self.wishlist.add(booking)
        self.accepted.remove(booking)

        # remove bookings from the blocked list which are not blocked anymore
        free = set(self.blocked)

        for accepted in self.accepted:
            for blocked in self.blocked:
                if overlaps(accepted, blocked):
                    free.remove(blocked)

        self.blocked -= free
        self.wishlist |= free

    @property
    def is_valid(self):
        """ Returns True if the results of this agent are valid.

        The algorithm should never get to this stage, so this is an extra
        security measure to make sure there's no bug.

        """
        for a, b in product(self.accepted, self.accepted):
            if a != b and overlaps(a, b):
                return False

        return True


class OccasionAgent(hashable('id')):
    """ Represents the other side of the Attendee/Occasion pair.

    While the attende agent will try to get the best possible occasion
    according to the wishses of the attendee, the occasion agent will
    try to get the best attendee according to the wishes of the occasion.

    These wishes may include hard-coded rules or peferences defined by the
    organiser/admin, who may manually prefer certain attendees over others.

    """

    __slots__ = ('occasion', 'bookings', 'attendees')

    def __init__(self, occasion):
        self.id = occasion.id
        self.occasion = occasion
        self.bookings = set()
        self.attendees = {}

    @property
    def full(self):
        return len(self.bookings) >= (self.occasion.max_spots)

    def preferred(self, booking):
        """ Returns the first booking with a lower score than the given
        booking (which indicates that the given booking is preferred over
        the returned item).

        If there's no preferred booking, None is returned.

        """
        return next(
            (b for b in self.bookings if b.score < booking.score),
            None
        )

    def match(self, attendee, booking):

        # as long as there are spots, automatically accept new requests
        if not self.full:
            self.attendees[booking] = attendee
            self.bookings.add(booking)

            attendee.accept(booking)
            return True

        # if the occasion is already full, accept the booking by throwing
        # another one out, if there exists a better fit
        over = self.preferred(booking)

        if over:
            self.attendees[over].deny(over)
            self.bookings.remove(over)

            self.bookings.add(booking)
            attendee.accept(booking)

            return True

        return False


def deferred_acceptance_from_database(session, period_id, **kwargs):
    b = session.query(Booking)
    b = b.options(joinedload(Booking.occasion))
    b = b.filter(Booking.period_id == period_id)
    b = b.filter(Booking.state.in_(('open', 'accepted', 'blocked')))

    o = session.query(Occasion)
    o = o.filter(Occasion.period_id == period_id)

    bookings = deferred_acceptance(bookings=b, occasions=o, **kwargs)

    # write the changes to the database
    def update_states(bookings, state):
        ids = set(b.id for b in bookings)

        if not ids:
            return

        b = session.query(Booking)
        b = b.filter(Booking.id.in_(ids))

        for booking in b:
            booking.state = state

    update_states(bookings.open, 'open')
    update_states(bookings.accepted, 'accepted')
    update_states(bookings.blocked, 'blocked')


def deferred_acceptance(bookings, occasions,
                        validity_check=True,
                        stability_check=False,
                        hard_budget=False):
    """ Matches bookings with occasions. """

    bookings = [b for b in bookings]
    bookings.sort(key=lambda b: b.attendee_id)

    occasions = {
        o.id: OccasionAgent(o) for o in occasions
    }

    attendees = {
        aid: AttendeeAgent(aid, bookings)
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
                if occasions[booking.occasion_id].match(candidate, booking):
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
        assert is_stable(attendees.values(), occasions.values())

    return Bunch(
        open=set(b for a in attendees.values() for b in a.wishlist),
        accepted=set(b for a in attendees.values() for b in a.accepted),
        blocked=set(b for a in attendees.values() for b in a.blocked)
    )


def is_stable(attendees, occasions):
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

                over = occasion.preferred(booking)

                if over:
                    for o in occasions:
                        if o != occasion and o.preferred(over):
                            return False

    return True
