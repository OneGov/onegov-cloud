import pytest
import sqlalchemy
import transaction

from datetime import datetime
from onegov.activity import ActivityCollection
from onegov.activity import OccasionCollection
from onegov.activity.models import Booking
from pytz import utc


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
