import pytest
import sqlalchemy
import transaction

from datetime import datetime
from onegov.activity import ActivityCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity.models import DAYS
from onegov.activity.models import Booking
from pytz import utc
from sedate import replace_timezone


def test_add_activity(session, owner):

    collection = ActivityCollection(session)
    collection.add(
        title="Visit the Butcher",
        username=owner.username,
        lead="Come visit the butcher with us and kill your own baby pig",
        text="<h1>Babe was such an overrated movie</h1>",
        tags=('butcher', 'killing', 'blood', 'fun'),
    )

    activity = collection.by_name('visit-the-butcher')
    assert activity.title == "Visit the Butcher"
    assert activity.username == owner.username
    assert activity.reporter == owner.username
    assert activity.lead.startswith("Come visit the butcher")
    assert activity.text.startswith("<h1>Babe was such a")
    assert activity.tags == {'butcher', 'killing', 'blood', 'fun'}


def test_unique_activity(session, owner):

    collection = ActivityCollection(session)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads'

    collection.add("Möped Lads", username=owner.username)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads-1'

    collection.add("Möped Lads", username=owner.username)
    assert collection.get_unique_name("Möped Lads") == 'moeped-lads-2'


def test_activity_pagination(session, owner):

    collection = ActivityCollection(session)

    for i in range(0, 20):
        collection.add(
            title='{:02d}'.format(i),
            username=owner.username
        )

    collection = collection.page_by_index(0)
    assert [a.title for a in collection.batch] == [
        "00", "01", "02", "03", "04", "05", "06", "07", "08", "09"
    ]

    collection = collection.page_by_index(1)
    assert [a.title for a in collection.batch] == [
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"
    ]


def test_activity_order(session, owner):

    collection = ActivityCollection(session)
    collection.add(title="Ä", username=owner.username)
    collection.add(title="B", username=owner.username)
    collection.add(title="C", username=owner.username)

    assert [a.title for a in collection.query().all()] == ["Ä", "B", "C"]


def test_activity_states(session, owner):

    c = ActivityCollection(session)
    c.add("A", username=owner.username)
    c.add("B", username=owner.username).propose()
    c.add("C", username=owner.username).propose().accept()
    c.add("D", username=owner.username).propose().deny()
    c.add("E", username=owner.username).propose().accept().archive()

    c.states = ('preview', )
    assert c.query().count() == 1

    c.states = ('preview', 'proposed')
    assert c.query().count() == 2

    c.states = ('preview', 'proposed', 'accepted')
    assert c.query().count() == 3

    c.states = ('preview', 'proposed', 'accepted', 'denied')
    assert c.query().count() == 4

    c.states = ('preview', 'proposed', 'accepted', 'denied', 'archived')
    assert c.query().count() == 5

    c.states = None
    assert c.query().count() == 5


def test_activity_used_tags(session, owner):

    c = ActivityCollection(session)

    activities = (
        c.add("Paintball", username=owner.username, tags=('sport', 'fun')),
        c.add("Dancing", username=owner.username, tags=('dance', 'fun'))
    )

    assert c.used_tags == {'sport', 'dance', 'fun'}

    c.states = ('proposed', )

    assert c.used_tags == {'sport', 'dance', 'fun'}

    activities[0].propose()

    assert c.used_tags == {'sport', 'dance', 'fun'}

    class LimitedActivityCollection(ActivityCollection):

        def query_base(self):
            return self.session.query(self.model_class).filter(
                self.model_class.state == 'proposed')

    c = LimitedActivityCollection(session)
    assert c.used_tags == {'sport', 'fun'}


def test_occasion_collection(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        location="Lucerne",
        age=(6, 9),
        spots=(2, 10),
        note="Bring game-face",
        activity=activities.add("Sport", username=owner.username)
    )

    assert tournament.start == datetime(2016, 10, 4, 11, tzinfo=utc)
    assert tournament.end == datetime(2016, 10, 4, 12, tzinfo=utc)
    assert tournament.timezone == "Europe/Zurich"
    assert tournament.location == "Lucerne"
    assert tournament.note == "Bring game-face"
    assert tournament.activity_id == activities.query().first().id

    # postgres ranges are coeced into half-open intervals
    assert tournament.age.lower == 6
    assert tournament.age.upper == 10
    assert tournament.spots.lower == 2
    assert tournament.spots.upper == 11

    transaction.commit()

    tournament = occasions.query().first()
    assert tournament.age.lower == 6
    assert tournament.age.upper == 10
    assert tournament.spots.lower == 2
    assert tournament.spots.upper == 11


def test_occasions_daterange_constraint(session, owner):
    sport = ActivityCollection(session).add("Sport", username=owner.username)
    sport.occasions.append(Occasion(
        start=replace_timezone(datetime(2020, 10, 10), 'Europe/Zurich'),
        end=replace_timezone(datetime(2010, 10, 10), 'Europe/Zurich'),
        timezone='Europe/Zurich'
    ))

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        session.flush()


def test_no_orphan_bookings(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username)
    )

    tournament.bookings.append(Booking(
        username=owner.username,
        last_name='Muster',
        first_name='Peter'
    ))

    session.flush()

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        occasions.delete(tournament)


def test_no_orphan_occasions(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username)
    )

    tournament.bookings.append(Booking(
        username=owner.username,
        last_name='Muster',
        first_name='Peter'
    ))

    session.flush()

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        activities.delete(activities.query().first())


def test_occasion_durations(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)

    assert not DAYS.has(retreat.durations, DAYS.half)
    assert not DAYS.has(retreat.durations, DAYS.full)
    assert not DAYS.has(retreat.durations, DAYS.many)

    # add an occasion that last half a day
    monday = occasions.add(
        start=datetime(2016, 10, 3, 12),
        end=datetime(2016, 10, 3, 16),
        timezone="Europe/Zurich",
        activity=retreat
    )
    transaction.commit()

    retreat = activities.query().first()
    assert DAYS.has(retreat.durations, DAYS.half)
    assert not DAYS.has(retreat.durations, DAYS.full)
    assert not DAYS.has(retreat.durations, DAYS.many)

    # add another half a day occasion
    tuesday = occasions.add(
        start=datetime(2016, 10, 4, 12),
        end=datetime(2016, 10, 4, 16),
        timezone="Europe/Zurich",
        activity=retreat
    )
    transaction.commit()

    retreat = activities.query().first()
    assert DAYS.has(retreat.durations, DAYS.half)
    assert not DAYS.has(retreat.durations, DAYS.full)
    assert not DAYS.has(retreat.durations, DAYS.many)

    # add a full day occasion
    wednesday = occasions.add(
        start=datetime(2016, 10, 5, 8),
        end=datetime(2016, 10, 5, 16),
        timezone="Europe/Zurich",
        activity=retreat
    )
    transaction.commit()

    retreat = activities.query().first()
    assert DAYS.has(retreat.durations, DAYS.half)
    assert DAYS.has(retreat.durations, DAYS.full)
    assert not DAYS.has(retreat.durations, DAYS.many)

    # add a multi day occasion
    weekend = occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        timezone="Europe/Zurich",
        activity=retreat
    )
    transaction.commit()

    retreat = activities.query().first()
    assert DAYS.has(retreat.durations, DAYS.half)
    assert DAYS.has(retreat.durations, DAYS.full)
    assert DAYS.has(retreat.durations, DAYS.many)

    # remove a the first half-day occasion (nothing should change)
    occasions.delete(monday)
    transaction.commit()

    retreat = activities.query().first()
    assert DAYS.has(retreat.durations, DAYS.half)
    assert DAYS.has(retreat.durations, DAYS.full)
    assert DAYS.has(retreat.durations, DAYS.many)

    # remove the second half-day occasion (no more half-days)
    occasions.delete(tuesday)
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(retreat.durations, DAYS.half)
    assert DAYS.has(retreat.durations, DAYS.full)
    assert DAYS.has(retreat.durations, DAYS.many)

    # remove the full day occasion
    occasions.delete(wednesday)
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(retreat.durations, DAYS.half)
    assert not DAYS.has(retreat.durations, DAYS.full)
    assert DAYS.has(retreat.durations, DAYS.many)

    # remove the remaining occasion
    occasions.delete(weekend)
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(retreat.durations, DAYS.half)
    assert not DAYS.has(retreat.durations, DAYS.full)
    assert not DAYS.has(retreat.durations, DAYS.many)


def test_occasion_durations_query(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)
    meeting = activities.add("Management Meeting", username=owner.username)

    # the retreat lasts a weekend
    occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        timezone="Europe/Zurich",
        activity=retreat
    )

    # the meeting has a day and a half-day occasion
    occasions.add(
        start=datetime(2016, 10, 10, 8),
        end=datetime(2016, 10, 10, 12),
        timezone="Europe/Zurich",
        activity=meeting
    )

    occasions.add(
        start=datetime(2016, 10, 11, 8),
        end=datetime(2016, 10, 11, 16),
        timezone="Europe/Zurich",
        activity=meeting
    )

    transaction.commit()

    assert activities.query().count() == 2
    assert activities.for_filter(duration=DAYS.half).query().count() == 1
    assert activities.for_filter(duration=DAYS.full).query().count() == 1
    assert activities.for_filter(duration=DAYS.many).query().count() == 1

    assert activities\
        .for_filter(duration=DAYS.half)\
        .for_filter(duration=DAYS.full)\
        .query().count() == 1

    assert activities\
        .for_filter(duration=DAYS.half)\
        .for_filter(duration=DAYS.full)\
        .for_filter(duration=DAYS.many)\
        .query().count() == 2

    assert activities\
        .for_filter(duration=DAYS.half)\
        .for_filter(duration=DAYS.many)\
        .query().count() == 2


def test_occasion_ages(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)
    meeting = activities.add("Management Meeting", username=owner.username)

    occasions.add(
        start=datetime(2017, 2, 18, 8),
        end=datetime(2017, 2, 18, 17),
        timezone="Europe/Zurich",
        age=(1, 10),
        activity=retreat
    )
    occasions.add(
        start=datetime(2018, 2, 19, 8),
        end=datetime(2018, 2, 19, 17),
        timezone="Europe/Zurich",
        age=(10, 20),
        activity=meeting
    )

    transaction.commit()

    assert activities.for_filter(age_range=(1, 20)).query().count() == 2
    assert activities.for_filter(age_range=(1, 10)).query().count() == 2
    assert activities.for_filter(age_range=(10, 20)).query().count() == 2
    assert activities.for_filter(age_range=(1, 5)).query().count() == 1
    assert activities.for_filter(age_range=(15, 20)).query().count() == 1
    assert activities.for_filter(age_range=(20, 21)).query().count() == 1
    assert activities.for_filter(age_range=(21, 22)).query().count() == 0
    assert activities.for_filter(age_range=(4, 4)).query().count() == 1
    assert activities.for_filter(age_range=(15, 15)).query().count() == 1
    assert activities.for_filter(age_range=(0, 0)).query().count() == 0
    assert activities.for_filter(age_range=(1, 5))\
        .for_filter(age_range=(5, 15)).query().count() == 2

    assert activities.for_filter(age_range=(1, 1)).contains_age_range((0, 2))
    assert activities.for_filter(age_range=(1, 1)).contains_age_range((1, 1))
    assert activities.for_filter(age_range=(1, 1)).contains_age_range((1, 2))

    assert not activities.for_filter(age_range=(1, 1))\
        .contains_age_range((0, 0))

    assert not activities.for_filter(age_range=(1, 10))\
        .contains_age_range((20, 30))

    assert activities\
        .for_filter(age_range=(1, 10))\
        .for_filter(age_range=(20, 30))\
        .contains_age_range((10, 15))

    assert activities\
        .for_filter(age_range=(1, 10))\
        .for_filter(age_range=(20, 30))\
        .contains_age_range((10, 20))

    assert not activities\
        .for_filter(age_range=(1, 10))\
        .for_filter(age_range=(20, 30))\
        .contains_age_range((15, 16))


def test_occasion_owners(session, owner, secondary_owner):

    activities = ActivityCollection(session)

    activities.add("Management Retreat", username=owner.username)
    activities.add("Management Meeting", username=secondary_owner.username)

    transaction.commit()

    assert activities\
        .for_filter(owner='owner@example.org')\
        .query().count() == 1
    assert activities\
        .for_filter(owner='owner@example.org')\
        .for_filter(owner='secondary@example.org')\
        .query().count() == 2

    assert activities\
        .for_filter(owner='secondary@example.org')\
        .query().count() == 1
