import pytest
import sqlalchemy
import transaction

from datetime import datetime, date
from freezegun import freeze_time
from onegov.activity import ActivityCollection
from onegov.activity import Attendee
from onegov.activity import AttendeeCollection
from onegov.activity import Occasion
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.activity import BookingCollection
from onegov.activity.models import DAYS
from onegov.core.utils import Bunch
from pytz import utc
from sedate import replace_timezone
from uuid import uuid4


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

    transaction.commit()

    c = LimitedActivityCollection(session)
    assert c.used_tags == {'sport', 'fun'}


def test_occasions(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)
    periods = PeriodCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        location="Lucerne",
        age=(6, 9),
        spots=(2, 10),
        note="Bring game-face",
        activity=activities.add("Sport", username=owner.username),
        period=period
    )

    transaction.commit()

    tournament = occasions.query().one()
    assert tournament.start == datetime(2016, 10, 4, 11, tzinfo=utc)
    assert tournament.end == datetime(2016, 10, 4, 12, tzinfo=utc)
    assert tournament.timezone == "Europe/Zurich"
    assert tournament.location == "Lucerne"
    assert tournament.note == "Bring game-face"
    assert tournament.activity_id == activities.query().first().id
    assert tournament.period_id == periods.query().first().id
    assert tournament.active

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

    # the occasions active flag is bound to the period's activity
    periods.query().first().deactivate()
    transaction.commit()
    assert not occasions.query().first().active

    periods.query().first().activate()
    transaction.commit()
    assert occasions.query().first().active


def test_profiles(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)
    periods = PeriodCollection(session)

    sport = activities.add("Sport", username=owner.username)

    autumn = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31))
    )

    winter = periods.add(
        title="Winter 2016",
        prebooking=(datetime(2016, 11, 1), datetime(2016, 11, 30)),
        execution=(datetime(2016, 12, 1), datetime(2016, 12, 31))
    )

    autumn_id, winter_id = autumn.id, winter.id

    # 2 occasions in autumn
    occasions.add(
        start=datetime(2016, 10, 1, 13),
        end=datetime(2016, 10, 1, 14),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=autumn
    )

    occasions.add(
        start=datetime(2016, 10, 1, 13),
        end=datetime(2016, 10, 1, 14),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=autumn
    )

    # 1 occasion in winter
    occasions.add(
        start=datetime(2016, 12, 1, 13),
        end=datetime(2016, 12, 1, 14),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=winter
    )

    transaction.commit()

    sport = activities.query().first()
    assert len(sport.period_ids) == 2
    assert winter_id in sport.period_ids
    assert autumn_id in sport.period_ids

    # drop the winter occasion
    occasions.delete(
        occasions.query().filter(Occasion.period_id == winter_id).first())
    transaction.commit()

    sport = activities.query().first()
    assert len(sport.period_ids) == 1
    assert autumn_id in sport.period_ids


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
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username),
        period=period
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    bookings.add(owner, dustin, tournament)

    transaction.commit()

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        occasions.delete(tournament)


def test_no_orphan_occasions(session, owner):

    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username),
        period=period
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    bookings.add(owner, dustin, tournament)

    session.flush()

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        activities.delete(activities.query().first())


def test_occasion_durations(session, owner):

    activities = ActivityCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)

    assert not DAYS.has(retreat.durations, DAYS.half)
    assert not DAYS.has(retreat.durations, DAYS.full)
    assert not DAYS.has(retreat.durations, DAYS.many)

    periods.add(
        title="2016",
        prebooking=(datetime(2015, 1, 1), datetime(2015, 12, 31)),
        execution=(datetime(2016, 1, 1), datetime(2016, 12, 31)),
        active=True
    )

    # add an occasion that last half a day
    monday = occasions.add(
        start=datetime(2016, 10, 3, 12),
        end=datetime(2016, 10, 3, 16),
        timezone="Europe/Zurich",
        activity=retreat,
        period=periods.active()
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
        activity=retreat,
        period=periods.active()
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
        activity=retreat,
        period=periods.active()
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
        activity=retreat,
        period=periods.active()
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
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)
    meeting = activities.add("Management Meeting", username=owner.username)

    periods.add(
        title="2016",
        prebooking=(datetime(2015, 1, 1), datetime(2015, 12, 31)),
        execution=(datetime(2016, 1, 1), datetime(2016, 12, 31)),
        active=True
    )

    # the retreat lasts a weekend
    occasions.add(
        start=datetime(2016, 10, 8, 8),
        end=datetime(2016, 10, 9, 16),
        timezone="Europe/Zurich",
        activity=retreat,
        period=periods.active()
    )

    # the meeting has a day and a half-day occasion
    occasions.add(
        start=datetime(2016, 10, 10, 8),
        end=datetime(2016, 10, 10, 12),
        timezone="Europe/Zurich",
        activity=meeting,
        period=periods.active()
    )

    occasions.add(
        start=datetime(2016, 10, 11, 8),
        end=datetime(2016, 10, 11, 16),
        timezone="Europe/Zurich",
        activity=meeting,
        period=periods.active()
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
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)
    meeting = activities.add("Management Meeting", username=owner.username)

    periods.add(
        title="2016",
        prebooking=(datetime(2015, 1, 1), datetime(2015, 12, 31)),
        execution=(datetime(2016, 1, 1), datetime(2016, 12, 31)),
        active=True
    )

    occasions.add(
        start=datetime(2017, 2, 18, 8),
        end=datetime(2017, 2, 18, 17),
        timezone="Europe/Zurich",
        age=(1, 10),
        activity=retreat,
        period=periods.active()
    )
    occasions.add(
        start=datetime(2018, 2, 19, 8),
        end=datetime(2018, 2, 19, 17),
        timezone="Europe/Zurich",
        age=(10, 20),
        activity=meeting,
        period=periods.active()
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


def test_attendee_age(session, owner):

    def age(years):
        return date.today().replace(year=date.today().year - years)

    attendees = AttendeeCollection(session)
    d = attendees.add(owner, "Dustin Henderson", age(13))
    m = attendees.add(owner, "Mike Wheeler", age(14))

    assert d.age == 13
    assert m.age == 14

    assert attendees.query().filter(Attendee.age <= 13).count() == 1
    assert attendees.query().filter(Attendee.age <= 14).count() == 2


def test_booking_collection(session, owner):

    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username),
        period=periods.add(
            title="Autumn 2016",
            prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
            execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
            active=True
        )
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    bookings.add(owner, dustin, tournament)

    assert bookings.query().count() == 1
    assert bookings.for_period(Bunch(id=uuid4())).query().count() == 0
    assert bookings.for_username('foobar').query().count() == 0
    assert bookings.for_period(Bunch(id=uuid4())).count(owner.username) == 0
    assert bookings.booking_count(owner.username) == 1


def test_star_booking(session, owner):
    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    sport = activities.add("Sport", username=owner.username)

    autumn = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    s1 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=autumn
    )

    s2 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=autumn
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    b1 = bookings.add(owner, dustin, s1)
    b2 = bookings.add(owner, dustin, s2)

    assert b1.star(max_stars=1) is True
    assert b2.star(max_stars=1) is False

    assert b1.starred is True
    assert b2.starred is False


def test_booking_period_id_reference(session, owner):

    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    tournament = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username),
        period=period
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    bookings.add(owner, dustin, tournament)

    transaction.commit()

    assert bookings.query().first().period_id == period.id

    new = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=False
    )

    tournament = occasions.query().first()
    tournament.period_id = new.id

    transaction.commit()

    assert bookings.query().first().period_id == new.id


def test_happiness(session, owner):

    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    sport = activities.add("Sport", username=owner.username)

    o1 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period
    )

    o2 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period
    )

    o3 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    transaction.commit()

    def assert_happiness(period_id, value):

        def equal(result):
            if value is None:
                return result is None
            else:
                return round(result, 3) == value

        dustin = attendees.query().first()
        assert equal(dustin.happiness(period_id))

        q = attendees.query().with_entities(Attendee.happiness(period_id))
        assert equal(q.first().happiness)

    # no bookings yet
    assert_happiness(period.id, None)

    bookings.add(owner, dustin, o1)
    bookings.add(owner, dustin, o2)
    bookings.add(owner, dustin, o3)

    transaction.commit()

    # low priorities, all bookings accepted
    b1, b2, b3 = bookings.query().all()
    b1.state = 'accepted'
    b2.state = 'accepted'
    b3.state = 'accepted'

    transaction.commit()

    assert_happiness(period.id, 1.0)

    # high priorities, all bookings accepted
    b1, b2, b3 = bookings.query().all()
    b1.priority = 1
    b2.priority = 1
    b3.priority = 1

    transaction.commit()

    assert_happiness(period.id, 1.0)

    # low priorities denied, one high priority accepted
    b1, b2, b3 = bookings.query().all()
    b1.priority = 1
    b1.state = 'accepted'
    b2.priority = 0
    b2.state = 'open'
    b3.priority = 0
    b3.state = 'open'

    transaction.commit()

    assert_happiness(period.id, 0.5)

    # low priorities accepted, one high priority denied
    b1, b2, b3 = bookings.query().all()
    b1.priority = 1
    b1.state = 'open'
    b2.priority = 0
    b2.state = 'accepted'
    b3.priority = 0
    b3.state = 'accepted'

    transaction.commit()

    assert_happiness(period.id, 0.5)

    # 1/3 high priorities accepted
    b1, b2, b3 = bookings.query().all()
    b1.priority = 1
    b1.state = 'accepted'
    b2.priority = 1
    b2.state = 'open'
    b3.priority = 1
    b3.state = 'open'

    transaction.commit()

    assert_happiness(period.id, 0.333)

    # 1 extra high priority booking accepted
    b1, b2, b3 = bookings.query().all()
    b1.priority = 7
    b1.state = 'accepted'
    b2.priority = 0
    b2.state = 'open'
    b3.priority = 0
    b3.state = 'open'

    transaction.commit()

    assert_happiness(period.id, 0.8)


def test_attendees_count(session, owner):
    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    sport = activities.add("Sport", username=owner.username)

    o = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(1, 2)
    )

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8)
    )

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2002, 8, 8)
    )

    transaction.commit()

    assert occasions.query().one().attendee_count == 0
    assert not occasions.query().one().operable

    bookings.add(owner, a1, o)
    transaction.commit()

    assert occasions.query().one().attendee_count == 0
    assert not occasions.query().one().operable

    bookings.query().one().state = 'accepted'
    transaction.commit()

    assert occasions.query().one().attendee_count == 1
    assert occasions.query().one().operable

    bookings.add(owner, a2, o)
    transaction.commit()

    assert occasions.query().one().attendee_count == 1
    assert occasions.query().one().operable

    bookings.query().all()[0].state = 'accepted'
    bookings.query().all()[1].state = 'accepted'
    transaction.commit()

    assert occasions.query().one().attendee_count == 2
    assert occasions.query().one().operable

    session.delete(bookings.query().first())
    transaction.commit()

    assert occasions.query().one().attendee_count == 1
    assert occasions.query().one().operable

    bookings.query().one().state = 'open'

    assert occasions.query().one().attendee_count == 0
    assert not occasions.query().one().operable


def test_accept_booking(session, owner):
    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True,
    )

    sport = activities.add("Sport", username=owner.username)

    o1 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    o2 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2000, 1, 1)
    )

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2000, 1, 1)
    )

    a3 = attendees.add(
        user=owner,
        name="Eleven",
        birth_date=date(2000, 1, 1)
    )

    transaction.commit()

    # only works for confirmed periods
    with pytest.raises(RuntimeError) as e:
        bookings.accept_booking(bookings.add(owner, a1, o1))

    assert "The period has not yet been confirmed" in str(e)
    transaction.abort()

    periods.active().confirmed = True
    transaction.commit()

    # adding bookings works until the occasion is full
    bookings.accept_booking(bookings.add(owner, a1, o1))
    bookings.accept_booking(bookings.add(owner, a2, o1))

    with pytest.raises(RuntimeError) as e:
        bookings.accept_booking(bookings.add(owner, a3, o1))

    assert "The occasion is already full" in str(e)
    transaction.abort()

    # only open/denied bookings can be accepted this way
    booking = bookings.add(owner, a1, o1)

    for state in ('accepted', 'blocked', 'cancelled'):
        booking.state = state

        with pytest.raises(RuntimeError) as e:
            bookings.accept_booking(booking)

    transaction.abort()

    # we can't accept a booking that conflicts with another accepted booking
    bookings.accept_booking(bookings.add(owner, a1, o1))

    with pytest.raises(RuntimeError) as e:
        bookings.accept_booking(bookings.add(owner, a1, o2))

    assert "Conflict with booking" in str(e)
    transaction.abort()

    # other conflicting bookings are marked as blocked
    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o2)

    bookings.accept_booking(b1)

    assert b1.state == 'accepted'
    assert b2.state == 'blocked'

    b1.state = 'open'
    b2.state = 'open'

    bookings.accept_booking(b2)

    assert b2.state == 'accepted'
    assert b1.state == 'blocked'


def test_cancel_booking(session, owner):
    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True,
    )

    sport = activities.add("Sport", username=owner.username)

    o1 = occasions.add(
        start=datetime(2016, 10, 4, 10),
        end=datetime(2016, 10, 4, 12),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    o2 = occasions.add(
        start=datetime(2016, 10, 4, 11),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    o3 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 15),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    o4 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 15),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 1)
    )

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2000, 1, 1)
    )

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2000, 1, 1)
    )

    a3 = attendees.add(
        user=owner,
        name="Eleven",
        birth_date=date(2000, 1, 1)
    )

    transaction.commit()

    # only works for confirmed periods
    with pytest.raises(RuntimeError) as e:
        bookings.cancel_booking(bookings.add(owner, a1, o1))

    assert "The period has not yet been confirmed" in str(e)
    transaction.abort()

    periods.active().confirmed = True
    transaction.commit()

    # only works for accepted bookings
    with pytest.raises(RuntimeError) as e:
        bookings.cancel_booking(bookings.add(owner, a1, o1))

    assert "Only accepted bookings can be cancelled" in str(e)
    transaction.abort()

    # cancelling a booking will automatically accept the blocked ones
    # (this is run after matching, so we want to make sure the matching
    # is kept tight, with no unnecessarily open/denied bookings)
    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o2)
    b3 = bookings.add(owner, a1, o3)

    bookings.accept_booking(b2)

    assert b1.state == 'blocked'
    assert b2.state == 'accepted'
    assert b1.state == 'blocked'

    bookings.cancel_booking(b2)

    assert b1.state == 'accepted'
    assert b2.state == 'cancelled'
    assert b3.state == 'accepted'

    transaction.abort()

    # same, this time with only one overlap
    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o2)
    b3 = bookings.add(owner, a1, o3)

    bookings.accept_booking(b1)

    assert b1.state == 'accepted'
    assert b2.state == 'blocked'
    assert b3.state == 'open'

    bookings.cancel_booking(b1)

    assert b1.state == 'cancelled'
    assert b2.state == 'accepted'
    assert b3.state == 'blocked'

    transaction.abort()

    # if the occasions are already full, the state is going to be 'denied'
    bookings.accept_booking(bookings.add(owner, a2, o1))
    bookings.accept_booking(bookings.add(owner, a3, o1))

    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o2)

    bookings.accept_booking(b2)

    assert b1.state == 'blocked'
    assert b2.state == 'accepted'

    bookings.cancel_booking(b2)

    assert b1.state == 'denied'
    assert b2.state == 'cancelled'

    transaction.abort()

    # if the cancellation leads to open spots, other bookings are considered
    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a2, o1)
    b3 = bookings.add(owner, a3, o1)

    bookings.accept_booking(b1)
    bookings.accept_booking(b2)

    assert b1.state == 'accepted'
    assert b2.state == 'accepted'
    assert b3.state == 'open'

    bookings.cancel_booking(b2)

    assert b1.state == 'accepted'
    assert b2.state == 'cancelled'
    assert b3.state == 'accepted'

    transaction.abort()

    # make sure a cancellation doesn't lead to overbooking
    b1 = bookings.add(owner, a1, o4)
    b2 = bookings.add(owner, a2, o4, priority=1)
    b3 = bookings.add(owner, a3, o4)

    bookings.accept_booking(b1)

    assert b1.state == 'accepted'
    assert b2.state == 'open'
    assert b3.state == 'open'

    bookings.cancel_booking(b1)

    assert b1.state == 'cancelled'
    assert b2.state == 'accepted'
    assert b3.state == 'open'


def test_period_phases(session):
    periods = PeriodCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(date(2016, 9, 1), date(2016, 9, 30)),
        execution=(date(2016, 11, 1), date(2016, 11, 30)),
        active=False,
    )

    assert period.phase == 'inactive'

    period.active = True
    assert period.phase == 'wishlist'

    period.confirmed = True
    assert period.phase == 'booking'

    period.finalized = True

    with freeze_time('2016-10-31'):
        assert period.phase == 'payment'

    with freeze_time('2016-11-01'):
        assert period.phase == 'execution'

    with freeze_time('2016-12-01'):
        assert period.phase == 'archive'
