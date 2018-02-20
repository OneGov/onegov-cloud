import random

from datetime import date, timedelta
from freezegun import freeze_time
from functools import partial
from onegov.activity.matching import deferred_acceptance_from_database
from onegov.activity.matching import Scoring
from onegov.activity.matching import PreferAdminChildren
from onegov.activity.matching import PreferOrganiserChildren
from onegov.activity.matching import PreferInAgeBracket
from onegov.core.utils import Bunch
from psycopg2.extras import NumericRange
from uuid import uuid4


match = partial(
    deferred_acceptance_from_database,
    stability_check=True,
    validity_check=True,
    hard_budget=True
)


def new_occasion(collections, period, offset, length,
                 activity_name="foobar", username="owner@example.org",
                 spots=(0, 10), age=(0, 10)):

    activity = collections.activities.by_name(activity_name)

    if not activity:
        activity = collections.activities.add(activity_name, username=username)

    return collections.occasions.add(
        start=period.prebooking_start + timedelta(days=offset),
        end=period.prebooking_start + timedelta(days=offset + length),
        timezone="Europe/Zurich",
        activity=activity,
        period=period,
        spots=spots,
        age=age
    )


def new_attendee(collections, name=None, birth_date=None, user=None):

    return collections.attendees.add(
        name=name or uuid4().hex,
        birth_date=birth_date or date(2000, 1, 1),
        user=user or Bunch(username="owner@example.org"),
        gender=random.choice(('male', 'female')))


def test_simple_match(session, owner, collections, prebooking_period):
    """ Tests the matching of two occasions on the same activity with no
    conflicting signups.

    """

    o1 = new_occasion(collections, prebooking_period, 0, 1, spots=(0, 1))
    o2 = new_occasion(collections, prebooking_period, 0, 1, spots=(0, 1))

    a1 = new_attendee(collections)
    a2 = new_attendee(collections)

    collections.bookings.add(owner, a1, o1)
    collections.bookings.add(owner, a2, o2)

    # multiple runs lead to the same result
    for i in range(0, 2):
        match(session, prebooking_period.id)

        bookings = collections.bookings.query().all()

        assert len(bookings) == 2

        assert bookings[0].state == 'accepted'
        assert bookings[1].state == 'accepted'

        assert a1.happiness(prebooking_period.id) == 1.0
        assert a2.happiness(prebooking_period.id) == 1.0


def test_changing_priorities(session, owner, collections, prebooking_period):
    """ Makes sure that changing priorities lead to a changing match. """

    # only one available spot
    o = new_occasion(collections, prebooking_period, 0, 1, spots=(0, 1))

    # two attendees
    a1 = new_attendee(collections)
    a2 = new_attendee(collections)

    # one booking is prioritised
    b1 = collections.bookings.add(owner, a1, o)
    b2 = collections.bookings.add(owner, a2, o)

    b1.priority = 1
    b2.priority = 0

    match(session, prebooking_period.id)

    assert b1.state == 'accepted'
    assert b2.state == 'open'

    b1.priority = 0
    b2.priority = 1

    match(session, prebooking_period.id)

    assert b1.state == 'open'
    assert b2.state == 'accepted'


@freeze_time("2016-11-22")
def test_prefer_in_age_bracket(session, owner, collections, prebooking_period):
    o = new_occasion(
        collections, prebooking_period, 0, 1, spots=(0, 1), age=(10, 20))

    # two attendees, one is inside the age bracket, the other is outside
    a1 = new_attendee(collections, birth_date=date(1980, 11, 22))
    a2 = new_attendee(collections, birth_date=date(2000, 11, 22))

    b1 = collections.bookings.add(owner, a1, o)
    b2 = collections.bookings.add(owner, a2, o)

    match(session, prebooking_period.id, score_function=Scoring(
        criteria=[PreferInAgeBracket.from_session(session)]
    ))

    assert b1.state == 'open'
    assert b2.state == 'accepted'

    o.age = NumericRange(20, 50)

    match(session, prebooking_period.id, score_function=Scoring(
        criteria=[PreferInAgeBracket.from_session(session)]
    ))

    assert b1.state == 'accepted'
    assert b2.state == 'open'


def test_prefer_organisers_of_period(session, owner, secondary_owner,
                                     collections, prebooking_period,
                                     inactive_period):

    # if someone was an organiser in another period, it doesn't count
    new_occasion(collections, inactive_period, 0, 1, spots=(0, 1),
                 username=secondary_owner.username, activity_name="old")

    # what counts is being an organiser in the current period
    o = new_occasion(collections, prebooking_period, 0, 1, spots=(0, 1),
                     username=owner.username, activity_name="new")

    # two attendees, one belonging to an organiser
    a1 = new_attendee(collections, user=owner)
    a2 = new_attendee(collections, user=secondary_owner)

    b1 = collections.bookings.add(owner, a1, o)
    b2 = collections.bookings.add(secondary_owner, a2, o)

    match(session, prebooking_period.id, score_function=Scoring(
        criteria=[PreferOrganiserChildren.from_session(session)]
    ))

    assert b1.state == 'accepted'
    assert b2.state == 'open'


def test_prefer_organisers_over_members(session, owner, member,
                                        collections, prebooking_period):

    # organisers > members
    o = new_occasion(collections, prebooking_period, 0, 1, spots=(0, 1),
                     username=owner.username)

    # two attendees, one belonging to an organiser
    a1 = new_attendee(collections, user=member)
    a2 = new_attendee(collections, user=owner)

    b1 = collections.bookings.add(member, a1, o)
    b2 = collections.bookings.add(owner, a2, o)

    match(session, prebooking_period.id, score_function=Scoring(
        criteria=[PreferOrganiserChildren.from_session(session)]
    ))

    assert b1.state == 'open'
    assert b2.state == 'accepted'


def test_prefer_admin_children(session, owner, member, collections,
                               prebooking_period):

    owner.role = 'admin'

    o = new_occasion(collections, prebooking_period, 0, 1, spots=(0, 1))

    # two attendees, one belonging to an association member (editor)
    a1 = new_attendee(collections, user=member)
    a2 = new_attendee(collections, user=owner)

    b1 = collections.bookings.add(owner, a1, o)
    b2 = collections.bookings.add(member, a2, o)

    match(session, prebooking_period.id, score_function=Scoring(
        criteria=[PreferAdminChildren.from_session(session)]
    ))

    assert b1.state == 'accepted'
    assert b2.state == 'open'


def test_interleaved_dates(session, owner, collections, prebooking_period):

    o1 = new_occasion(collections, prebooking_period, 0, 1)
    collections.occasions.add_date(
        o1,
        o1.dates[0].end + timedelta(days=2, seconds=1),
        o1.dates[0].end + timedelta(days=3),
        o1.dates[0].timezone
    )

    o2 = new_occasion(collections, prebooking_period, 2, 1)
    collections.occasions.add_date(
        o2,
        o2.dates[0].end + timedelta(days=3, seconds=1),
        o2.dates[0].end + timedelta(days=4),
        o2.dates[0].timezone
    )

    a1 = new_attendee(collections, user=owner)

    b1 = collections.bookings.add(owner, a1, o1, priority=1)
    b2 = collections.bookings.add(owner, a1, o2, priority=0)

    match(session, prebooking_period.id)

    assert b1.state == 'accepted'
    assert b2.state == 'accepted'


def test_overlapping_dates(session, owner, collections, prebooking_period):

    # only the second dates overlap
    o1 = new_occasion(collections, prebooking_period, 0, 1)
    collections.occasions.add_date(
        o1,
        o1.dates[0].end + timedelta(days=3, seconds=1),
        o1.dates[0].end + timedelta(days=5),
        o1.dates[0].timezone
    )

    o2 = new_occasion(collections, prebooking_period, 2, 1)
    collections.occasions.add_date(
        o2,
        o2.dates[0].end + timedelta(days=2, seconds=1),
        o2.dates[0].end + timedelta(days=3),
        o2.dates[0].timezone
    )

    a1 = new_attendee(collections, user=owner)

    b1 = collections.bookings.add(owner, a1, o1, priority=1)
    b2 = collections.bookings.add(owner, a1, o2, priority=0)

    match(session, prebooking_period.id)

    assert b1.state == 'accepted'
    assert b2.state == 'blocked'


def test_alignment(session, owner, collections, prebooking_period):

    o1 = new_occasion(collections, prebooking_period, 0, 0.5)
    o2 = new_occasion(collections, prebooking_period, 0.5, 0.5)

    a1 = new_attendee(collections, user=owner)

    b1 = collections.bookings.add(owner, a1, o1, priority=1)
    b2 = collections.bookings.add(owner, a1, o2, priority=0)

    match(session, prebooking_period.id)

    assert b1.state == 'accepted'
    assert b2.state == 'accepted'

    prebooking_period.alignment = 'day'

    match(session, prebooking_period.id)
    assert b1.state == 'accepted'
    assert b2.state == 'blocked'
