import pytest
import transaction

from datetime import datetime
from onegov.reservation.models import Resource
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
