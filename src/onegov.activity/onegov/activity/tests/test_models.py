import pytest
import sqlalchemy
import transaction

from datetime import datetime, date, timedelta
from freezegun import freeze_time
from onegov.activity import ActivityCollection
from onegov.activity import ActivityFilter
from onegov.activity import Attendee
from onegov.activity import AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import InvoiceItemCollection
from onegov.activity import Occasion, OccasionDate
from onegov.activity import OccasionCollection
from onegov.activity import Period
from onegov.activity import PeriodCollection
from onegov.activity import PublicationRequestCollection
from onegov.activity.models import DAYS
from onegov.core.utils import Bunch
from psycopg2.extras import NumericRange
from pytz import utc
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
    c.add("D", username=owner.username).propose().accept().archive()

    c.filter.states = ('preview', )
    assert c.query().count() == 1

    c.filter.states = ('preview', 'proposed')
    assert c.query().count() == 2

    c.filter.states = ('preview', 'proposed', 'accepted')
    assert c.query().count() == 3

    c.filter.states = ('preview', 'proposed', 'accepted', 'archived')
    assert c.query().count() == 4

    c.filter.states = None
    assert c.query().count() == 4


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
        meeting_point="Lucerne",
        age=(6, 9),
        spots=(2, 10),
        note="Bring game-face",
        activity=activities.add("Sport", username=owner.username),
        period=period
    )

    transaction.commit()

    tournament = occasions.query().one()
    assert tournament.dates[0].start == datetime(2016, 10, 4, 11, tzinfo=utc)
    assert tournament.dates[0].end == datetime(2016, 10, 4, 12, tzinfo=utc)
    assert tournament.dates[0].timezone == "Europe/Zurich"
    assert tournament.dates[0].duration_in_seconds == 3600
    assert tournament.meeting_point == "Lucerne"
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


def test_activity_date_ranges(session, owner, collections):
    sport = collections.activities.add("Sport", username=owner.username)
    police = collections.activities.add("Police", username=owner.username)

    period = collections.periods.add(
        title="Spring 2017",
        prebooking=(datetime(2017, 2, 1), datetime(2017, 2, 28)),
        execution=(datetime(2017, 3, 1), datetime(2017, 3, 31)),
        active=True
    )

    collections.occasions.add(
        start=datetime(2017, 3, 1, 10),
        end=datetime(2017, 3, 1, 12),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=period
    )

    collections.occasions.add(
        start=datetime(2017, 3, 1, 14),
        end=datetime(2017, 3, 1, 16),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=period
    )

    collections.occasions.add(
        start=datetime(2017, 3, 4, 8),
        end=datetime(2017, 3, 6, 16),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=period
    )

    collections.occasions.add(
        start=datetime(2017, 3, 6, 18),
        end=datetime(2017, 3, 8, 18),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=police,
        period=period
    )

    transaction.commit()

    a = collections.activities

    # toggle daterange on
    a = a.for_filter(daterange=(date(2017, 3, 1), date(2017, 3, 30)))
    assert a.query().count() == 2

    # toggle daterange off
    a = a.for_filter(daterange=(date(2017, 3, 1), date(2017, 3, 30)))
    assert a.query().count() == 2  # no filter -> show all
    assert not a.filter.dateranges

    # only include the first activity
    a = a.for_filter(daterange=(date(2017, 3, 1), date(2017, 3, 5)))
    assert a.query().count() == 1

    # include the second activity
    a = a.for_filter(daterange=(date(2017, 3, 7), date(2017, 3, 8)))
    assert a.query().count() == 2

    # exlucde the first activity
    a = a.for_filter(daterange=(date(2017, 3, 1), date(2017, 3, 5)))
    assert a.query().count() == 1


def test_activity_weekdays(session, owner, collections):
    sport = collections.activities.add("Sport", username=owner.username)
    police = collections.activities.add("Police", username=owner.username)

    period = collections.periods.add(
        title="Spring 2017",
        prebooking=(datetime(2017, 2, 1), datetime(2017, 2, 28)),
        execution=(datetime(2017, 5, 8), datetime(2017, 5, 21)),
        active=True
    )

    # Monday
    collections.occasions.add(
        start=datetime(2017, 5, 8, 10),
        end=datetime(2017, 5, 8, 12),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=period
    )

    # Tuesday
    collections.occasions.add(
        start=datetime(2017, 5, 9, 10),
        end=datetime(2017, 5, 9, 12),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=sport,
        period=period
    )

    # Tuesday - Wednesdy
    collections.occasions.add(
        start=datetime(2017, 5, 9, 18),
        end=datetime(2017, 5, 10, 18),
        timezone="Europe/Zurich",
        age=(6, 9),
        spots=(2, 10),
        activity=police,
        period=period
    )

    transaction.commit()

    a = collections.activities

    # monday
    a = a.for_filter(weekday=0)
    assert a.query().count() == 1

    # monday, tuesday
    a = a.for_filter(weekday=1)
    assert a.query().count() == 2

    # tuesday (negates monday)
    a = a.for_filter(weekday=0)
    assert a.query().count() == 2

    # tuesday, wednesday
    a = a.for_filter(weekday=2)
    assert a.query().count() == 2

    # wednesday (negates tuesday)
    a = a.for_filter(weekday=1)
    assert a.query().count() == 1


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
    period_ids = set(o.period_id for o in sport.occasions)

    assert len(period_ids) == 2
    assert winter_id in period_ids
    assert autumn_id in period_ids

    # drop the winter occasion
    occasions.delete(
        occasions.query().filter(Occasion.period_id == winter_id).first())
    transaction.commit()

    sport = activities.query().first()
    period_ids = set(o.period_id for o in sport.occasions)

    assert len(period_ids) == 1
    assert autumn_id in period_ids


def test_occasion_daterange_constraint(session, owner):
    period = PeriodCollection(session).add(
        title="Autumn 2016",
        prebooking=(datetime(2000, 1, 1), datetime(2000, 1, 1)),
        execution=(datetime(2001, 1, 1), datetime(2050, 12, 31))
    )

    sport = ActivityCollection(session).add("Sport", username=owner.username)
    occasions = OccasionCollection(session)

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        occasions.add(
            activity=sport,
            start=datetime(2020, 10, 10),
            end=datetime(2010, 10, 10),
            timezone='Europe/Zurich',
            period=period
        )


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
        birth_date=date(2002, 9, 8),
        gender='male'
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
        birth_date=date(2002, 9, 8),
        gender='male'
    )

    bookings.add(owner, dustin, tournament)

    session.flush()

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        activities.delete(activities.query().first())


def test_occasion_duration(session, owner):

    activities = ActivityCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)

    retreat = activities.add("Management Retreat", username=owner.username)

    def durations(activity):
        occasions = session.query(Occasion)\
            .with_entities(Occasion.duration)\
            .filter_by(activity_id=activity.id)

        return sum(set(o.duration for o in occasions))

    assert not DAYS.has(durations(retreat), DAYS.half)
    assert not DAYS.has(durations(retreat), DAYS.full)
    assert not DAYS.has(durations(retreat), DAYS.many)

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
    assert DAYS.has(durations(retreat), DAYS.half)
    assert not DAYS.has(durations(retreat), DAYS.full)
    assert not DAYS.has(durations(retreat), DAYS.many)

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
    assert DAYS.has(durations(retreat), DAYS.half)
    assert not DAYS.has(durations(retreat), DAYS.full)
    assert not DAYS.has(durations(retreat), DAYS.many)

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
    assert DAYS.has(durations(retreat), DAYS.half)
    assert DAYS.has(durations(retreat), DAYS.full)
    assert not DAYS.has(durations(retreat), DAYS.many)

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
    assert DAYS.has(durations(retreat), DAYS.half)
    assert DAYS.has(durations(retreat), DAYS.full)
    assert DAYS.has(durations(retreat), DAYS.many)

    # remove a the first half-day occasion (nothing should change)
    occasions.delete(monday)
    transaction.commit()

    retreat = activities.query().first()
    assert DAYS.has(durations(retreat), DAYS.half)
    assert DAYS.has(durations(retreat), DAYS.full)
    assert DAYS.has(durations(retreat), DAYS.many)

    # remove the second half-day occasion (no more half-days)
    occasions.delete(tuesday)
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(durations(retreat), DAYS.half)
    assert DAYS.has(durations(retreat), DAYS.full)
    assert DAYS.has(durations(retreat), DAYS.many)

    # remove the full day occasion
    occasions.delete(wednesday)
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(durations(retreat), DAYS.half)
    assert not DAYS.has(durations(retreat), DAYS.full)
    assert DAYS.has(durations(retreat), DAYS.many)

    # remove the remaining occasion
    occasions.delete(weekend)
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(durations(retreat), DAYS.half)
    assert not DAYS.has(durations(retreat), DAYS.full)
    assert not DAYS.has(durations(retreat), DAYS.many)

    # add an occasion with overnight stay which should be categorised as 'many'
    weekend = occasions.add(
        start=datetime(2018, 10, 1, 13, 30),
        end=datetime(2018, 10, 2, 10),
        timezone="Europe/Zurich",
        activity=retreat,
        period=periods.active()
    )
    transaction.commit()

    retreat = activities.query().first()
    assert not DAYS.has(durations(retreat), DAYS.half)
    assert not DAYS.has(durations(retreat), DAYS.full)
    assert DAYS.has(durations(retreat), DAYS.many)


def test_occasion_duration_with_multiple_dates(collections, owner):
    period = collections.periods.add(
        "Summer 2018", (
            datetime(2018, 5, 1),
            datetime(2018, 5, 31),
        ), (
            datetime(2018, 6, 1),
            datetime(2018, 6, 30)
        )
    )

    def with_dates(*ranges):
        a = collections.activities.add(uuid4().hex, username=owner.username)

        first, *rest = ranges

        occasion = collections.occasions.add(
            start=datetime(*first[0]),
            end=datetime(*first[1]),
            timezone='Europe/Zurich',
            activity=a,
            period=period
        )

        for s, e in rest:
            s, e = datetime(*s), datetime(*e)
            collections.occasions.add_date(occasion, s, e, 'Europe/Zurich')

        return occasion

    occasion = with_dates(
        ((2018, 6, 1, 6, 0), (2018, 6, 1, 7, 0)),
        ((2018, 6, 1, 8, 0), (2018, 6, 1, 9, 0))
    )

    assert occasion.duration == DAYS.half

    occasion = with_dates(
        ((2018, 6, 1, 10, 0), (2018, 6, 1, 12, 0)),
        ((2018, 6, 1, 14, 0), (2018, 6, 1, 16, 0))
    )

    assert occasion.duration == DAYS.half

    occasion = with_dates(
        ((2018, 6, 1, 10, 0), (2018, 6, 1, 12, 0)),
        ((2018, 6, 1, 14, 0), (2018, 6, 1, 17, 0))
    )

    assert occasion.duration == DAYS.full

    occasion = with_dates(
        ((2018, 6, 1, 10, 0), (2018, 6, 1, 12, 0)),
        ((2018, 6, 1, 22, 0), (2018, 6, 2, 2, 0))
    )

    assert occasion.duration == DAYS.full

    occasion = with_dates(
        ((2018, 6, 1, 10, 0), (2018, 6, 1, 12, 0)),
        ((2018, 6, 2, 14, 0), (2018, 6, 2, 16, 0))
    )

    assert occasion.duration == DAYS.many


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

    # add an occasion with overnight stay which should be categorised as 'many'
    assert activities.for_filter(duration=DAYS.half).query().count() == 1
    assert activities.for_filter(duration=DAYS.full).query().count() == 1
    assert activities.for_filter(duration=DAYS.many).query().count() == 1

    occasions.add(
        start=datetime(2018, 10, 1, 13, 30),
        end=datetime(2018, 10, 2, 10),
        timezone="Europe/Zurich",
        activity=meeting,
        period=periods.active()
    )
    transaction.commit()

    assert activities.for_filter(duration=DAYS.half).query().count() == 1
    assert activities.for_filter(duration=DAYS.full).query().count() == 1
    assert activities.for_filter(duration=DAYS.many).query().count() == 2


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

    assert activities.for_filter(age_range=(1, 1))\
        .filter.contains_age_range((0, 2))
    assert activities.for_filter(age_range=(1, 1))\
        .filter.contains_age_range((1, 1))
    assert activities.for_filter(age_range=(1, 1))\
        .filter.contains_age_range((1, 2))

    assert not activities.for_filter(age_range=(1, 1))\
        .filter.contains_age_range((0, 0))

    assert not activities.for_filter(age_range=(1, 10))\
        .filter.contains_age_range((20, 30))

    assert activities\
        .for_filter(age_range=(1, 10))\
        .for_filter(age_range=(20, 30))\
        .filter.contains_age_range((10, 15))

    assert activities\
        .for_filter(age_range=(1, 10))\
        .for_filter(age_range=(20, 30))\
        .filter.contains_age_range((10, 20))

    assert not activities\
        .for_filter(age_range=(1, 10))\
        .for_filter(age_range=(20, 30))\
        .filter.contains_age_range((15, 16))


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
    d = attendees.add(owner, "Dustin Henderson", age(13), 'male')
    m = attendees.add(owner, "Mike Wheeler", age(14), 'male')

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
        birth_date=date(2002, 9, 8),
        gender='male'
    )

    bookings.add(owner, dustin, tournament)

    assert bookings.query().count() == 1
    assert bookings.for_period(Bunch(id=uuid4())).query().count() == 0
    assert bookings.for_username('foobar').query().count() == 0
    assert bookings.for_period(Bunch(id=uuid4())).count(owner.username) == 0
    assert bookings.booking_count(owner.username) == 1


def test_star_nobble_booking(session, owner):
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

    s3 = occasions.add(
        start=datetime(2016, 10, 4, 13),
        end=datetime(2016, 10, 4, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=autumn
    )

    dustin = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2002, 9, 8),
        gender='male'
    )

    b1 = bookings.add(owner, dustin, s1)
    b2 = bookings.add(owner, dustin, s2)
    b3 = bookings.add(owner, dustin, s3)

    assert b1.star(max_stars=1) is True
    assert b2.star(max_stars=1) is False

    assert b1.starred is True
    assert b2.starred is False

    b1.nobble()
    assert b1.starred is True
    assert b1.nobbled is True

    b1.unstar()
    assert b1.starred is False
    assert b1.nobbled is True

    b1.unnobble()
    assert b1.starred is False
    assert b1.nobbled is False

    b1.nobble()
    b1.star()

    b2.unstar()
    b2.unnobble()

    b3.nobble()
    b3.unstar()

    q = session.query(Booking)
    assert q.filter(Booking.starred == True).count() == 1
    assert q.filter(Booking.nobbled == True).count() == 2

    b2.nobble()
    b2.star()

    assert q.filter(Booking.starred == True).count() == 2
    assert q.filter(Booking.nobbled == True).count() == 3

    b1.unstar()
    b1.unnobble()

    assert b1.priority == 0

    b1.star()

    assert b1.priority == 1

    b1.nobble()

    assert b1.priority == 3

    b1.unstar()

    assert b1.priority == 2


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
        birth_date=date(2002, 9, 8),
        gender='male'
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
        birth_date=date(2002, 9, 8),
        gender='male'
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
        birth_date=date(2002, 9, 8),
        gender='male'
    )

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2002, 8, 8),
        gender='male'
    )

    transaction.commit()

    q = occasions.query()

    assert q.one().attendee_count == 0
    assert q.one().available_spots == 2
    assert q.with_entities(Occasion.available_spots).one()[0] == 2

    assert not q.one().operable

    bookings.add(owner, a1, o)
    transaction.commit()

    assert q.one().attendee_count == 0
    assert q.one().available_spots == 2
    assert q.with_entities(Occasion.available_spots).one()[0] == 2
    assert not q.one().operable

    bookings.query().one().state = 'accepted'
    transaction.commit()

    assert q.one().attendee_count == 1
    assert q.one().available_spots == 1
    assert q.with_entities(Occasion.available_spots).one()[0] == 1
    assert q.one().operable

    bookings.add(owner, a2, o)
    transaction.commit()

    assert q.one().attendee_count == 1
    assert q.one().available_spots == 1
    assert q.with_entities(Occasion.available_spots).one()[0] == 1
    assert q.one().operable

    bookings.query().all()[0].state = 'accepted'
    bookings.query().all()[1].state = 'accepted'
    transaction.commit()

    assert q.one().attendee_count == 2
    assert q.one().available_spots == 0
    assert q.with_entities(Occasion.available_spots).one()[0] == 0
    assert q.one().operable

    session.delete(bookings.query().first())
    transaction.commit()

    assert q.one().attendee_count == 1
    assert q.one().available_spots == 1
    assert q.with_entities(Occasion.available_spots).one()[0] == 1
    assert q.one().operable

    bookings.query().one().state = 'open'

    assert q.one().attendee_count == 0
    assert q.one().available_spots == 2
    assert q.with_entities(Occasion.available_spots).one()[0] == 2
    assert not q.one().operable

    q.one().cancelled = True
    transaction.commit()

    assert q.one().attendee_count == 0
    assert q.one().available_spots == 0
    assert q.with_entities(Occasion.available_spots).one()[0] == 0


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

    o3 = occasions.add(
        start=datetime(2016, 10, 5, 13),
        end=datetime(2016, 10, 5, 14),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    o4 = occasions.add(
        start=datetime(2016, 10, 5, 15),
        end=datetime(2016, 10, 5, 16),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2000, 1, 1),
        gender='male'
    )

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2000, 1, 1),
        gender='male'
    )

    a3 = attendees.add(
        user=owner,
        name="Eleven",
        birth_date=date(2000, 1, 1),
        gender='female'
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

    transaction.abort()

    # if there's a booking limit we ensure it isn't violated
    period = periods.active()
    period.all_inclusive = True
    period.max_bookings_per_attendee = 1

    b1 = bookings.add(owner, a1, o1)
    bookings.accept_booking(b1)

    with pytest.raises(RuntimeError) as e:
        bookings.accept_booking(bookings.add(owner, a1, o3))

    assert "The booking limit has been reached" in str(e)

    transaction.abort()

    # there was a regression which lead to an error before the booking limit
    # was reached (accepted bookings were assumed to be in conflict)
    period = periods.active()
    period.all_inclusive = True
    period.max_bookings_per_attendee = 2

    b1 = bookings.add(owner, a1, o1)
    bookings.accept_booking(b1)
    b2 = bookings.add(owner, a1, o3)
    bookings.accept_booking(b2)

    with pytest.raises(RuntimeError) as e:
        bookings.accept_booking(bookings.add(owner, a1, o4))

    assert "The booking limit has been reached" in str(e)

    transaction.abort()

    # the custom limit overrides the period limit
    a1 = attendees.query().filter(Attendee.name == "Dustin Henderson").one()
    a1.limit = 1

    period = periods.active()
    period.max_bookings_per_attendee = 2

    bookings.accept_booking(bookings.add(owner, a1, o1))

    with pytest.raises(RuntimeError) as e:
        bookings.accept_booking(bookings.add(owner, a1, o3))

    assert "The booking limit has been reached" in str(e)

    transaction.abort()

    # if accepting the booking leads to the booking limit, the rest is blocked
    period = periods.active()
    period.all_inclusive = True
    period.max_bookings_per_attendee = 1

    assert o1.dates[0].end < o3.dates[0].start
    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o3)

    bookings.accept_booking(b1)

    assert b1.state == 'accepted'
    assert b2.state == 'blocked'


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
        start=datetime(2016, 10, 4, 9),
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
        end=datetime(2016, 10, 4, 16),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2)
    )

    o4 = occasions.add(
        start=datetime(2016, 10, 4, 15),
        end=datetime(2016, 10, 4, 18),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 1)
    )

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2000, 1, 1),
        gender='male'
    )

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2000, 1, 1),
        gender='male'
    )

    a3 = attendees.add(
        user=owner,
        name="Eleven",
        birth_date=date(2000, 1, 1),
        gender='female'
    )

    transaction.commit()

    # only works for confirmed periods
    with pytest.raises(RuntimeError) as e:
        bookings.cancel_booking(bookings.add(owner, a1, o1))

    assert "The period has not yet been confirmed" in str(e)
    transaction.abort()

    periods.active().confirmed = True
    transaction.commit()

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

    transaction.abort()

    # make sure the booking limit is honored
    period = periods.active()
    period.all_inclusive = True
    period.max_bookings_per_attendee = 1

    b1 = bookings.add(owner, a1, o1, priority=4)
    b2 = bookings.add(owner, a1, o2, priority=3)
    b3 = bookings.add(owner, a1, o3, priority=2)
    b4 = bookings.add(owner, a1, o4, priority=1)

    bookings.accept_booking(b1)

    assert b1.state == 'accepted'
    assert b2.state == 'blocked'
    assert b3.state == 'blocked'
    assert b4.state == 'blocked'

    bookings.cancel_booking(b1)

    assert b1.state == 'cancelled'
    assert b2.state == 'accepted'
    assert b3.state == 'blocked'
    assert b4.state == 'blocked'

    bookings.cancel_booking(b2)

    assert b1.state == 'cancelled'
    assert b2.state == 'cancelled'
    assert b3.state == 'accepted'
    assert b4.state == 'blocked'

    transaction.abort()

    # make sure accepting a previously denied booking of the same occasion will
    # will be skipped if doing so would conflict with the limit
    period = periods.active()
    period.all_inclusive = True
    period.max_bookings_per_attendee = 1

    b1 = bookings.add(owner, a1, o4)
    b2 = bookings.add(owner, a2, o1)
    b3 = bookings.add(owner, a2, o4)

    b1.state = 'accepted'
    b2.state = 'accepted'
    b3.state = 'denied'

    session.flush()

    bookings.cancel_booking(b1)

    assert b1.state == 'cancelled'
    assert b2.state == 'accepted'
    assert b3.state == 'denied'


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

    with freeze_time('2016-08-31'):
        assert period.phase == 'inactive'

    with freeze_time('2016-09-01'):
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


def test_invoice_items(session, owner):
    items = InvoiceItemCollection(session)
    items.add(owner, "Ferienpass 2016", "Malcolm", "Camp", 100.0, 1.0)
    items.add(owner, "Ferienpass 2016", "Malcolm", "Pass", 25.0, 1.0)
    items.add(owner, "Ferienpass 2016", "Dewey", "Football", 100.0, 1.0)
    items.add(owner, "Ferienpass 2016", "Dewey", "Pass", 25.0, 1.0)
    items.add(owner, "Ferienpass 2016", "Discount", "8%", 250, -0.05)

    assert items.total == 237.5

    items.add(owner, "Ferienpass 2017", "Malcolm", "Camp", 100, 1 / 3)

    assert items.for_invoice("Ferienpass 2017").total == 33
    assert items.for_invoice("asdf").total is None
    assert items.total == 270.5

    items.query().first().paid = True
    assert items.outstanding == 270.5 - 100.0


def test_confirm_period(session, owner):

    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True)
    period.all_inclusive = False
    period.booking_cost = 10

    sport = activities.add("Sport", username=owner.username)

    o = occasions.add(
        start=datetime(2016, 10, 4, 10),
        end=datetime(2016, 10, 4, 12),
        timezone="Europe/Zurich",
        activity=sport,
        period=period,
        spots=(0, 2))
    o.cost = 20

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2000, 1, 1),
        gender='male')

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2000, 1, 1),
        gender='male')

    transaction.commit()

    b1 = bookings.add(owner, a1, o)
    b2 = bookings.add(owner, a2, o)
    b1.state = 'open'
    b2.state = 'accepted'

    period = periods.query().one()
    period.confirm()

    assert bookings.query().all()[0].cost == 30.0
    assert bookings.query().all()[1].cost == 30.0
    assert sorted([b.state for b in bookings.query()]) == [
        'accepted',
        'denied',
    ]

    transaction.abort()

    period = periods.query().one()
    period.all_inclusive = True
    period.booking_cost = 10

    b1 = bookings.add(owner, a1, o)

    period.confirm()

    assert bookings.query().one().cost == 20.0


def test_cancel_occasion(session, owner):

    activities = ActivityCollection(session)
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
    bookings = BookingCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True)

    o1 = occasions.add(
        start=datetime(2016, 10, 4, 10),
        end=datetime(2016, 10, 4, 12),
        timezone="Europe/Zurich",
        activity=activities.add("Sport", username=owner.username),
        period=period,
        spots=(0, 2))

    o2 = occasions.add(
        start=datetime(2016, 10, 4, 10),
        end=datetime(2016, 10, 4, 12),
        timezone="Europe/Zurich",
        activity=activities.add("Science", username=owner.username),
        period=period,
        spots=(0, 2))

    a1 = attendees.add(
        user=owner,
        name="Dustin Henderson",
        birth_date=date(2008, 1, 1),
        gender='male')

    a2 = attendees.add(
        user=owner,
        name="Mike Wheeler",
        birth_date=date(2008, 1, 1),
        gender='male')

    transaction.commit()

    o1, o2 = occasions.query().all()

    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a2, o1)

    o1.cancel()
    assert b1.state == 'cancelled'
    assert b2.state == 'cancelled'
    assert o1.cancelled
    assert not o2.cancelled

    transaction.abort()

    periods.active().confirmed = True
    o1, o2 = occasions.query().all()

    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o2)

    b1.state = 'accepted'
    b2.state = 'blocked'

    o1.cancel()

    assert b1.state == 'cancelled'
    assert b2.state == 'accepted'
    assert o1.cancelled
    assert not o2.cancelled


def test_no_overlapping_dates(session, collections, prebooking_period, owner):
    period = prebooking_period

    o = collections.occasions.add(
        start=period.execution_start,
        end=period.execution_start + timedelta(hours=2),
        timezone="Europe/Zurich",
        activity=collections.activities.add("Sport", username=owner.username),
        period=period
    )

    with pytest.raises(AssertionError):
        collections.occasions.add_date(
            occasion=o,
            start=period.execution_start + timedelta(hours=1),
            end=period.execution_start + timedelta(hours=3),
            timezone="Europe/Zurich"
        )


def test_no_occasion_orphans(session, collections, prebooking_period, owner):
    period = prebooking_period

    collections.occasions.add(
        start=period.execution_start,
        end=period.execution_start + timedelta(hours=2),
        timezone="Europe/Zurich",
        activity=collections.activities.add("Sport", username=owner.username),
        period=period
    )

    transaction.commit()

    assert collections.occasions.query().count() == 1
    assert session.query(OccasionDate).count() == 1

    collections.occasions.delete(collections.occasions.query().first())
    transaction.commit()

    assert collections.occasions.query().count() == 0
    assert session.query(OccasionDate).count() == 0


def test_date_changes(session, collections, prebooking_period, owner):
    period = prebooking_period

    collections.occasions.add(
        start=period.execution_start,
        end=period.execution_start + timedelta(hours=2),
        timezone="Europe/Zurich",
        activity=collections.activities.add("Sport", username=owner.username),
        period=period
    )

    transaction.commit()

    o = collections.occasions.query().first()
    assert DAYS.has(o.duration, DAYS.half)
    assert not DAYS.has(o.duration, DAYS.full)
    assert not DAYS.has(o.duration, DAYS.many)

    o.dates[0].end += timedelta(hours=6)
    assert DAYS.has(o.duration, DAYS.half)
    assert not DAYS.has(o.duration, DAYS.full)
    assert not DAYS.has(o.duration, DAYS.many)

    session.flush()

    assert not DAYS.has(o.duration, DAYS.half)
    assert DAYS.has(o.duration, DAYS.full)
    assert not DAYS.has(o.duration, DAYS.many)


def test_is_permitted_birth_date():
    o = Occasion(age=NumericRange(6, 9), dates=[
        OccasionDate(
            start=datetime(2017, 7, 26, 10),
            end=datetime(2017, 7, 26, 16),
            timezone='Europe/Zurich'
        ),
        OccasionDate(
            start=datetime(2017, 7, 26, 17),
            end=datetime(2017, 7, 26, 20),
            timezone='Europe/Zurich'
        )
    ])

    assert o.is_permitted_birth_date(date(2012, 7, 26), wiggle_room=366)
    assert not o.is_permitted_birth_date(date(2012, 7, 26), wiggle_room=365)

    assert not o.is_too_young(date(2012, 7, 26), wiggle_room=366)
    assert o.is_too_young(date(2012, 7, 26), wiggle_room=365)

    assert o.is_permitted_birth_date(date(2008, 7, 26), wiggle_room=365)
    assert not o.is_permitted_birth_date(date(2008, 7, 26), wiggle_room=364)

    assert not o.is_too_old(date(2008, 7, 26), wiggle_room=365)
    assert o.is_too_old(date(2008, 7, 26), wiggle_room=364)


def test_deadline(session, collections, prebooking_period, owner):
    period = prebooking_period

    start, end = period.execution_start,\
        period.execution_start + timedelta(hours=2)

    occasion = collections.occasions.add(
        start=start,
        end=end,
        timezone="Europe/Zurich",
        activity=collections.activities.add("Sport", username=owner.username),
        period=period
    )
    assert occasion.deadline == period.execution_start.date()

    period.deadline_days = 1
    assert occasion.deadline == (start - timedelta(days=2)).date()

    period.deadline_date = date(2017, 2, 23)
    assert occasion.deadline == date(2017, 2, 23)


def test_prebooking_phases():
    period = Period()

    period.prebooking_start = date(2017, 5, 1)
    period.prebooking_end = date(2017, 5, 2)

    with freeze_time('2017-04-30 23:59:59'):
        assert period.is_prebooking_in_future

    with freeze_time('2017-05-01 00:00:00'):
        assert not period.is_prebooking_in_future

        period.active = False
        assert not period.is_currently_prebooking

        period.active = True
        assert period.is_currently_prebooking

    with freeze_time('2017-05-05 00:00:00'):
        assert not period.is_prebooking_in_future
        assert not period.is_currently_prebooking
        assert period.is_prebooking_in_past

    with freeze_time('2017-05-02 23:59:59'):
        assert period.is_currently_prebooking

        period.confirmed = True
        assert not period.is_currently_prebooking
        assert period.is_prebooking_in_past


def test_publication_request(session, owner):

    activities = ActivityCollection(session)
    requests = PublicationRequestCollection(session)
    periods = PeriodCollection(session)

    period = periods.add(
        title="Autumn 2016",
        prebooking=(datetime(2016, 9, 1), datetime(2016, 9, 30)),
        execution=(datetime(2016, 10, 1), datetime(2016, 10, 31)),
        active=True
    )

    activity = activities.add(
        title="Sport",
        username=owner.username,
    )

    request = requests.add(activity=activity, period=period)
    session.flush()

    request = requests.query().first()
    assert request.activity.title == "Sport"
    assert request.period.title == "Autumn 2016"


def test_archive_period(session, owner):

    activities = ActivityCollection(session)
    occasions = OccasionCollection(session)
    periods = PeriodCollection(session)

    current_period = periods.add(
        title="Autumn 2017",
        prebooking=(datetime(2017, 9, 1), datetime(2017, 9, 30)),
        execution=(datetime(2017, 10, 1), datetime(2017, 10, 31)),
        active=True
    )

    future_period = periods.add(
        title="Winter 2017",
        prebooking=(datetime(2017, 11, 1), datetime(2017, 11, 30)),
        execution=(datetime(2017, 12, 1), datetime(2017, 12, 31)),
        active=False
    )

    sport = activities.add("Sport", username=owner.username)
    games = activities.add("Games", username=owner.username)
    empty = activities.add("Empty", username=owner.username)

    sport.propose().accept()
    games.propose().accept()
    empty.propose().accept()

    occasions.add(
        start=datetime(2017, 10, 4, 13),
        end=datetime(2017, 10, 4, 14),
        timezone="Europe/Zurich",
        meeting_point="Lucerne",
        age=(6, 9),
        spots=(2, 10),
        note="Bring game-face",
        activity=sport,
        period=current_period
    )
    occasions.add(
        start=datetime(2017, 12, 4, 13),
        end=datetime(2017, 12, 4, 14),
        timezone="Europe/Zurich",
        meeting_point="Lucerne",
        age=(6, 9),
        spots=(2, 10),
        note="Bring game-face",
        activity=sport,
        period=future_period
    )
    occasions.add(
        start=datetime(2017, 12, 4, 13),
        end=datetime(2017, 12, 4, 14),
        timezone="Europe/Zurich",
        meeting_point="Lucerne",
        age=(6, 9),
        spots=(2, 10),
        note="Bring game-face",
        activity=games,
        period=current_period
    )

    current_period.confirmed = True
    current_period.finalized = True

    current_period.archive()

    assert current_period.archived == True
    assert sport.state == 'accepted'
    assert games.state == 'archived'
    assert empty.state == 'archived'


def test_activity_filter_toggle():
    f = ActivityFilter(tags=['Foo'])

    assert not f.toggled(tag='Foo').tags
    assert f.toggled(tag='Bar').tags == {'Foo', 'Bar'}


def test_activity_period_filter(scenario):
    # an activity fully booked in the previous period...
    scenario.add_period(title="Prev", active=False, confirmed=True)
    scenario.add_activity(title="Running", state='accepted')
    scenario.add_occasion(spots=(0, 1))

    scenario.commit()
    scenario.refresh()

    scenario.add_attendee()
    scenario.add_booking(state='accepted')

    # ...and unbooked in the current period
    scenario.add_period(title="Next", active=True, confirmed=True)
    scenario.add_occasion(spots=(0, 1))

    scenario.commit()
    scenario.refresh()

    assert scenario.occasions[0].attendee_count == 1
    assert scenario.occasions[1].attendee_count == 0

    # free spots should now depend on the selected period
    a = scenario.c.activities
    a.query().count() == 2

    assert a.for_filter(period_id=scenario.periods[0].id).query().count() == 1
    assert a.for_filter(period_id=scenario.periods[1].id).query().count() == 1

    assert a.for_filter(available='none').query().count() == 1
    assert a.for_filter(available='few').query().count() == 1

    assert a.for_filter(
        period_id=scenario.periods[0].id,
        available='many'
    ).query().count() == 0

    assert a.for_filter(
        period_id=scenario.periods[1].id,
        available='none'
    ).query().count() == 0


def test_activity_cost_filter(scenario):
    scenario.add_period()

    scenario.add_activity()
    scenario.add_occasion(cost=0)

    scenario.add_activity()
    scenario.add_occasion(cost=50)

    scenario.add_activity()
    scenario.add_occasion(cost=100)

    a = scenario.c.activities

    assert a.for_filter(price_range=(0, 0)).query().count() == 1
    assert a.for_filter(price_range=(0, 50)).query().count() == 2
    assert a.for_filter(price_range=(50, 100)).query().count() == 2
    assert a.for_filter(price_range=(0, 100)).query().count() == 3
    assert a.for_filter(price_range=(100, 1000)).query().count() == 1
    assert a.for_filter(price_range=(101, 1000)).query().count() == 0

    scenario.latest_period.all_inclusive = False
    scenario.latest_period.booking_cost = 1

    assert a.for_filter(price_range=(0, 0)).query().count() == 0
    assert a.for_filter(price_range=(1, 1)).query().count() == 1
    assert a.for_filter(price_range=(1, 51)).query().count() == 2
    assert a.for_filter(price_range=(51, 101)).query().count() == 2
    assert a.for_filter(price_range=(1, 101)).query().count() == 3
    assert a.for_filter(price_range=(101, 1000)).query().count() == 1
    assert a.for_filter(price_range=(102, 1000)).query().count() == 0

    scenario.latest_period.all_inclusive = True

    assert a.for_filter(price_range=(0, 0)).query().count() == 1
    assert a.for_filter(price_range=(0, 50)).query().count() == 2
    assert a.for_filter(price_range=(50, 100)).query().count() == 2
    assert a.for_filter(price_range=(0, 100)).query().count() == 3
    assert a.for_filter(price_range=(100, 1000)).query().count() == 1
    assert a.for_filter(price_range=(101, 1000)).query().count() == 0


def test_timeline_filter(scenario):
    with freeze_time('2018-02-01'):
        scenario.add_period(active=False)
        scenario.add_activity(title="Winter")
        scenario.add_occasion()

    with freeze_time('2018-05-01'):
        scenario.add_period(active=False)
        scenario.add_activity(title="Spring")
        scenario.add_occasion()

    with freeze_time('2018-07-01'):
        scenario.add_period(active=False)
        scenario.add_activity(title="Summer")
        scenario.add_occasion()

    with freeze_time('2018-09-01'):
        scenario.add_period(active=False)
        scenario.add_activity(title="Autumn")

    a = scenario.c.activities

    with freeze_time('2018-01-01 23:30'):
        assert a.for_filter(timeline='past').query().count() == 0
        assert a.for_filter(timeline='now').query().count() == 0
        assert a.for_filter(timeline='future').query().count() == 3
        assert a.for_filter(timeline='undated').query().count() == 1

    with freeze_time('2018-02-10 23:30'):
        assert a.for_filter(timeline='past').query().count() == 0
        assert a.for_filter(timeline='now').query().count() == 1
        assert a.for_filter(timeline='future').query().count() == 2
        assert a.for_filter(timeline='undated').query().count() == 1

    with freeze_time('2018-04-01 23:30'):
        assert a.for_filter(timeline='past').query().count() == 1
        assert a.for_filter(timeline='future').query().count() == 2
        assert a.for_filter(timeline='undated').query().count() == 1

    with freeze_time('2018-05-10 22:30'):
        assert a.for_filter(timeline='past').query().count() == 1
        assert a.for_filter(timeline='now').query().count() == 1
        assert a.for_filter(timeline='future').query().count() == 1
        assert a.for_filter(timeline='undated').query().count() == 1

    with freeze_time('2018-06-01 22:30'):
        assert a.for_filter(timeline='past').query().count() == 2
        assert a.for_filter(timeline='future').query().count() == 1
        assert a.for_filter(timeline='undated').query().count() == 1

    with freeze_time('2018-07-10 22:30'):
        assert a.for_filter(timeline='past').query().count() == 2
        assert a.for_filter(timeline='now').query().count() == 1
        assert a.for_filter(timeline='future').query().count() == 0
        assert a.for_filter(timeline='undated').query().count() == 1

    with freeze_time('2018-08-01 22:30'):
        assert a.for_filter(timeline='past').query().count() == 3
        assert a.for_filter(timeline='future').query().count() == 0
        assert a.for_filter(timeline='undated').query().count() == 1
