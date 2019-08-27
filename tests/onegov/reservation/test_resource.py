import pytest
import transaction

from datetime import datetime
from freezegun import freeze_time
from onegov.reservation.models import Resource
from pytz import utc
from uuid import uuid4


def test_libres_context_fixture(session_manager, libres_context):
    assert session_manager is libres_context.get_service('session_provider')


def test_resource_scheduler(libres_context):
    resource = Resource(id=uuid4())

    with pytest.raises(AssertionError):
        resource.get_scheduler(libres_context)

    resource.timezone = 'Europe/Zurich'

    scheduler = resource.get_scheduler(libres_context)
    scheduler.managed_allocations().count() == 0

    assert scheduler.resource == resource.id


def test_scheduler_boundaries(libres_context):
    resource = Resource(id=uuid4())
    resource.timezone = 'Europe/Amsterdam'

    scheduler = resource.get_scheduler(libres_context)
    scheduler.allocate((
        datetime(2015, 6, 11, 8),
        datetime(2015, 6, 11, 18)
    ))

    assert scheduler.managed_allocations().count() == 1

    new_resource = Resource()
    new_resource.id = resource.id
    new_resource.timezone = 'Europe/Amsterdam'

    scheduler = new_resource.get_scheduler(libres_context)

    assert scheduler.managed_allocations().count() == 1

    new_resource = Resource(id=uuid4())
    new_resource.timezone = 'Europe/Amsterdam'
    new_resource.libres_context = libres_context

    scheduler = new_resource.get_scheduler(libres_context)

    assert scheduler.managed_allocations().count() == 0


def test_delete_cascade(session_manager, libres_context):
    resource = Resource(id=uuid4())
    resource.timezone = 'Europe/Zurich'
    resource.name = 'test'
    resource.title = 'Test'

    session = session_manager.session()
    session.add(resource)

    scheduler = resource.get_scheduler(libres_context)
    scheduler.allocate((
        datetime(2015, 6, 11, 8),
        datetime(2015, 6, 11, 18)
    ))

    transaction.commit()
    session.expire_all()

    resource = session.query(Resource).one()
    scheduler = resource.get_scheduler(libres_context)
    assert scheduler.managed_allocations().count() == 1

    session.delete(resource)

    assert scheduler.managed_allocations().count() == 0


def test_invalid_deadlines():
    resource = Resource()

    with pytest.raises(ValueError):
        resource.deadline = 'Foobar'

    with pytest.raises(ValueError):
        resource.deadline = '3h'

    with pytest.raises(ValueError):
        resource.deadline = ('3', 'd')

    with pytest.raises(ValueError):
        resource.deadline = (0, 'd')

    with pytest.raises(ValueError):
        resource.deadline = (3, 'm')

    resource.deadline = ''
    assert resource.deadline is None

    resource.deadline = None
    resource.deadline = (5, 'd')
    resource.deadline = (24, 'h')


def test_deadline():
    resource = Resource(timezone='UTC')

    # by default, no deadline is active
    with freeze_time("2018-11-28"):
        assert not resource.is_past_deadline(
            datetime(2018, 11, 27, tzinfo=utc))
        assert not resource.is_past_deadline(
            datetime(2018, 11, 28, tzinfo=utc))
        assert not resource.is_past_deadline(
            datetime(2018, 11, 29, tzinfo=utc))

    allocation = datetime(2018, 11, 28, 13, tzinfo=utc)

    resource.deadline = (1, 'h')

    # if it's 11:59, we can reserve for 13:00
    with freeze_time("2018-11-28 11:59"):
        assert not resource.is_past_deadline(allocation)

    # if it's 12:00, we can no longer reserve for 13:00
    with freeze_time("2018-11-28 12:00"):
        assert resource.is_past_deadline(allocation)

    # if it's 13:00, we can no longer reserve for 13:00
    with freeze_time("2018-11-28 13:00"):
        assert resource.is_past_deadline(allocation)

    resource.deadline = (1, 'd')

    # the day before at 23:59, we can still reserve
    with freeze_time("2018-11-27 23:59"):
        assert not resource.is_past_deadline(allocation)

    # the same day at 00:00 we can no longer reserve
    with freeze_time("2018-11-28 00:00"):
        assert resource.is_past_deadline(allocation)

    # any time thereafter is the same
    with freeze_time("2018-11-28 13:00"):
        assert resource.is_past_deadline(allocation)

    with freeze_time("2018-11-29 13:00"):
        assert resource.is_past_deadline(allocation)
