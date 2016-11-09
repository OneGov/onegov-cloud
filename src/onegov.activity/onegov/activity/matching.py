""" Implements the matching algorithm used to match attendees to occasions.

The algorithm used is based on Deferred Acceptance. The algorithm has a
quadratic runtime.

"""

import sedate

from onegov.activity import Attendee, Booking, Occasion
from itertools import product
from sortedcontainers import SortedSet
from sqlalchemy.orm import joinedload


def overlaps(booking, other):
    assert booking != other

    return sedate.overlaps(
        booking.occasion.start, booking.occasion.end,
        other.occasion.start, other.occasion.end
    )


def bookings_by_state(bookings, state):
    yield from (b for b in bookings if b.state == state)


class AttendeeAgent(object):
    """ Acts on behalf of the attendee with the goal to get a stable booking
    with an occasion.

    A booking/occasion pair is considered stable if there exists no other
    such pair which is preferred by both the attendee and the occasion.

    In other words, if there's no other occasion that would accept the
    attendee over another attendee.

    """

    __slots__ = ('attendee', 'wishlist', 'accepted', 'blocked')

    def __init__(self, attendee):
        self.attendee = attendee

        # keep the wishlist sorted from highest to lowest priority
        self.wishlist = SortedSet(
            bookings_by_state(attendee.bookings, 'open'),
            key=lambda b: b.priority * -1
        )

        self.accepted = set(bookings_by_state(attendee.bookings, 'accepted'))
        self.blocked = set(bookings_by_state(attendee.bookings, 'blocked'))

    def __hash__(self):
        return hash(self.attendee)

    def __eq__(self, other):
        return self.attendee.id == other.attendee.id

    def accept(self, booking):
        """ Accepts the given booking. """

        self.wishlist.remove(booking)
        self.accepted.add(booking)

        self.blocked |= {b for b in self.wishlist if overlaps(booking, b)}

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

    def __init__(self, occasion, attendees):
        self.occasion = occasion
        self.bookings = set(bookings_by_state(occasion.bookings, 'accepted'))

        # keep track of the attendees associated with a booking -> this
        # indicates that we might need some kind of interlocutor which
        # handles the relationship between the agents
        self.attendees = {
            booking: a
            for a in attendees
            for booking in a.accepted
        }

    def __hash__(self):
        return hash(self.occasion)

    def __eq__(self, other):
        return self.occasion.id == other.occasion.id

    @property
    def operable(self):
        return len(self.bookings) >= self.occasion.spots.lower

    @property
    def full(self):
        return len(self.bookings) == (self.occasion.spots.upper - 1)

    def score(self, booking):
        return booking.priority

    def match(self, attendee, booking):

        # as long as there are spots, automatically accept new requests
        if not self.full:
            self.attendees[booking] = attendee
            self.bookings.add(booking)

            attendee.accept(booking)
            return True

        # if the occasion is already full, accept the booking by throwing
        # another one out, if there exists a better fit
        for b in self.bookings:
            if self.score(b) < self.score(booking):
                self.attendees[b].deny(b)
                self.bookings.remove(b)
                self.bookings.add(booking)

                attendee.accept(booking)
                return True

        return False


def match_bookings_with_occasions(session, period_id):
    """ Matches bookings with occasions. """

    attendees = set(
        AttendeeAgent(a) for a in
        session.query(Attendee).options(joinedload(Attendee.bookings)))

    occasions = set(
        OccasionAgent(o, attendees) for o in
        session.query(Occasion).options(joinedload(Occasion.bookings))
        .filter(Occasion.period_id == period_id))

    occasions_by_booking = {
        booking: occasion
        for occasion in occasions
        for booking in occasion.occasion.bookings}

    # while there are attendees with entries in a wishlist
    while next((a for a in attendees if a.wishlist), None):

        candidates = [a for a in attendees if a.wishlist]
        matched = 0

        # match attendees to courses
        while candidates:
            candidate = candidates.pop()

            for booking in candidate.wishlist:
                if occasions_by_booking[booking].match(candidate, booking):
                    matched += 1
                    break

        # if no matches were possible the situation can't be improved
        if not matched:
            break

    # make sure the algorithm didn't make any mistakes
    for a in attendees:
        assert a.is_valid

    # write the changes to the database
    def update_states(bookings, state):
        ids = set(b.id for b in bookings)

        if not ids:
            return

        b = session.query(Booking)
        b = b.filter(Booking.id.in_(ids))
        b.update({Booking.state: state}, 'fetch')

    update_states(set(b for a in attendees for b in a.wishlist), 'open')
    update_states(set(b for a in attendees for b in a.accepted), 'accepted')
    update_states(set(b for a in attendees for b in a.blocked), 'blocked')
