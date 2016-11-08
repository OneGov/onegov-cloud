""" Implements the matching algorithm used to match attendees to occasions.

The algorithm used is based on Deferred Acceptance. The algorithm has a
quadratic runtime.

"""


class AttendeeAgent(object):
    """ Acts on behalf of the attendee with the goal to get a stable booking
    with an occasion.

    A booking/occasion pair is considered stable if there exists no other
    such pair which is preferred by both the attendee and the occasion.

    In other words, if there's no other occasion that would accept the
    attendee over another attendee.

    """

    def __init__(self, attendee):
        self.attendee = attendee


class OccasionAgent(object):
    """ Represents the other side of the Attendee/Occasion pair.

    While the attende agent will try to get the best possible occasion
    according to the wishses of the attendee, the occasion agent will
    try to get the best attendee according to the wishes of the occasion.

    These wishes may include hard-coded rules or peferences defined by the
    organiser/admin, who may manually prefer certain attendees over others.

    """

    def __init__(self, occasion):
        self.occasion = occasion


def match_bookings_with_occasions(session):
    """ Matches bookings with occasions. """
