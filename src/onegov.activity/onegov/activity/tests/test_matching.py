from datetime import date, timedelta
from onegov.activity.matching import match_bookings_with_occasions
from onegov.core.utils import Bunch
from uuid import uuid4


def new_occasion(collections, period, offset, length,
                 activity_name="foobar", username="owner@example.org",
                 spots=(0, 10), age=(0, 10)):

    activity = collections.activities.by_name(activity_name)

    if not activity:
        activity = collections.activities.add(activity_name, username=username)

    return collections.occasions.add(
        start=period.prebooking_start + timedelta(days=offset),
        end=period.prebooking_end + timedelta(days=offset + length),
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
        user=user or Bunch(username="owner@example.org"))


def test_simple_match(session, owner, collections, prebooking_period):
    """ Tests the matching of two occasions on the same activity with no
    conflicting signups.

    """

    period = prebooking_period

    o1 = new_occasion(collections, period, 0, 1, spots=(0, 1))
    o2 = new_occasion(collections, period, 0, 1, spots=(0, 1))

    a1 = new_attendee(collections)
    a2 = new_attendee(collections)

    collections.bookings.add(owner, a1, o1)
    collections.bookings.add(owner, a2, o2)

    match_bookings_with_occasions(session, prebooking_period.id)

    bookings = collections.bookings.query().all()

    assert len(bookings) == 2

    assert bookings[0].state == 'accepted'
    assert bookings[1].state == 'accepted'

    assert a1.happiness(prebooking_period.id) == 1.0
    assert a2.happiness(prebooking_period.id) == 1.0
