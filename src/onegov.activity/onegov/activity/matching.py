""" Implements the matching algorithm used to match attendees to occasions.

The algorithm used is based on Deferred Acceptance. The algorithm has a
quadratic runtime.

"""

import sedate

from abc import ABCMeta, abstractmethod
from onegov.activity import log
from onegov.activity import Booking, Occasion
from onegov.core.utils import Bunch
from itertools import groupby, product
from sortedcontainers import SortedSet
from sqlalchemy.orm import joinedload


def overlaps(booking, other):
    assert booking != other

    return sedate.overlaps(
        booking.start, booking.end,
        other.start, other.end
    )


def bookings_by_state(bookings, state):
    yield from (b for b in bookings if b.state == state)


class MatchableBooking(metaclass=ABCMeta):
    """ Describes the interface required by the booking class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    def __eq__(self, other):
        """ The class must be comparable to other classes. """

    @abstractmethod
    def __hash__(self):
        """ The class must be hashable. """

    @property
    @abstractmethod
    def occasion_id(self):
        """ Returns the id of the occasion this booking belongs to. """

    @property
    @abstractmethod
    def attendee_id(self):
        """ Returns the id of the attendee this booking belongs to. """

    @abstractmethod
    def score(self):
        """ Returns the score of the current booking. Occasions prefer
        bookings by score. The higher the score, the more the booking is
        preferred over others.

        The value of the score is an integer which must not change during
        the runtime of the algorithm (otherwise the algorithm may not halt).

        """

    @property
    @abstractmethod
    def state(self):
        """ Returns the state of the booking, one of:

        * "open" (for unassigned bookings)
        * "accepted" (for already accepted bookings)
        * "blocked" (for bookings blocked by another accepted booking)

        """

    @property
    @abstractmethod
    def priority(self):
        """ Returns the priority of the booking. The higher the priority
        the further up the wishlist.

        Bookings further up the wishlist are first passed to the occasions.
        All things being equal (i.e. the scores of the other bookings), this
        leads to a higher chance of placement.

        """

    @property
    @abstractmethod
    def start(self):
        """ Returns the start-time of the booking. """

    @property
    @abstractmethod
    def end(self):
        """ Returns the start-time of the booking. """


class MatchableOccasion(metaclass=ABCMeta):
    """ Describes the interface required by the occasion class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    @property
    @abstractmethod
    def id(self):
        """ The id of the occasion. """

    @property
    @abstractmethod
    def max_spots(self):
        """ The maximum number of available spots. """


class AttendeeAgent(object):
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
        self.wishlist = SortedSet(bookings, key=lambda b: b.priority * -1)
        self.accepted = set()
        self.blocked = set()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

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
                if self.overlaps(accepted, blocked):
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


class OccasionAgent(object):
    """ Represents the other side of the Attendee/Occasion pair.

    While the attende agent will try to get the best possible occasion
    according to the wishses of the attendee, the occasion agent will
    try to get the best attendee according to the wishes of the occasion.

    These wishes may include hard-coded rules or peferences defined by the
    organiser/admin, who may manually prefer certain attendees over others.

    """

    __slots__ = ('occasion', 'bookings', 'attendees')

    def __init__(self, occasion):
        self.occasion = occasion
        self.bookings = set()
        self.attendees = {}

    def __hash__(self):
        return hash(self.occasion)

    def __eq__(self, other):
        return self.occasion.id == other.occasion.id

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


def match_bookings_with_occasions_from_db(session, period_id, **kwargs):
    MatchableBooking.register(Booking)
    MatchableOccasion.register(Occasion)

    b = session.query(Booking)
    b = b.options(joinedload(Booking.occasion))
    b = b.filter(Booking.period_id == period_id)
    b = b.filter(Booking.state.in_(('open', 'accepted', 'blocked')))

    o = session.query(Occasion)
    o = o.filter(Occasion.period_id == period_id)

    bookings = match_bookings_with_occasions(bookings=b, occasions=o, **kwargs)

    # write the changes to the database
    def update_states(bookings, state):
        ids = set(b.id for b in bookings)

        if not ids:
            return

        b = session.query(Booking)
        b = b.filter(Booking.id.in_(ids))
        b.update({Booking.state: state}, 'fetch')

    update_states(bookings.open, 'open')
    update_states(bookings.accepted, 'accepted')
    update_states(bookings.blocked, 'blocked')


def valid_bookings(bookings):
    for booking in bookings:
        assert issubclass(booking.__class__, MatchableBooking)
        yield booking


def valid_occasions(occasions):
    for occasion in occasions:
        assert issubclass(occasion.__class__, MatchableOccasion)
        yield occasion


def by_attendee(booking):
    return booking.attendee_id


class LoopProtection(object):

    def __init__(self, max_ticks):
        self.ticks = 0
        self.max_ticks = max_ticks

    def limit_reached(self):
        self.ticks += 1

        if self.ticks >= self.max_ticks:
            log.warn("Loop limit of {} has been reached".format(self.ticks))
            return True


def match_bookings_with_occasions(bookings, occasions, stability_check=False):
    """ Matches bookings with occasions. """

    bookings = [b for b in valid_bookings(bookings)]
    bookings.sort(key=by_attendee)

    attendees = {
        aid: AttendeeAgent(aid, bookings)
        for aid, bookings in groupby(bookings, key=by_attendee)
    }

    occasions = {
        o.id: OccasionAgent(o)
        for o in valid_occasions(occasions)
    }

    # I haven't proven yet that the following loop will always end. Until I
    # do there's a fallback check to make sure that we'll stop at some point
    protection = LoopProtection(max_ticks=len(attendees) * 2)

    # while there are attendees with entries in a wishlist
    while next((a for a in attendees.values() if a.wishlist), None):

        if protection.limit_reached():
            break

        candidates = [a for a in attendees.values() if a.wishlist]
        matched = 0

        # match attendees to courses
        while candidates:
            candidate = candidates.pop()

            for booking in candidate.wishlist:
                if occasions[booking.occasion_id].match(candidate, booking):
                    matched += 1
                    break

        # if no matches were possible the situation can't be improved
        if not matched:
            break

    # make sure the algorithm didn't make any mistakes
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
