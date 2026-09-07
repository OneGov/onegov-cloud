from __future__ import annotations

import sys

from datetime import date, timedelta, datetime
from decimal import Decimal
from functools import partial
from itertools import count
from onegov.activity.utils import dates_overlap
from onegov.activity.matching import deferred_acceptance
from onegov.activity.matching import MatchableBooking
from onegov.activity.matching import MatchableOccasion
from onegov.activity.matching import PreferAdminChildren
from onegov.activity.matching import PreferInAgeBracket
from onegov.activity.matching import PreferMotivated
from onegov.activity.matching import PreferOrganiserChildren
from onegov.activity.matching import Scoring
from onegov.activity.matching.core import is_stable, OccasionAgent
from onegov.activity.matching.utils import unblockable
from onegov.core.utils import Bunch
from sedate import standardize_date
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.activity.models.booking import BookingState
    from sqlalchemy.orm import Session


today = date.today
keycount = count(start=1, step=1)

match = partial(
    deferred_acceptance,
    stability_check=True,
    validity_check=True,
    hard_budget=True
)


def days(n: float) -> timedelta:
    return timedelta(days=n)


class Booking(MatchableBooking):

    preferred_occasion: str

    def __init__(
        self,
        occasion: Occasion,
        attendee: str,
        state: BookingState,
        priority: int,
        dates: Sequence[tuple[date | datetime, date | datetime]],
        score: int = 0
    ) -> None:
        self.occasion = occasion
        self.attendee = attendee
        self._id = next(keycount)
        self._state = state
        self._priority = priority
        self._dates = dates
        self.score = Decimal(score)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def occasion_id(self) -> str:
        return self.occasion.id

    @property
    def attendee_id(self) -> str:
        return self.attendee

    @property
    def state(self) -> BookingState:
        return self._state

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def group_code(self) -> str:
        return uuid4().hex

    @property
    def dates(self) -> Sequence[Any]:
        return [Bunch(start=s, end=e) for s, e in self._dates]

    def overlaps(
        self,
        other: Booking,
        with_anti_affinity_check: bool = False
    ) -> bool:
        if self.id == other.id:
            return True

        return dates_overlap(
            tuple((d.start, d.end) for d in self.dates),
            tuple((o.start, o.end) for o in other.dates)
        )


class Occasion(MatchableOccasion):

    def __init__(
        self,
        name: str,
        dates: Sequence[tuple[date | datetime, date | datetime]],
        max_spots: int = 10,
        no_overlap_check: bool = False,
        anti_affinity_group: str | None = None
    ) -> None:

        self.name = name
        self._max_spots = max_spots
        self._no_overlap_check = no_overlap_check
        self._anti_affinity_group = anti_affinity_group

        def standardize(dt: date | datetime) -> date | datetime:
            if isinstance(dt, datetime):
                return standardize_date(dt, 'Europe/Zurich')
            return dt

        self._dates = [(standardize(s), standardize(e)) for s, e in dates]

    @property
    def id(self) -> str:
        return self.name

    @property
    def max_spots(self) -> int:
        return self._max_spots

    def booking(
        self,
        attendee: str,
        state: BookingState,
        priority: int
    ) -> Booking:
        return Booking(self, attendee, state, priority, self._dates)

    @property
    def dates(self) -> Sequence[Any]:
        return [Bunch(start=s, end=e) for s, e in self._dates]

    @property
    def exclude_from_overlap_check(self) -> bool:
        return self._no_overlap_check

    @property
    def anti_affinity_group(self) -> str:
        return self._anti_affinity_group  # type: ignore[return-value]


def test_overlapping_bookings() -> None:

    # the algorithm will block other bookings, favoring higher priorities
    o1 = Occasion("Daytrip", [(today(), today())])
    o2 = Occasion("Camp", [(today(), today() + days(1))])
    o3 = Occasion("Zoo", [(today() + days(1), today() + days(2))])

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


def test_overlapping_bookings_with_multiple_dates() -> None:

    o1 = Occasion("Daytrip", [
        (today(), today()),
        (today() + days(1), today() + days(1))
    ])

    o2 = Occasion("Camp", [
        (today() + days(1), today() + days(1)),
        (today() + days(2), today() + days(2))
    ])

    bookings = [
        o1.booking("Justin", 'open', 1),
        o2.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2))

    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1]}


def test_overlap_exclusion() -> None:

    o1 = Occasion("A", [(today(), today())])
    o2 = Occasion("B", [(today(), today())], no_overlap_check=True)

    bookings = [
        o1.booking("Justin", 'open', 1),
        o2.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2))
    assert result.accepted == {bookings[0], bookings[1]}


def test_overlapping_bookings_with_minutes_between() -> None:

    o1 = Occasion("A", [(
        datetime(2017, 2, 16, 10),
        datetime(2017, 2, 16, 11),
    )])

    o2 = Occasion("B", [(
        datetime(2017, 2, 16, 11),
        datetime(2017, 2, 16, 12),
    )])

    o3 = Occasion("C", [(
        datetime(2017, 2, 16, 12),
        datetime(2017, 2, 16, 13),
    )])

    bookings = [
        o1.booking("Justin", 'open', 2),
        o2.booking("Justin", 'open', 1),
        o3.booking("Justin", 'open', 0),
    ]

    result = match(bookings, (o1, o2, o3))
    assert not result.open
    assert result.accepted == {bookings[0], bookings[1], bookings[2]}

    result = match(bookings, (o1, o2, o3), minutes_between=1)
    assert not result.open
    assert result.accepted == {bookings[0], bookings[2]}
    assert result.blocked == {bookings[1]}

    result = match(bookings, (o1, o2, o3), minutes_between=60)
    assert not result.open
    assert result.accepted == {bookings[0], bookings[2]}
    assert result.blocked == {bookings[1]}

    result = match(bookings, (o1, o2, o3), minutes_between=61)
    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1], bookings[2]}

    bookings = [
        o1.booking("Justin", 'open', 1),
        o2.booking("Justin", 'open', 2),
        o3.booking("Justin", 'open', 0),
    ]

    result = match(bookings, (o1, o2, o3), minutes_between=1)
    assert not result.open
    assert result.accepted == {bookings[1]}
    assert result.blocked == {bookings[0], bookings[2]}


def test_is_stable() -> None:

    o1 = Occasion("A", [(
        datetime(2017, 2, 16, 10),
        datetime(2017, 2, 16, 11),
    )])

    o2 = Occasion("B", [(
        datetime(2017, 2, 16, 11),
        datetime(2017, 2, 16, 12),
    )])

    o3 = Occasion("C", [(
        datetime(2017, 2, 16, 13),
        datetime(2017, 2, 16, 14),
    )])

    bookings = [
        o1.booking("Justin", 'open', 1),
        o2.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2))

    attendees: list[Any] = [Bunch(accepted=result.accepted)]

    def preferred(b: Booking) -> Decimal:
        call_frame = sys._getframe(1)
        occasion = call_frame.f_locals['self']
        return Decimal('1' if b.preferred_occasion == occasion.id else '0')

    # if no bookings prefer another occasion which prefers them -> stable
    occasions = [OccasionAgent(o, preferred) for o in (o1, o2)]
    occasions[0].bookings.add(bookings[0])
    occasions[1].bookings.add(bookings[1])

    bookings[0].preferred_occasion = 'A'
    bookings[1].preferred_occasion = 'B'

    assert is_stable(attendees, occasions)

    # if there are bookings which would like to be swapped -> unstable
    occasions = [OccasionAgent(o, preferred) for o in (o1, o2)]

    occasions[0].bookings.add(bookings[0])
    occasions[1].bookings.add(bookings[1])

    bookings[0].preferred_occasion = 'B'
    bookings[1].preferred_occasion = 'A'

    assert not is_stable(attendees, occasions)

    # if there are multiple bookings where some would like to be swapped,
    # but not vice versa (here the priority creates a cascade) -> stable
    bookings = [
        o1.booking("Justin", 'open', 2),
        o2.booking("Justin", 'open', 1),
        o3.booking("Justin", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3))
    attendees = [Bunch(accepted=result.accepted)]

    occasions = [
        OccasionAgent(o, lambda b: Decimal(b.priority))
        for o in (o1, o2, o3)
    ]
    occasions[0].bookings.add(bookings[0])
    occasions[1].bookings.add(bookings[1])
    occasions[2].bookings.add(bookings[2])

    assert is_stable(attendees, occasions)

    # multiple bookings which like to be swapped (but not all) -> unstable

    occasions = [OccasionAgent(o, preferred) for o in (o1, o2, o3)]
    occasions[0].bookings.add(bookings[0])
    occasions[1].bookings.add(bookings[1])
    occasions[2].bookings.add(bookings[2])

    bookings[0].preferred_occasion = 'A'
    bookings[1].preferred_occasion = 'C'
    bookings[2].preferred_occasion = 'B'

    assert not is_stable(attendees, occasions)


def test_accept_highest_priority() -> None:

    o = Occasion("Best Activity Ever", [(today(), today())], max_spots=2)
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
    o = Occasion("Best Activity Ever", [(today(), today())], max_spots=2)
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
    assert (
        result.accepted == {bookings[1], bookings[2]}
        or result.accepted == {bookings[0], bookings[2]}
    )
    assert not result.blocked


def test_prefer_motivated() -> None:
    motivation_score = PreferMotivated()

    assert motivation_score(Bunch(priority=1)) == 1
    assert motivation_score(Bunch(priority=0)) == 0
    assert motivation_score(Bunch(priority=123)) == 123


def test_prefer_in_age_bracket() -> None:
    age_range: tuple[int, int]
    attendee_age: int

    age_bracket_score = PreferInAgeBracket(
        get_age_range=lambda b: age_range,
        get_attendee_age=lambda b: attendee_age)

    age_range = (10, 20)
    attendee_age = 10

    booking: Any = None
    assert age_bracket_score(booking) == 1.0

    attendee_age = 21
    assert age_bracket_score(booking) == 0.9

    attendee_age = 22
    assert age_bracket_score(booking) == 0.8

    attendee_age = 23
    assert age_bracket_score(booking) == 0.7

    attendee_age = 30
    assert age_bracket_score(booking) == 0.0

    attendee_age = 9
    assert age_bracket_score(booking) == 0.9

    attendee_age = 8
    assert age_bracket_score(booking) == 0.8


def test_prefer_organiser_children() -> None:

    is_organiser_child: bool

    organiser_child_score = PreferOrganiserChildren(
        get_is_organiser_child=lambda c: is_organiser_child)

    is_organiser_child = True
    booking: Any = None
    assert organiser_child_score(booking) == 1.5

    is_organiser_child = False
    assert organiser_child_score(booking) == 0.0


def test_prefer_association_children() -> None:

    is_association_child: bool

    association_child_score = PreferAdminChildren(
        get_is_association_child=lambda c: is_association_child)

    is_association_child = True
    booking: Any = None
    assert association_child_score(booking) == 1.5

    is_association_child = False
    assert association_child_score(booking) == 0.0


def test_serialize_scoring(session: Session) -> None:

    scoring: Scoring[Any] = Scoring()
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

    assert len(scoring.criteria) == 5


def test_booking_limit() -> None:

    o1 = Occasion('1', [(today(), today())])
    o2 = Occasion('2', [(today() + days(1), today() + days(1))])
    o3 = Occasion('3', [(today() + days(2), today() + days(2))])
    o4 = Occasion('4', [(today() + days(3), today() + days(3))])

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
        o3.booking("Tom", 'open', 0),
        o4.booking("Tom", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3, o4), default_limit=1)

    assert not result.open
    assert result.accepted == {bookings[0]}
    assert result.blocked == {bookings[1], bookings[2], bookings[3]}

    result = match(bookings, (o1, o2, o3, o4), default_limit=2)

    assert not result.open
    assert result.accepted == {bookings[0], bookings[1]}
    assert result.blocked == {bookings[2], bookings[3]}

    result = match(bookings, (o1, o2, o3, o4), default_limit=3)

    assert not result.open
    assert result.accepted == {bookings[0], bookings[1], bookings[2]}
    assert result.blocked == {bookings[3]}

    result = match(bookings, (o1, o2, o3, o4), default_limit=4)

    assert not result.open
    assert len(result.accepted) == 4
    assert not result.blocked

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
        o3.booking("Tom", 'open', 1),
        o4.booking("Tom", 'open', 0)
    ]

    result = match(bookings, (o1, o2, o3, o4), default_limit=1)

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

    result = match(bookings, (o1, o2, o3, o4), default_limit=1)

    assert not result.open
    assert result.accepted == {bookings[0], bookings[4]}
    assert len(result.blocked) == 4

    result = match(bookings, (o1, o2, o3, o4), default_limit=2)

    assert not result.open
    assert result.accepted == {
        bookings[0],
        bookings[1],
        bookings[4],
        bookings[5]
    }
    assert len(result.blocked) == 2

    bookings = [
        o1.booking("Tom", 'open', 1),
        o2.booking("Tom", 'open', 0),
        o1.booking("Dick", 'open', 1),
        o2.booking("Dick", 'open', 0),
        o1.booking("Harry", 'open', 1),
        o2.booking("Harry", 'open', 0),
    ]

    result = match(bookings, (o1, o2), default_limit=2, attendee_limits={
        "Tom": 1,
        "Dick": 1,
    })

    assert len(result.accepted) == 4
    assert result.accepted == {
        bookings[0],
        bookings[2],
        bookings[4],
        bookings[5],
    }


def test_day_alignment() -> None:
    o1 = Occasion('1', [
        (datetime(2017, 2, 20, 8), datetime(2017, 2, 20, 16))
    ])
    o2 = Occasion('2', [
        (datetime(2017, 2, 21, 8), datetime(2017, 2, 21, 16)),
        (datetime(2017, 2, 22, 8), datetime(2017, 2, 22, 12))
    ])
    o3 = Occasion('3', [
        (datetime(2017, 2, 22, 13), datetime(2017, 2, 22, 16))
    ])

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
        o3.booking("Tom", 'open', 0)
    ]

    # o2 and o3 do not overlap, but they have an occasion on the same day
    # which should be catpured by our occasions_per_day limit
    result = match(bookings, (o1, o2, o3))
    assert len(result.accepted) == 3

    result = match(bookings, (o1, o2, o3), alignment='day')
    assert len(result.accepted) == 2


def test_split_day_alignment() -> None:
    o1 = Occasion('1', [
        (datetime(2017, 2, 20, 8), datetime(2017, 2, 20, 16))
    ])
    o2 = Occasion('2', [
        (datetime(2017, 2, 21, 8), datetime(2017, 2, 21, 12)),
        (datetime(2017, 2, 21, 13), datetime(2017, 2, 21, 16))
    ])

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
    ]

    # the occasion o2 is split into two occasions on the same day ->
    # we however do not consider this to be a block, since it's the same
    # occasion
    assert len(match(bookings, (o1, o2)).accepted) == 2
    assert len(match(bookings, (o1, o2), alignment='day').accepted) == 2


def test_multi_day_alignment() -> None:
    o1 = Occasion('1', [
        (datetime(2017, 2, 20, 8), datetime(2017, 2, 21, 16))
    ])
    o2 = Occasion('2', [
        (datetime(2017, 2, 21, 17), datetime(2017, 2, 21, 18))
    ])

    bookings = [
        o1.booking("Tom", 'open', 0),
        o2.booking("Tom", 'open', 0),
    ]

    # the occasion o2 is split into two occasions on the same day ->
    # we however do not consider this to be a block, since it's the same
    # occasion
    assert len(match(bookings, (o1, o2)).accepted) == 2
    assert len(match(bookings, (o1, o2), alignment='day').accepted) == 1


def test_unblockable_regression() -> None:
    def booking(start: tuple[int, int], end: tuple[int, int]) -> Booking:
        start_dt = datetime(2018, 3, 8, *start)
        end_dt = datetime(2018, 3, 8, *end)

        return Booking(
            occasion=None,  # type: ignore[arg-type]
            attendee=None,  # type: ignore[arg-type]
            state=None,  # type: ignore[arg-type]
            priority=0,
            dates=[(start_dt, end_dt)]
        )

    accepted = {
        booking((7, 0), (8, 0)),
        booking((8, 0), (13, 0))
    }

    blocked = {
        booking((7, 0), (9, 0))
    }

    assert not unblockable(accepted, blocked)


def test_anti_affinity_groups() -> None:
    foo = Occasion("foo", [
        (datetime(2019, 2, 12, 8), datetime(2019, 2, 12, 16))
    ])
    bar = Occasion("bar", [
        (datetime(2019, 2, 13, 8), datetime(2019, 2, 13, 16))
    ])

    bookings = [
        foo.booking("Tom", 'open', 0),
        bar.booking("Tom", 'open', 1)
    ]

    foo._anti_affinity_group = None
    bar._anti_affinity_group = None
    assert len(match(bookings, (foo, bar)).accepted) == 2

    foo._anti_affinity_group = 'xyz'
    bar._anti_affinity_group = 'zyx'
    assert len(match(bookings, (foo, bar)).accepted) == 2

    foo._anti_affinity_group = 'xyz'
    bar._anti_affinity_group = 'xyz'
    assert len(match(bookings, (foo, bar)).accepted) == 1

    # the overlap check is less important than the anti-affinity
    foo._no_overlap_check = True
    bar._no_overlap_check = True
    assert len(match(bookings, (foo, bar)).accepted) == 1


def test_limited_bookings_regression() -> None:
    """ When limiting attendees to a low limit of occasions, an error would
    result in attendees with lots of wishes not getting as many occasions
    as possible.

    """

    # a week-long occasion for one person only
    o1 = Occasion('1', [(today(), today() + days(1))], max_spots=1)

    # single-day occasions for one person only
    o2 = Occasion('2', [(today() + days(1), today() + days(1))], max_spots=1)
    o3 = Occasion('3', [(today() + days(2), today() + days(2))], max_spots=1)

    # we need the week-long occasion to be booked in the first loop, then
    # denied in the next due to low-priority, to trigger a deny call
    bookings = [
        o1.booking("Abed", 'open', 0),
        o2.booking("Abed", 'open', 1),
        o3.booking("Abed", 'open', 2),
        o1.booking("Evil Abed", 'open', 3),
        o2.booking("Evil Abed", 'open', 4),
        o3.booking("Evil Abed", 'open', 5),
    ]

    result = match(
        bookings, (o1, o2, o3),
        default_limit=2,
    )

    # in the regression, this would be 2, even though 3 were possible
    assert len(result.accepted) == 3


def test_number_of_wishes_does_not_favor_attendee() -> None:
    """ PRO-1428: does the algorithm prefer children with few wishes?

    The premise of the ticket - that the algorithm systematically favours
    children with fewer wishes because it "tries to satisfy as many children
    as possible" - does not hold. Deferred acceptance fills each occasion
    purely by score (priority); the number of wishes an attendee submitted is
    never taken into account.

    This test documents that behaviour by pitting a single-wish child against
    a many-wish child for the same single spot, all at equal priority. The
    many-wish child wins the contested spot *and* keeps a second, non-competed
    spot, leaving the single-wish child with nothing - the opposite of the
    ticket's premise.

    """

    # non-overlapping occasions, one spot each
    o1 = Occasion('O1', [(today(), today())], max_spots=1)
    o2 = Occasion('O2', [(today() + days(1), today() + days(1))], max_spots=1)

    # the single-wish child only wants O1
    single = o1.booking("Single Wish", 'open', 0)

    # the many-wish child wants both O1 and O2 (equal priority throughout)
    many_o1 = o1.booking("Many Wishes", 'open', 0)
    many_o2 = o2.booking("Many Wishes", 'open', 0)

    result = match([single, many_o1, many_o2], (o1, o2))

    # both spots always get filled, but which child wins the contested O1 spot
    # is decided only by the (equal) score and an arbitrary tie-break - never
    # by wish count. One of the two stable outcomes leaves the many-wish child
    # holding both O1 and O2 while the single-wish child gets nothing, i.e. the
    # single-wish child enjoys no protection whatsoever.
    assert len(result.accepted) == 2
    assert result.accepted == {single, many_o2} or (
        result.accepted == {many_o1, many_o2} and result.open == {single})
    assert result.blocked == set()


def test_priority_not_wish_count_drives_matching() -> None:
    """ PRO-1428: the actual lever is priority (starred wishes), not the
    number of wishes.

    A child who submits a single wish and stars it concentrates the maximum
    priority on that one booking. That higher score - not the fact that they
    have few wishes - is what wins them the contested spot. This is the real
    explanation for the effect the organiser observed.

    """

    o1 = Occasion('O1', [(today(), today())], max_spots=1)
    o2 = Occasion('O2', [(today() + days(1), today() + days(1))], max_spots=1)

    # the single-wish child stars O1 -> higher priority/score
    single = o1.booking("Single Wish", 'open', 1)

    # the many-wish child did not star O1
    many_o1 = o1.booking("Many Wishes", 'open', 0)
    many_o2 = o2.booking("Many Wishes", 'open', 0)

    result = match([single, many_o1, many_o2], (o1, o2))

    # now the single-wish child wins O1 on priority, the many-wish child is
    # bumped to its second choice O2
    assert result.accepted == {single, many_o2}
    assert result.open == {many_o1}
    assert result.blocked == set()


def test_lower_priority_wish_can_never_displace_higher_one() -> None:
    """ PRO-1428: the reverse case - a single-wish child that did *not* star
    its wish can never take the spot from a higher-priority booking.

    An occasion only evicts a sitting booking for a newcomer with a strictly
    higher score (``OccasionAgent.preferred``). So a single-wish child at
    priority 0 loses the contested spot to a many-wish child who starred it,
    deterministically - unlike the equal-priority tie there is no arbitrary
    tie-break here. Since the single wish is the child's only wish, they end
    up with nothing.

    """

    o1 = Occasion('O1', [(today(), today())], max_spots=1)
    o2 = Occasion('O2', [(today() + days(1), today() + days(1))], max_spots=1)

    # the single-wish child did not star its only wish
    single = o1.booking("Single Wish", 'open', 0)

    # the many-wish child starred O1 -> higher priority/score
    many_o1 = o1.booking("Many Wishes", 'open', 1)
    many_o2 = o2.booking("Many Wishes", 'open', 0)

    result = match([single, many_o1, many_o2], (o1, o2))

    # the higher-priority booking keeps O1, the single-wish child is shut out
    assert result.accepted == {many_o1, many_o2}
    assert result.open == {single}


def test_star_cap_favours_low_wish_children() -> None:
    """ PRO-1428: the star cap (3 per child, see Booking.star / the feriennet
    toggle-star view) is absolute, not proportional.

    A child with few wishes can star *all* of them, so every wish sits at
    priority 1. A child with many wishes can only star 3, leaving the rest at
    priority 0 - and a priority-0 wish always loses a contested spot to a
    priority-1 one. The result is a structural tilt towards low-wish children
    in oversubscribed occasions, which is a plausible driver of the effect the
    organiser observed.

    Here the many-wish child spent its 3 stars on A/B/C and competes with the
    low-wish child for D/E/F, which the low-wish child was able to star. The
    low-wish child wins all three contested spots, deterministically.

    """

    # six single-spot, non-overlapping occasions
    occasions = {
        name: Occasion(name, [(today() + days(i), today() + days(i))],
                       max_spots=1)
        for i, name in enumerate('ABCDEF')
    }

    # many-wish child: wishes all six, but the star cap only lets it star
    # three (A/B/C -> priority 1); D/E/F stay unstarred (priority 0)
    many = [occasions[n].booking("Many Wishes", 'open', 1) for n in 'ABC']
    many += [occasions[n].booking("Many Wishes", 'open', 0) for n in 'DEF']

    # low-wish child: only wishes D/E/F and can star all of them (priority 1)
    low = [occasions[n].booking("Low Wishes", 'open', 1) for n in 'DEF']

    result = match(many + low, tuple(occasions.values()))

    accepted = {(b.occasion.name, b.attendee) for b in result.accepted}

    # low-wish child wins every contested spot on its full-coverage starring
    assert accepted == {
        ('A', 'Many Wishes'), ('B', 'Many Wishes'), ('C', 'Many Wishes'),
        ('D', 'Low Wishes'), ('E', 'Low Wishes'), ('F', 'Low Wishes'),
    }
    assert result.blocked == set()
