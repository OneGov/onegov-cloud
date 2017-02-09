from datetime import date, timedelta
from functools import partial
from itertools import count
from onegov.activity.matching import deferred_acceptance
from onegov.activity.matching import MatchableBooking
from onegov.activity.matching import MatchableOccasion
from onegov.activity.matching import PreferAdminChildren
from onegov.activity.matching import PreferInAgeBracket
from onegov.activity.matching import PreferMotivated
from onegov.activity.matching import PreferOrganiserChildren
from onegov.activity.matching import Scoring
from onegov.core.utils import Bunch


today = date.today
keycount = count(start=1, step=1)

match = partial(
    deferred_acceptance,
    stability_check=True,
    validity_check=True,
    hard_budget=True
)


def days(n):
    return timedelta(days=n)


class Booking(MatchableBooking):

    def __init__(self, occasion, attendee, state, priority, dates):
        self.occasion = occasion
        self.attendee = attendee
        self._id = next(keycount)
        self._state = state
        self._priority = priority
        self._dates = dates

    def __eq__(self, other):
        return self._id == other._id

    def __hash__(self):
        return hash(self._id)

    @property
    def id(self):
        return self._id

    @property
    def occasion_id(self):
        return self.occasion

    @property
    def attendee_id(self):
        return self.attendee

    @property
    def state(self):
        return self._state

    @property
    def priority(self):
        return self._priority

    @property
    def dates(self):
        return [Bunch(start=s, end=e) for s, e in self._dates]


class Occasion(MatchableOccasion):

    def __init__(self, name, dates, max_spots=10):
        self.name = name
        self._max_spots = max_spots
        self._dates = dates

    @property
    def id(self):
        return self.name

    @property
    def max_spots(self):
        return self._max_spots

    def booking(self, attendee, state, priority):
        return Booking(self.id, attendee, state, priority, self._dates)

    @property
    def dates(self):
        return [Bunch(start=s, end=e) for s, e in self._dates]


def test_overlapping_bookings():

    # the algorithm will block other bookings, favoring higher priorities
    o1 = Occasion("Daytrip", [[today(), today()]])
    o2 = Occasion("Camp", [[today(), today() + days(1)]])
    o3 = Occasion("Zoo", [[today() + days(1), today() + days(2)]])

    bookings = [
        o1.booking("Justin", 'open', 1),
        o2.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2))

    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1]}

    # the order of the bookings doesn't matter
    bookings = [
        o1.booking("Justin", 'open', 0),
        o2.booking("Justin", 'open', 1)
    ]

    result = match(bookings, (o1, o2))

    assert not result.open
    assert result.blocked == {bookings[0]}
    assert result.accepted == {bookings[1]}

    # if the bookings found are instable, the algorithm will correct that
    bookings = [
        o1.booking("Justin", 'blocked', 1),
        o2.booking("Justin", 'accepted', 0)
    ]

    result = match(bookings, (o1, o2))

    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1]}

    # always prefer the booking with the highest priority, even if it leads
    # to more blocked bookings than it would otherwise
    bookings = [
        o1.booking("Justin", 'open', 0),
        o2.booking("Justin", 'open', 1),
        o3.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3))

    assert not result.open
    assert result.blocked == {bookings[0], bookings[2]}
    assert result.accepted == {bookings[1]}

    # be predictable if there are no other preferences
    bookings = [
        o1.booking("Justin", 'open', 0),
        o2.booking("Justin", 'open', 0),
        o3.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3))

    assert not result.open
    assert result.accepted == {bookings[0], bookings[2]}
    assert result.blocked == {bookings[1]}


def test_overlapping_bookings_with_multiple_dates():

    o1 = Occasion("Daytrip", [
        [today(), today()],
        [today() + days(1), today() + days(1)]
    ])

    o2 = Occasion("Camp", [
        [today() + days(1), today() + days(1)],
        [today() + days(2), today() + days(2)]
    ])

    bookings = [
        o1.booking("Justin", 'open', 1),
        o2.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2))

    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1]}


def test_accept_highest_priority():

    o = Occasion("Best Activity Ever", [[today(), today()]], max_spots=2)
    bookings = [
        o.booking("Tick", 'open', 0),
        o.booking("Trick", 'open', 1),
        o.booking("Track", 'open', 1)
    ]

    result = match(bookings, [o])

    assert result.open == {bookings[0]}
    assert result.accepted == {bookings[1], bookings[2]}
    assert not result.blocked

    # all other things being equal, the choice is inherently random.
    # to be predictable we need to change all the set and dictionaries to
    # their ordered counterparts which is something we want to avoid for
    # performance/memory usage reasons
    o = Occasion("Best Activity Ever", [[today(), today()]], max_spots=2)
    bookings = [
        o.booking("Tick", 'open', 0),
        o.booking("Trick", 'open', 0),
        o.booking("Track", 'open', 1)
    ]

    result = match(bookings, [o])

    # the first result loses, because it's the first result with a lower
    # score than the third booking - we could turn this around, the important
    # thing is that we are predictable
    assert result.open == {bookings[0]} or result.open == {bookings[1]}
    assert result.accepted == {bookings[1], bookings[2]} or\
        result.accepted == {bookings[0], bookings[2]}
    assert not result.blocked


def test_prefer_motivated():
    motivation_score = PreferMotivated()

    assert motivation_score(Bunch(priority=1)) == 1
    assert motivation_score(Bunch(priority=0)) == 0
    assert motivation_score(Bunch(priority=123)) == 123


def test_prefer_in_age_bracket():
    age_range = None
    attendee_age = None

    age_bracket_score = PreferInAgeBracket(
        get_age_range=lambda b: age_range,
        get_attendee_age=lambda b: attendee_age)

    age_range = (10, 20)
    attendee_age = 10

    assert age_bracket_score(None) == 1.0

    attendee_age = 21
    assert age_bracket_score(None) == 0.9

    attendee_age = 22
    assert age_bracket_score(None) == 0.8

    attendee_age = 23
    assert age_bracket_score(None) == 0.7

    attendee_age = 30
    assert age_bracket_score(None) == 0.0

    attendee_age = 9
    assert age_bracket_score(None) == 0.9

    attendee_age = 8
    assert age_bracket_score(None) == 0.8


def test_prefer_organiser_children():

    is_organiser_child = None

    organiser_child_score = PreferOrganiserChildren(
        get_is_organiser_child=lambda c: is_organiser_child)

    is_organiser_child = True
    assert organiser_child_score(None) == 1.0

    is_organiser_child = False
    assert organiser_child_score(None) == 0.0


def test_prefer_association_children():

    is_association_child = None

    association_child_score = PreferAdminChildren(
        get_is_association_child=lambda c: is_association_child)

    is_association_child = True
    assert association_child_score(None) == 1.0

    is_association_child = False
    assert association_child_score(None) == 0.0


def test_serialize_scoring(session):

    scoring = Scoring()
    assert scoring.settings == {}

    scoring.criteria.append(PreferInAgeBracket.from_session(session))
    assert scoring.settings == {
        'prefer_in_age_bracket': True
    }

    scoring.criteria.append(PreferOrganiserChildren.from_session(session))
    assert scoring.settings == {
        'prefer_in_age_bracket': True,
        'prefer_organiser': True
    }

    scoring.criteria.append(PreferAdminChildren.from_session(session))
    assert scoring.settings == {
        'prefer_in_age_bracket': True,
        'prefer_organiser': True,
        'prefer_admins': True
    }

    scoring = Scoring.from_settings(scoring.settings, session)

    assert len(scoring.criteria) == 4


def test_booking_limit():

    o1 = Occasion(1, [[today(), today()]])
    o2 = Occasion(2, [[today() + days(1), today() + days(1)]])
    o3 = Occasion(3, [[today() + days(2), today() + days(2)]])
    o4 = Occasion(4, [[today() + days(3), today() + days(3)]])

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
        o3.booking("Tom", 'open', 0),
        o4.booking("Tom", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3, o4), limit=1)

    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1], bookings[2], bookings[3]}

    result = match(bookings, (o1, o2, o3, o4), limit=2)

    assert not result.open
    assert result.accepted == {bookings[0], bookings[1]}
    assert result.blocked == {bookings[2], bookings[3]}

    result = match(bookings, (o1, o2, o3, o4), limit=3)

    assert not result.open
    assert result.accepted == {bookings[0], bookings[1], bookings[2]}
    assert result.blocked == {bookings[3]}

    result = match(bookings, (o1, o2, o3, o4), limit=4)

    assert not result.open
    assert len(result.accepted) == 4
    assert not result.blocked

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
        o3.booking("Tom", 'open', 1),
        o4.booking("Tom", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3, o4), limit=1)

    assert not result.open
    assert result.accepted == {bookings[2]}
    assert result.blocked == {bookings[0], bookings[1], bookings[3]}

    bookings = [
        o1.booking("Tom", 'open', 2),
        o2.booking("Tom", 'open', 1),
        o3.booking("Tom", 'open', 0),
        o1.booking("Harry", 'open', 0),
        o2.booking("Harry", 'open', 2),
        o3.booking("Harry", 'open', 1),
    ]

    result = match(bookings, (o1, o2, o3, o4), limit=1)

    assert not result.open
    assert result.accepted == {bookings[0], bookings[4]}
    assert len(result.blocked) == 4

    result = match(bookings, (o1, o2, o3, o4), limit=2)

    assert not result.open
    assert result.accepted == {
        bookings[0],
        bookings[1],
        bookings[4],
        bookings[5]
    }
    assert len(result.blocked) == 2
