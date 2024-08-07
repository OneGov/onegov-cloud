from datetime import timedelta
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.core.utils import Bunch, module_path
from onegov.user import User
from onegov.user import UserCollection
from pytest import fixture
from sedate import utcnow
from tests.onegov.activity.fixtures.scenario import Scenario


@fixture(scope='function')
def owner(session):
    return UserCollection(session).add(
        username='owner@example.org',
        password='hunter2',
        role='editor'
    )


@fixture(scope='function')
def secondary_owner(session):
    return UserCollection(session).add(
        username='secondary@example.org',
        password='hunter2',
        role='editor'
    )


@fixture(scope='function')
def member(session):
    return UserCollection(session).add(
        username='member@example.org',
        password='hunter2',
        role='member'
    )


@fixture(scope='function')
def collections(session):
    return Bunch(
        activities=ActivityCollection(session),
        attendees=AttendeeCollection(session),
        bookings=BookingCollection(session),
        occasions=OccasionCollection(session),
        periods=PeriodCollection(session),
    )


@fixture(scope='function')
def prebooking_period(collections):
    """ Returns a period which is currently in the prebooking phase. """

    s, e = (
        utcnow() - timedelta(days=10),
        utcnow() + timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s, e),
        booking=(e + timedelta(days=1), e + timedelta(days=9)),
        execution=(e + timedelta(days=10), e + timedelta(days=20)),
        active=True
    )


@fixture(scope='function')
def execution_period(collections):
    """ Returns a period which is currently in the execution phase. """

    s, e = (
        utcnow() - timedelta(days=10),
        utcnow() + timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s - timedelta(days=20), s - timedelta(days=10)),
        booking=(s - timedelta(days=9), s - timedelta(days=1)),
        execution=(s, e),
        active=True
    )


@fixture(scope='function')
def inactive_period(collections):
    """ Returns a previously used period """

    s, e = (
        utcnow() - timedelta(days=100),
        utcnow() - timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s - timedelta(days=20), s - timedelta(days=10)),
        booking=(s - timedelta(days=9), s - timedelta(days=1)),
        execution=(s, e),
        active=False
    )


@fixture(scope='session')
def postfinance_xml():
    xml = 'camt.053_P_CH0309000000250090342_380000000_0_2016053100163801.xml'
    xml_path = module_path('tests.onegov.activity', '/fixtures/' + xml)

    with open(xml_path, 'r') as f:
        yield f.read()


@fixture(scope='session')
def postfinance_qr_xml():
    xml = 'CAMT053_280324-1.xml'
    xml_path = module_path('tests.onegov.activity', '/fixtures/' + xml)

    with open(xml_path, 'r') as f:
        yield f.read()


@fixture(scope='function')
def scenario(request, session, test_password):

    session.add(User(
        username='admin@example.org',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=test_password,
        role='editor'
    ))

    yield Scenario(session, test_password)
