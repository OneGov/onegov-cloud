from datetime import datetime, timedelta
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.activity.tests.fixtures.scenario import Scenario
from onegov.core.utils import Bunch, module_path
from onegov.user import User
from onegov.user import UserCollection
from pytest import fixture


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
        datetime.utcnow() - timedelta(days=10),
        datetime.utcnow() + timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s, e),
        execution=(e + timedelta(days=10), e + timedelta(days=20)),
        active=True
    )


@fixture(scope='function')
def execution_period(collections):
    """ Returns a period which is currently in the execution phase. """

    s, e = (
        datetime.utcnow() - timedelta(days=10),
        datetime.utcnow() + timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s - timedelta(days=20), s - timedelta(days=10)),
        execution=(s, e),
        active=True
    )


@fixture(scope='function')
def inactive_period(collections):
    """ Returns a previously used period """

    s, e = (
        datetime.utcnow() - timedelta(days=100),
        datetime.utcnow() - timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s - timedelta(days=20), s - timedelta(days=10)),
        execution=(s, e),
        active=False
    )


@fixture(scope='session')
def postfinance_xml():
    xml = 'camt.053_P_CH0309000000250090342_380000000_0_2016053100163801.xml'
    xml_path = module_path('onegov.activity', '/tests/fixtures/' + xml)

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
