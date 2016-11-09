from datetime import datetime, timedelta
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.core.utils import Bunch
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
